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
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response  # type: ignore
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from swarm.auth import EnvOrTokenAuthentication
from swarm.models import ChatConversation, ChatMessage
from swarm.extensions.blueprint import discover_blueprints
from swarm.extensions.config.config_loader import (
    load_server_config,
    load_llm_config,
)
from swarm.utils.logger_setup import setup_logger
from swarm.utils.redact import redact_sensitive_data
from swarm.utils.general_utils import extract_chat_id
from .settings import DJANGO_DATABASE

# Initialize logger for this module
logger = setup_logger(__name__)

# Initialize Redis if available
REDIS_AVAILABLE = os.getenv("STATEFUL_CHAT_ID_PATH") and settings.DJANGO_DATABASE == "postgres"
redis_client = None
if REDIS_AVAILABLE:
    try:
        redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Redis connection successful.")
    except Exception as e:
        logger.warning(f"⚠️ Redis unavailable, falling back to PostgreSQL: {e}")
        REDIS_AVAILABLE = False

# Load configuration
CONFIG_PATH = Path(settings.BASE_DIR) / "swarm_config.json"
try:
    config = load_server_config(str(CONFIG_PATH))
    redacted_config = redact_sensitive_data(config)  # Redact before logging
    logger.debug(f"Loaded configuration from {CONFIG_PATH}: {redacted_config}")
except Exception as e:
    logger.critical(f"Failed to load configuration from {CONFIG_PATH}: {e}")
    raise e

# Discover blueprints
BLUEPRINTS_DIR = (Path(settings.BASE_DIR) / "blueprints").resolve()
try:
    blueprints_metadata = discover_blueprints([str(BLUEPRINTS_DIR)])
    redacted_blueprints_metadata = redact_sensitive_data(blueprints_metadata)
    logger.debug(f"Discovered blueprints meta {redacted_blueprints_metadata}")
except Exception as e:
    logger.error(f"Error discovering blueprints: {e}", exc_info=True)
    raise e

# Inject LLM metadata into blueprints
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
    # Convert to dictionary if response is a Pydantic object
    if hasattr(response, "model_dump"):
        response = response.model_dump()

    messages = response.get("messages", [])

    def remove_functions(obj):
        """Recursively remove function objects and other non-serializable types."""
        if isinstance(obj, dict):
            return {k: remove_functions(v) for k, v in obj.items() if not callable(v)}
        elif isinstance(obj, list):
            return [remove_functions(item) for item in obj if not callable(item)]
        elif isinstance(obj, tuple):
            return tuple(remove_functions(item) for item in obj if not callable(item))
        return obj

    if "agent" in response:
        response["agent"] = remove_functions(response["agent"])

    clean_context_variables = remove_functions(context_variables)
    clean_response = remove_functions(response)

    formatted_messages = [
        {
            "index": i,
            "message": msg,
            "finish_reason": "stop"
        }
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
        "context_variables": clean_context_variables,
        "full_response": clean_response,
    }


@api_view(['POST'])
@csrf_exempt
@authentication_classes([EnvOrTokenAuthentication])
@permission_classes([IsAuthenticated])
def chat_completions(request):
    """
    Main entry point: parse request -> lookup blueprint -> retrieve history -> run -> store -> return result.
    """
    if request.method != "POST":
        return Response({"error": "Method not allowed. Use POST."}, status=405)

    logger.info(f"Authenticated User: {request.user}")
    logger.info(f"Is Authenticated? {request.user.is_authenticated}")

    # 1) Parse incoming request
    parse_result = parse_chat_request(request)
    if isinstance(parse_result, Response):
        return parse_result

    body, model, messages, context_vars, conversation_id = parse_result

    # 2) Get or create an appropriate blueprint instance
    blueprint_instance_response = get_blueprint_instance(model, context_vars)
    if isinstance(blueprint_instance_response, Response):
        return blueprint_instance_response
    blueprint_instance = blueprint_instance_response

    # 3) Load conversation history from Redis or DB (using ChatMessage table)
    messages_extended = load_conversation_history(conversation_id, messages)

    # 4) Run the conversation via the blueprint
    try:
        response_obj, updated_context = run_conversation(blueprint_instance, messages_extended, context_vars)
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        return Response({"error": f"Error during execution: {str(e)}"}, status=500)

    if hasattr(response_obj, "model_dump"):
        response_obj = response_obj.model_dump()

    from .views import serialize_swarm_response  # Adjust import as needed
    serialized = serialize_swarm_response(response_obj, model, updated_context)

    # 6) Store updated conversation history using DB (or Redis if available)
    if conversation_id:
        serialized["conversation_id"] = conversation_id
        store_conversation_history(conversation_id, messages_extended, response_obj)

    # 7) Return final response
    return Response(serialized, status=200)


