"""
REST Mode Views for Open Swarm MCP.

This module defines asynchronous views to handle chat completions and model listings,
aligning with OpenAI's Chat Completions API.

Endpoints:
    - POST /v1/chat/completions: Handles chat completion requests.
    - GET /v1/models: Lists available blueprints as models.
"""

import os
import json
import uuid
import time
import logging
import asyncio
from typing import Any, Dict, List
from pathlib import Path

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render

from swarm import Swarm

from swarm.extensions.blueprint import discover_blueprints
from swarm.extensions.config.config_loader import (
    load_server_config,
    validate_api_keys,
    load_llm_config,
)

from .utils.logger import setup_logger

# Initialize logger for this module
logger = setup_logger(__name__)

# Load configuration from 'swarm_config.json'
CONFIG_PATH = Path(settings.BASE_DIR) / "swarm_config.json"
try:
    config = load_server_config(str(CONFIG_PATH))
    logger.debug(f"Loaded configuration from {CONFIG_PATH}: {config}")
except Exception as e:
    logger.critical(f"Failed to load configuration from {CONFIG_PATH}: {e}")
    raise e

# Discover blueprints located in the 'blueprints' directory
BLUEPRINTS_DIR = (Path(settings.BASE_DIR) / "blueprints").resolve()
logger.debug(f"Attempting to locate blueprints at: {BLUEPRINTS_DIR}")
try:
    blueprints_metadata = discover_blueprints([str(BLUEPRINTS_DIR)])
    logger.debug(f"Discovered blueprints metadata: {blueprints_metadata}")
except Exception as e:
    logger.error(f"Error discovering blueprints: {e}", exc_info=True)
    raise e

# Inject LLM metadata into blueprints
try:
    llm_config = load_llm_config(config)
    llm_model = llm_config.get("model", "gpt-4o")
    llm_provider = llm_config.get("provider", "openai")
    logger.debug(f"Loaded LLM configuration: Provider='{llm_provider}', Model='{llm_model}'")

    for blueprint in blueprints_metadata.values():
        blueprint["openai_model"] = llm_model
        blueprint["llm_provider"] = llm_provider
    logger.debug(f"Updated blueprints with LLM metadata: {blueprints_metadata}")
except ValueError as e:
    logger.critical(f"Failed to load LLM configuration: {e}")
    raise e

def get_file_modification_timestamp(file_path: str) -> int:
    """
    Get the modification timestamp of a file.

    Args:
        file_path (str): Path to the file.

    Returns:
        int: Timestamp of the last modification.
    """
    try:
        timestamp = int(os.path.getmtime(file_path))
        logger.debug(f"Modification timestamp for '{file_path}': {timestamp}")
        return timestamp
    except Exception as e:
        logger.error(f"Error getting modification timestamp for {file_path}: {e}", exc_info=True)
        return int(time.time())

