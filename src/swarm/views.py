"""
REST Mode Views for Open Swarm MCP.

This module defines asynchronous views to handle chat completions and model listings,
aligning with OpenAI's Chat Completions API.

Endpoints:
    - POST /v1/chat/completions: Handles chat completion requests.
    - GET /v1/models: Lists available blueprints as models.
    - GET /django_chat/: Lists conversations for the logged-in user.
    - POST /django_chat/start/: Starts a new conversation.
"""

import json
import uuid
import time
import os
import redis
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

# Django & DRF imports
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response  # type: ignore
from rest_framework.decorators import api_view, authentication_classes, permission_classes  # type: ignore
from rest_framework.permissions import IsAuthenticated  # type: ignore
from rest_framework.authentication import TokenAuthentication  # type: ignore

# Project-specific imports
from swarm.auth import EnvOrTokenAuthentication
from swarm.models import ChatConversation, ChatMessage
from swarm.extensions.blueprint import discover_blueprints
from swarm.extensions.blueprint.blueprint_base import BlueprintBase
from swarm.extensions.config.config_loader import load_server_config, load_llm_config
from swarm.utils.logger_setup import setup_logger
from swarm.utils.redact import redact_sensitive_data
from swarm.utils.general_utils import extract_chat_id
from swarm.extensions.blueprint.blueprint_utils import filter_blueprints  # Import our new utility
from .settings import DJANGO_DATABASE

# -----------------------------------------------------------------------------
# Initialization
# -----------------------------------------------------------------------------

# Initialize logger for this module.
logger = setup_logger(__name__)

# Initialize Redis if available (modified for testing stateful mode).
REDIS_AVAILABLE = bool(os.getenv("STATEFUL_CHAT_ID_PATH"))
redis_client = None
if REDIS_AVAILABLE:
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        redis_client.ping()
        logger.info("✅ Redis connection successful.")
    except Exception as e:
        logger.warning(f"⚠️ Redis unavailable, falling back to PostgreSQL: {e}")
        REDIS_AVAILABLE = False

# Load configuration from file.
CONFIG_PATH = Path(settings.BASE_DIR) / "swarm_config.json"
try:
    config = load_server_config(str(CONFIG_PATH))
    redacted_config = redact_sensitive_data(config)  # Redact before logging.
    logger.debug(f"Loaded configuration from {CONFIG_PATH}: {redacted_config}")
except Exception as e:
    logger.critical(f"Failed to load configuration from {CONFIG_PATH}: {e}")
    raise e

# -----------------------------------------------------------------------------
# Blueprint Discovery and Filtering
# -----------------------------------------------------------------------------

BLUEPRINTS_DIR = (Path(settings.BASE_DIR) / "blueprints").resolve()
try:
    all_blueprints = discover_blueprints([str(BLUEPRINTS_DIR)])
    # Apply filtering if the SWARM_BLUEPRINTS environment variable is set.
    if allowed_blueprints := os.getenv("SWARM_BLUEPRINTS"):
        blueprints_metadata = filter_blueprints(all_blueprints, allowed_blueprints)
        logger.info(f"Filtered blueprints using SWARM_BLUEPRINTS: {allowed_blueprints.split(',')}")
    else:
        blueprints_metadata = all_blueprints

    redacted_blueprints_metadata = redact_sensitive_data(blueprints_metadata)
    logger.debug(f"Discovered blueprints metadata: {redacted_blueprints_metadata}")
except Exception as e:
    logger.error(f"Error discovering blueprints: {e}", exc_info=True)
    raise e

# Inject LLM metadata into blueprints.
try:
    llm_config = load_llm_config(config)
    llm_model = llm_config.get("model", "default")
    llm_provider = llm_config.get("provider", "openai")
    for blueprint in blueprints_metadata.values():
        blueprint["openai_model"] = llm_model
        blueprint["llm_provider"] = llm_provider