def parse_chat_request(request) -> Any:
    """
    Extract & validate JSON. Return tuple or an error Response.
    """
    try:
        body = json.loads(request.body)
        model = body.get("model", "default")

        messages = body.get("messages", [])
        if not messages and "message" in body:
            messages = [body["message"]]

        messages = [msg if isinstance(msg, dict) else {"content": msg} for msg in messages]
        context_variables = body.get("context_variables", {})

        from .views import extract_chat_id  # Adjust import as needed
        conversation_id = extract_chat_id(body)

        for idx, msg in enumerate(messages):
            if "role" not in msg:
                messages[idx]["role"] = "user"

        if not messages:
            return Response({"error": "Messages are required."}, status=400)

        return (body, model, messages, context_variables, conversation_id)

    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON payload."}, status=400)


def get_blueprint_instance(model: str, context_vars: dict) -> Any:
    """
    Retrieve or create a blueprint instance based on the model name.
    Return either a blueprint instance or an error Response.
    """
    from .views import blueprints_metadata, config  # Adjust import as needed

    blueprint_meta = blueprints_metadata.get(model)
    if not blueprint_meta:
        if model == "default":
            class DummyBlueprint(BlueprintBase):
                metadata = {"title": "Dummy Blueprint", "env_vars": []}
                def create_agents(self) -> dict:
                    DummyAgent = type("DummyAgent", (), {"name": "DummyAgent"})
                    self.starting_agent = DummyAgent
                    return {"DummyAgent": DummyAgent}

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


def load_conversation_history(conversation_id: Optional[str], messages: List[dict]) -> List[dict]:
    """
    Retrieve conversation history from Redis if available; otherwise, read from the database using the ChatMessage table.
    Combines the stored history with the new incoming messages.
    """
    if not conversation_id:
        return messages  # No previous conversation

    past_messages = []
    if REDIS_AVAILABLE and redis_client:
        try:
            history_raw = redis_client.get(conversation_id)
            if history_raw:
                past_messages = json.loads(history_raw)
        except Exception as e:
            logger.error(f"Error retrieving conversation history from Redis: {e}", exc_info=True)
    else:
        try:
            # Look up the ChatConversation using the conversation_id field
            conversation = ChatConversation.objects.get(conversation_id=conversation_id)
            # Get all related ChatMessage objects (ordered by timestamp)
            past_messages = list(conversation.messages.all().order_by("timestamp").values("sender", "content", "timestamp"))
        except ChatConversation.DoesNotExist:
            past_messages = []

    return past_messages + messages


def store_conversation_history(conversation_id: str, messages: List[dict], response_obj: dict) -> None:
    """
    Store conversation history using the ChatMessage table.
    """
    full_history = messages + [response_obj]

    logger.debug(f"Storing conversation history for conversation_id={conversation_id}")

    if REDIS_AVAILABLE and redis_client:
        try:
            redis_client.set(conversation_id, json.dumps(full_history))
            logger.debug(f"✅ Successfully stored conversation history in Redis for conversation_id={conversation_id}")
            return
        except Exception as e:
            logger.error(f"⚠️ Error storing conversation history in Redis: {e}", exc_info=True)

    try:
        # Get or create the ChatConversation using the conversation_id field
        conversation, created = ChatConversation.objects.get_or_create(conversation_id=conversation_id)
        if created:
            logger.debug(f"🆕 Created new ChatConversation with id={conversation_id}")
        else:
            logger.debug(f"🔄 Retrieved existing ChatConversation with id={conversation_id}")

        # Determine how many messages are already stored
        existing_count = conversation.messages.count()
        new_messages = full_history[existing_count:]

        logger.debug(f"Found {existing_count} existing messages, adding {len(new_messages)} new messages.")

        for msg in new_messages:
            chat_message = ChatMessage.objects.create(
                conversation=conversation,
                sender=msg["role"],
                content=msg["content"]
            )
            logger.debug(f"📩 Stored ChatMessage (id={chat_message.id}) from {msg['role']}: {msg['content'][:50]}")

    except Exception as e:
        logger.error(f"⚠️ Error storing conversation history in database: {e}", exc_info=True)


def run_conversation(blueprint_instance: Any,
                     messages_extended: List[dict],
                     context_vars: dict) -> Tuple[Any, dict]:
    """
    Execute the blueprint's conversation logic and return the response object and updated context.
    """
    result = blueprint_instance.run_with_context(messages_extended, context_vars)
    response_obj = result["response"]
    updated_context = result["context_variables"]
    return response_obj, updated_context


@csrf_exempt
def list_models(request):
    """
    Lists discovered blueprint folders as models.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed. Use GET."}, status=405)

    try:
        data = [
            {
                "id": key,
                "object": "model",
                "title": meta.get("title", "No title"),
                "description": meta.get("description", "No description"),
            }
            for key, meta in blueprints_metadata.items()
        ]
        return JsonResponse({"object": "list", "data": data}, status=200)
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        return JsonResponse({"error": "Internal Server Error"}, status=500)


@csrf_exempt
def django_chat_webpage(request, blueprint_name):
    return render(request, 'django_chat_webpage.html', {'conversation_id': request.GET.get("conversation_id"), 'blueprint_name': blueprint_name})


@csrf_exempt
def blueprint_webpage(request, blueprint_name):
    """
    Serves a webpage for a specific blueprint.
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
    Serves a webpage for the chatbot interface.
    """
    logger.debug("Rendering chatbot webui")
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