def construct_openai_response(response: Any, openai_model: str) -> Dict[str, Any]:
    """
    Constructs a response dictionary conforming to OpenAI's Chat Completion API format.

    Args:
        response (Any): The response from Swarm.run (can be a dictionary or an object with a 'messages' attribute).
        openai_model (str): The actual OpenAI model name used for the request.

    Returns:
        Dict[str, Any]: The formatted response dictionary.

    Raises:
        ValueError: If the response is invalid or missing required data.
    """
    logger.debug("Constructing OpenAI-like response.")

    # Guard: Ensure response is not None
    if response is None:
        logger.error("Invalid response: response is None.")
        raise ValueError("Invalid response: response is None.")

    # Extract messages from response (handles both dictionary and object)
    if isinstance(response, dict):
        messages = response.get('messages', [])
    elif hasattr(response, 'messages'):
        messages = response.messages
    else:
        logger.error("Invalid response: response is not a dictionary or object with 'messages' attribute.")
        raise ValueError("Invalid response: response is not a dictionary or object with 'messages' attribute.")

    # Guard: Ensure messages is a non-empty list
    if not isinstance(messages, list) or len(messages) == 0:
        logger.error("Invalid response: 'messages' is not a list or is empty.")
        raise ValueError("Invalid response: 'messages' is not a list or is empty.")

    # Select all assistant messages with non-None content
    assistant_messages = [m for m in messages if m.get("role") == "assistant" and m.get("content") is not None]

    if not assistant_messages:
        assistant_messages = [{"content": "No response.", "role": "assistant", "sender": "Assistant"}]
        logger.debug("No assistant messages found; defaulting to 'No response.'")

    # Use the last assistant message
    assistant_message = assistant_messages[-1]
    logger.debug(f"Selected assistant message: {assistant_message}")

    # Generate a unique response ID
    response_id = f"swarm-chat-completion-{uuid.uuid4()}"
    logger.debug(f"Generated response ID: {response_id}")

    # Calculate token counts
    prompt_tokens = sum(len(msg['content'].split()) for msg in messages if msg['role'] in ['user', 'system'])
    completion_tokens = len(assistant_message['content'].split()) if assistant_message['content'] != "No response." else 0
    total_tokens = prompt_tokens + completion_tokens

    logger.debug(
        f"Token counts - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}"
    )

    # Return the formatted response
    return {
        "id": response_id,
        "object": "chat.completion",
        "created": 0, # TODO get_file_modification_timestamp(openai_model)?
        "model": openai_model,  # Use the actual OpenAI model name from server config
        "choices": [
            {
                "index": 0,
                "message": assistant_message,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
    }

async def run_swarm_sync(swarm_instance: Swarm, **params) -> Any:
    """
    Wraps the synchronous `swarm_instance.run` method in an asynchronous context.

    Args:
        swarm_instance (Swarm): The Swarm instance to run.
        **params: Parameters to pass to the Swarm.run method.

    Returns:
        Any: The response from Swarm.run.
    """
    loop = asyncio.get_event_loop()
    logger.debug("Running Swarm instance in executor.")
    return await loop.run_in_executor(None, lambda: swarm_instance.run(**params))

@csrf_exempt
def chat_completions(request):
    """
    Handles Chat Completion requests similar to OpenAI's /v1/chat/completions endpoint.
    """
    if request.method != 'POST':
        logger.debug(f"Invalid request method: {request.method}")
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        body = json.loads(request.body)
        logger.debug(f"Parsed JSON body: {body}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}", exc_info=True)
        return JsonResponse({"error": "Unexpected error parsing JSON."}, status=400)

    model = body.get('model', 'default')  # Blueprint identifier
    logger.debug(f"Extracted model/blueprint: '{model}'")

    if 'messages' not in body or not body['messages']:
        logger.error("Messages are required in the request body.")
        return JsonResponse({"error": "Messages are required."}, status=400)

    messages = body['messages']
    logger.debug(f"Received messages: {messages}")

    if model not in blueprints_metadata:
        logger.error(f"Model/blueprint '{model}' not found.")
        return JsonResponse({"error": f"Model '{model}' not found."}, status=404)

    blueprint_meta = blueprints_metadata[model]
    logger.debug(f"Blueprint metadata for '{model}': {blueprint_meta}")
    openai_model = blueprint_meta.get("openai_model", llm_model)
    llm_provider = blueprint_meta.get("llm_provider", 'openai')
    logger.debug(f"Selected LLM configuration: Provider='{llm_provider}', Model='{openai_model}'")

    blueprint_class = blueprint_meta.get("blueprint_class")
    if not blueprint_class:
        logger.error(f"Blueprint class for model '{model}' is not defined.")
        return JsonResponse({"error": f"Blueprint class for model '{model}' is not defined."}, status=500)

    try:
        # Override the model in the configuration by passing 'model_override'
        blueprint_instance = blueprint_class(config=config, model_override=openai_model)
        logger.debug(f"Blueprint instance created for '{model}'.")
    except Exception as e:
        logger.error(f"Error instantiating blueprint for model '{model}': {e}")
        return JsonResponse({"error": f"Failed to initialize blueprint: {e}"}, status=500)

    try:
        agent_map = blueprint_instance.get_agents()
        if not agent_map:
            logger.error(f"No agents found for the specified model '{model}'.")
            return JsonResponse({"error": "No agents found for the specified model."}, status=500)
        starting_agent = list(agent_map.values())[0]
        logger.debug(f"Retrieved starting agent: {starting_agent.name}")
    except Exception as e:
        logger.error(f"Error retrieving agents: {e}")
        return JsonResponse({"error": f"Error retrieving agents: {e}"}, status=500)

    try:
        # Assuming you have a Swarm class that handles agent interactions
        swarm_instance = Swarm()
        params = {
            "agent": starting_agent,
            "messages": messages,
            "context_variables": {},
            "model_override": openai_model,
            "debug": True,
            "max_turns": 10,
            "execute_tools": True,
        }
        logger.debug(f"Running swarm with parameters: {params}")

        response = swarm_instance.run(**params)
        logger.debug(f"Swarm response: {response}")

        # Construct the response in OpenAI's format
        openai_response = construct_openai_response(response, openai_model)
        logger.debug(f"Constructed OpenAI response: {openai_response}")
        return JsonResponse(openai_response, status=200)
    except Exception as e:
        logger.error(f"Internal server error during Swarm execution: {e}", exc_info=True)
        return JsonResponse({"error": f"Internal server error during Swarm execution: {e}"}, status=500)

@csrf_exempt
async def list_models(request):
    """
    Lists discovered blueprint folders as 'models' (like OpenAI's /v1/models).
    """
    logger.debug("Received /v1/models request")
    if request.method != "GET":
        logger.warning(f"Invalid HTTP method: {request.method}")
        return JsonResponse({"error": "Method not allowed. Use GET."}, status=405)

    try:
        data = []
        for folder_name, metadata in blueprints_metadata.items():
            blueprint_file = os.path.join(BLUEPRINTS_DIR, folder_name, f"blueprint_{folder_name}.py")
            created_timestamp = get_file_modification_timestamp(blueprint_file)
            title = metadata.get("title", "No title available")
            description = metadata.get("description", "No description available")
            data.append({
                "id": folder_name,
                "object": "model",
                "created": created_timestamp,
                "owned_by": "open-swarm-mcp",
                "permissions": [],
                "root": None,
                "parent": None,
                "title": title,
                "description": description,
            })
            logger.debug(f"Added model '{folder_name}': Title='{title}', Description='{description}'")

        logger.debug(f"Listing all models: {data}")
        return JsonResponse({"object": "list", "data": data}, status=200)
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        return JsonResponse({"error": "Internal Server Error"}, status=500)

@csrf_exempt
def blueprint_webpage(request, blueprint_name):
    """
    Serves a webpage for a specific blueprint.

    Args:
        request: The HTTP request object.
        blueprint_name (str): The name of the blueprint.

    Returns:
        HttpResponse: The rendered blueprint webpage or a 404 error.
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
    return render(request, "rest_mode/blueprint_page.html", {"blueprint_name": blueprint_name})