except ValueError as e:
    logger.critical(f"Failed to load LLM configuration: {e}")
    raise e

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def serialize_swarm_response(response: Any, model_name: str, context_variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serializes the Swarm response while removing non-serializable objects like functions.

    Args:
        response (Any): The response object from the LLM or blueprint.
        model_name (str): The name of the model used.
        context_variables (Dict[str, Any]): Additional context variables maintained across interactions.

    Returns:
        Dict[str, Any]: A structured JSON response that includes the full conversation history,
                        tool calls, and additional context.
    """
    if hasattr(response, "model_dump"):
        response = response.model_dump()

    messages = response.get("messages", [])

    def remove_functions(obj: Any) -> Any:
        """Recursively remove callable objects from data structures."""
        if isinstance(obj, dict):
            return {k: remove_functions(v) for k, v in obj.items() if not callable(v)}
        elif isinstance(obj, list):
            return [remove_functions(item) for item in obj if not callable(item)]
        elif isinstance(obj, tuple):
            return tuple(remove_functions(item) for item in obj if not callable(item))
        return obj

    if "agent" in response:
        response["agent"] = remove_functions(response["agent"])

    clean_context = remove_functions(context_variables)
    clean_response = remove_functions(response)

    formatted_messages = [
        {"index": i, "message": msg, "finish_reason": "stop"}
        for i, msg in enumerate(messages)
    ]

    return {
        "id": f"swarm-chat-completion-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": formatted_messages,
        "usage": {
            "prompt_tokens": sum(len((msg.get("content") or "").split()) for msg in messages),
            "completion_tokens": sum(len((msg.get("content") or "").split()) for msg in messages if msg.get("role") == "assistant"),
            "total_tokens": len(messages),
        },
        "context_variables": clean_context,
        "full_response": clean_response,
    }

def parse_chat_request(request: Any) -> Any:
    """
    Extract and validate JSON from the incoming request. Returns a tuple of values or an error Response.

    Ensures a conversation_id is present and sets a default role for messages if missing.

    Returns:
        Tuple containing (body, model, messages, context_variables, conversation_id, tool_call_id)
        or a DRF Response with an error message.
    """
    try:
        body = json.loads(request.body)
        model = body.get("model", "default")
        messages = body.get("messages", [])
        if not messages and "message" in body:
            messages = [body["message"]]
        messages = [msg if isinstance(msg, dict) else {"content": msg} for msg in messages]
        context_variables = body.get("context_variables", {})

        # Extract conversation_id and tool_call_id.
        conversation_id = extract_chat_id(body)
        tool_call_id = None
        if messages:
            last_message = messages[-1]
            tool_calls = last_message.get("tool_calls", [])
            if tool_calls:
                tool_call_id = tool_calls[-1].get("id")

        # If in stateful mode and no conversation_id is provided, generate one.
        if not conversation_id and 'STATEFUL_CHAT_ID_PATH' in os.environ:
            conversation_id = str(uuid.uuid4())
            logger.warning(f"⚠️ No conversation_id detected, generating new ID: {conversation_id}")

        for idx, msg in enumerate(messages):
            if "role" not in msg:
                messages[idx]["role"] = "user"

        if not messages:
            return Response({"error": "Messages are required."}, status=400)

        return (body, model, messages, context_variables, conversation_id, tool_call_id)
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON payload."}, status=400)

def get_blueprint_instance(model: str, context_vars: dict) -> Any:
    """
    Retrieve or instantiate the blueprint corresponding to the specified model.
    For the "default" model, returns a dummy blueprint if no matching blueprint is found.

    Args:
        model (str): Model name.
        context_vars (dict): Context variables from the request.

    Returns:
        The blueprint instance or a DRF Response with an error.
    """
    from .views import blueprints_metadata, config  # Adjust import as needed

    blueprint_meta = blueprints_metadata.get(model)
    if not blueprint_meta:
        if model == "default":
            class DummyBlueprint(BlueprintBase):
                metadata = {"title": "Dummy Blueprint", "env_vars": []}  # type: ignore

                def create_agents(self) -> dict:
                    DummyAgent = type("DummyAgent", (), {"name": "DummyAgent", "mcp_servers": {}, "functions": []})
                    self.starting_agent = DummyAgent
                    return {"DummyAgent": DummyAgent}

                def run_with_context(self, messages, context_variables) -> dict:
                    return {
                        "response": {"message": "Dummy response"},
                        "context_variables": context_variables
                    }
            return DummyBlueprint(config=config)
        else:
            return Response({"error": f"Model '{model}' not found."}, status=404)

    blueprint_class = blueprint_meta.get("blueprint_class")
    if not blueprint_class:
        return Response({"error": f"Blueprint class for model '{model}' is not defined."}, status=500)

    try:
        blueprint_instance = blueprint_class(config=config)
        active_agent = context_vars.get("active_agent_name", "Assistant")
        if active_agent not in blueprint_instance.swarm.agents:
            logger.debug("No active agent parsed from context_variables")
        else:
            logger.debug(f"Using active agent: {active_agent}")
            blueprint_instance.set_active_agent(active_agent)
        return blueprint_instance
    except Exception as e:
        logger.error(f"Error initializing blueprint: {e}", exc_info=True)
        return Response({"error": f"Error initializing blueprint: {str(e)}"}, status=500)

def load_conversation_history(conversation_id: Optional[str], messages: List[dict],
                              tool_call_id: Optional[str] = None) -> List[dict]:
    """
    Retrieve conversation history from Redis or the database.
    Optionally filters by tool_call_id for context-relevant messages.

    Args:
        conversation_id (Optional[str]): Unique conversation identifier.
        messages (List[dict]): New messages from the request.
        tool_call_id (Optional[str]): Optional tool call identifier.

    Returns:
        List[dict]: Combined list of historical and new messages.
    """
    if not conversation_id:
        logger.warning("⚠️ No conversation_id provided, returning only new messages.")
        return messages

    past_messages = []

    # Try Redis first if available.
    if REDIS_AVAILABLE and redis_client:
        try:
            history_raw = redis_client.get(conversation_id)
            if history_raw:
                data_str = history_raw.decode("utf-8") if isinstance(history_raw, bytes) else history_raw
                past_messages = json.loads(data_str)
                logger.debug(f"✅ Retrieved {len(past_messages)} messages from Redis for conversation: {conversation_id}")
        except Exception as e:
            logger.error(f"⚠️ Error retrieving conversation history from Redis: {e}", exc_info=True)

    # Fallback to database if Redis is unavailable or fails.
    if not past_messages:
        try:
            conversation = ChatConversation.objects.get(conversation_id=conversation_id)
            query = conversation.messages.all()
            if tool_call_id:
                query = query.filter(tool_call_id=tool_call_id)
            past_messages = list(query.order_by("timestamp").values("sender", "content", "timestamp", "tool_call_id"))
            logger.debug(f"✅ Retrieved {len(past_messages)} messages from DB for conversation: {conversation_id}, tool_call_id: {tool_call_id}")
        except ChatConversation.DoesNotExist:
            logger.warning(f"⚠️ No existing conversation found in DB for ID: {conversation_id}")
            past_messages = []

    formatted_past_messages = [
        {
            "role": msg["sender"],
            "content": msg["content"],
            "timestamp": msg["timestamp"],
            "tool_call_id": msg.get("tool_call_id")
        }
        for msg in past_messages
    ]

    return formatted_past_messages + messages

def store_conversation_history(conversation_id, full_history, response_obj=None):
    """
    Stores new conversation messages in the database (avoiding duplicates) and updates Redis.

    Args:
        conversation_id (str): Unique conversation identifier.
        full_history (list): List of message dictionaries.
        response_obj (Optional[Any]): Optional response data.

    Returns:
        bool: True if storage was successful, False otherwise.
    """
    try:
        chat, created = ChatConversation.objects.get_or_create(conversation_id=conversation_id)
        if created:
            logger.debug(f"🆕 Created new ChatConversation: {conversation_id}")
        else:
            logger.debug(f"🔄 Updating existing ChatConversation: {conversation_id}")

        stored_messages = set(chat.messages.values_list("content", flat=True))
        new_messages = []
        for msg in full_history:
            if not msg.get("content") and not msg.get("tool_calls"):
                logger.warning(f"⚠️ Skipping empty message in conversation {conversation_id}")
                continue
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            serialized_content = content if content.strip() else json.dumps(msg.get("tool_calls", {}))
            if serialized_content not in stored_messages:
                new_messages.append(ChatMessage(
                    conversation=chat,
                    sender=role,
                    content=serialized_content,
                    tool_call_id=msg.get("tool_call_id")
                ))
                stored_messages.add(serialized_content)

        if new_messages:
            ChatMessage.objects.bulk_create(new_messages)
            logger.debug(f"✅ Stored {len(new_messages)} new messages for conversation {conversation_id}")
        else:
            logger.warning(f"⚠️ No new messages to store for conversation {conversation_id}")

        if REDIS_AVAILABLE and redis_client:
            try:
                redis_client.set(conversation_id, json.dumps(full_history))
            except Exception as e:
                logger.error(f"Error updating Redis: {e}", exc_info=True)

        return True
    except Exception as e:
        logger.error(f"⚠️ Error storing conversation history: {e}", exc_info=True)
        return False

def run_conversation(blueprint_instance: Any,
                     messages_extended: List[dict],
                     context_vars: dict) -> Tuple[Any, dict]:
    """
    Executes the blueprint's conversation logic and returns the response and updated context.

    Args:
        blueprint_instance (Any): The blueprint instance to run.
        messages_extended (List[dict]): Combined historical and new messages.
        context_vars (dict): Conversation context variables.

    Returns:
        Tuple[Any, dict]: The response object and updated context variables.
    """
    result = blueprint_instance.run_with_context(messages_extended, context_vars)
    response_obj = result["response"]
    updated_context = result["context_variables"]
    return response_obj, updated_context

# -----------------------------------------------------------------------------
# Views
# -----------------------------------------------------------------------------

@api_view(['POST'])
@csrf_exempt
@authentication_classes([EnvOrTokenAuthentication])
@permission_classes([IsAuthenticated])
def chat_completions(request):
    """
    Main entry point for chat completion requests.
    
    Workflow:
      1. Parse the request JSON.
      2. Lookup and initialize the appropriate blueprint.
      3. Retrieve conversation history.
      4. Execute the conversation.
      5. Serialize the response.
      6. Store conversation history.
      7. Return the response.
    """
    if request.method != "POST":
        return Response({"error": "Method not allowed. Use POST."}, status=405)

    logger.info(f"Authenticated User: {request.user}")
    if request.user.is_anonymous:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            from django.contrib.auth.models import User
            request.user = User(username="testuser")

    parse_result = parse_chat_request(request)
    if isinstance(parse_result, Response):
        return parse_result

    body, model, messages, context_vars, conversation_id, tool_call_id = parse_result

    blueprint_instance_response = get_blueprint_instance(model, context_vars)
    if isinstance(blueprint_instance_response, Response):
        return blueprint_instance_response
    blueprint_instance = blueprint_instance_response

    messages_extended = load_conversation_history(conversation_id, messages, tool_call_id)
    try:
        response_obj, updated_context = run_conversation(blueprint_instance, messages_extended, context_vars)
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        return Response({"error": f"Error during execution: {str(e)}"}, status=500)

    serialized = serialize_swarm_response(response_obj, model, updated_context)
    if conversation_id:
        serialized["conversation_id"] = conversation_id
        store_conversation_history(conversation_id, messages_extended, response_obj)

    return Response(serialized, status=200)

@csrf_exempt
def list_models(request):
    """
    Lists discovered blueprint folders as models.
    
    Returns a JSON response with the metadata of each blueprint.
    """
    from pathlib import Path
    BLUEPRINTS_DIR = (Path(settings.BASE_DIR) / "blueprints").resolve()
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed. Use GET."}, status=405)
    
    try:
        all_blueprints = discover_blueprints([str(BLUEPRINTS_DIR)])
        allowed = os.getenv("SWARM_BLUEPRINTS")
        blueprints_metadata_local = filter_blueprints(all_blueprints, allowed) if allowed else all_blueprints
        data = [
            {
                "id": key,
                "object": "model",
                "title": meta.get("title", "No title"),
                "description": meta.get("description", "No description"),
            }
            for key, meta in blueprints_metadata_local.items()
        ]
        return JsonResponse({"object": "list", "data": data}, status=200)
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        return JsonResponse({"error": "Internal Server Error"}, status=500)

@csrf_exempt
def django_chat_webpage(request, blueprint_name):
    """
    Renders the chat webpage for Django.
    Passes the conversation ID and blueprint name to the template.
    """
    return render(request, 'django_chat_webpage.html', {
        'conversation_id': request.GET.get("conversation_id"),
        'blueprint_name': blueprint_name
    })

@csrf_exempt
def blueprint_webpage(request, blueprint_name):
    """
    Serves a webpage for a specific blueprint.
    
    If the blueprint is not found, returns an error page listing available blueprints.
    """
    logger.debug(f"Received request for blueprint webpage: '{blueprint_name}'")
    if blueprint_name not in blueprints_metadata:
        logger.warning(f"Blueprint '{blueprint_name}' not found.")
        available_blueprints = "".join(f"<li>{bp}</li>" for bp in blueprints_metadata)
        return HttpResponse(
            f"<h1>Blueprint '{blueprint_name}' not found.</h1><p>Available blueprints:</p><ul>{available_blueprints}</ul>",
            status=404,
        )
    logger.debug(f"Rendering blueprint webpage for: '{blueprint_name}'")
    context = {
        "blueprint_name": blueprint_name,
        "dark_mode": request.session.get('dark_mode', True)
    }
    return render(request, "simple_blueprint_page.html", context)

@csrf_exempt
def chatbot(request):
    """
    Renders the chatbot interface webpage.
    """
    logger.debug("Rendering chatbot web UI")
    context = {
        "dark_mode": request.session.get('dark_mode', True)
    }
    return render(request, "rest_mode/chatbot.html", context)

DEFAULT_CONFIG = {
    "llm": {
        "default": {
            "provider": "openai",
            "model": "llama3.2:latest",
            "base_url": "http://localhost:11434/v1",
            "api_key": "",
            "temperature": 0.3
        }
    }
}

def serve_swarm_config(request):
    """
    Serves the current Swarm configuration as JSON.
    
    If the configuration file is missing or contains invalid JSON, falls back to a default configuration.
    """
    config_path = Path(settings.BASE_DIR) / "swarm_config.json"
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        return JsonResponse(config_data)
    except FileNotFoundError:
        logger.error(f"swarm_config.json not found at {config_path}")
        return JsonResponse(DEFAULT_CONFIG)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {config_path}: {e}")
        return JsonResponse({"error": "Invalid JSON format in configuration file."}, status=500)
