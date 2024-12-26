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
from typing import Any, Dict, List, AsyncGenerator, Generator, cast
from functools import partial
from pathlib import Path

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .utils.logger import setup_logger
from swarm import Agent, Swarm

from open_swarm_mcp.config.blueprint_discovery import discover_blueprints
from open_swarm_mcp.config.config_loader import load_server_config

# Initialize logger for this module
logger = setup_logger(__name__)

# Load configuration
CONFIG_PATH = Path(settings.BASE_DIR) / "mcp_server_config.json"
config = load_server_config(str(CONFIG_PATH))
logger.debug(f"Loaded configuration in REST views: {config}")

# Discover blueprints
BLUEPRINTS_DIR = (Path(settings.BASE_DIR).parent / "blueprints").resolve()
logger.debug(f"Attempting to locate blueprints at: {BLUEPRINTS_DIR}")
blueprints_metadata = discover_blueprints([str(BLUEPRINTS_DIR)])

# Example blueprint_metadata after discovery (ensure 'openai_model' is included)
# blueprints_metadata = {
#     "default": {
#         "title": "Default Simple Agent",
#         "description": "A simple agent that echoes user inputs.",
#         "required_mcp_servers": [],
#         "env_vars": [],
#         "blueprint_class": <class 'blueprints.default.blueprint_default.DefaultBlueprint'>,
#         "openai_model": "gpt-3.5-turbo"  # Ensure this key exists
#     },
#     # Add other blueprints similarly
# }

logger.debug(f"Loaded blueprints metadata for REST views: {blueprints_metadata}")


def get_current_timestamp() -> int:
    """
    Retrieve the current UNIX timestamp.

    Returns:
        int: Current timestamp in seconds since the epoch.
    """
    return int(time.time())


def construct_openai_response(response: Any, openai_model: str) -> Dict[str, Any]:
    """
    Constructs a response dictionary conforming to OpenAI's Chat Completion API format.

    Args:
        response (Any): The response from Swarm.run.
        openai_model (str): The actual OpenAI model name used for the request.

    Returns:
        Dict[str, Any]: The formatted response dictionary.
    """
    # Select the first assistant message with non-None content
    assistant_message = next(
        (m.get("content") for m in response.messages if m.get("role") == "assistant" and m.get("content") is not None),
        "No response."
    )

    logger.debug(f"Selected assistant message: {assistant_message}")

    response_id = f"swarm-chat-completion-{uuid.uuid4()}"
    prompt_tokens = sum(len(msg['content'].split()) for msg in response.messages if msg['role'] in ['user', 'system'])
    completion_tokens = len(assistant_message.split()) if assistant_message != "No response." else 0
    total_tokens = prompt_tokens + completion_tokens

    logger.debug(f"Constructed OpenAI-like response: response_id={response_id}, prompt_tokens={prompt_tokens}, "
                 f"completion_tokens={completion_tokens}, total_tokens={total_tokens}, assistant_message={assistant_message}")
    return {
        "id": response_id,
        "object": "chat.completion",
        "created": get_current_timestamp(),
        "model": openai_model,  # Use the actual OpenAI model name
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": assistant_message
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
    }


@csrf_exempt
async def chat_completions(request):
    """
    Handles Chat Completion requests similar to OpenAI's /v1/chat/completions endpoint.
    """
    logger.debug("Received /v1/chat/completions request")

    if request.method != 'POST':
        logger.warning(f"Invalid HTTP method: {request.method}")
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        body = json.loads(request.body)
        logger.debug(f"Request payload: {body}")

        model = body.get('model', 'default')  # Blueprint identifier
        messages = body.get('messages')

        # Validate model exists
        if model not in blueprints_metadata:
            logger.warning(f"Model '{model}' not found. Available models: {list(blueprints_metadata.keys())}")
            return JsonResponse({"error": f"Model '{model}' not found."}, status=404)

        logger.debug(f"Model '{model}' found in metadata: {blueprints_metadata[model]}")

        # Retrieve the actual OpenAI model name
        openai_model = blueprints_metadata[model].get("openai_model", "gpt-3.5-turbo")
        logger.debug(f"Using OpenAI model '{openai_model}' for blueprint '{model}'")

        # Retrieve the blueprint class and agent
        blueprint_class = blueprints_metadata[model].get("blueprint_class")
        if not blueprint_class:
            logger.error(f"Blueprint class for model '{model}' is not defined.")
            return JsonResponse({"error": f"Blueprint class for model '{model}' is not defined."}, status=500)

        try:
            logger.debug(f"Instantiating blueprint class for model '{model}'")
            blueprint_instance = blueprint_class()
        except Exception as e:
            logger.error(f"Error instantiating blueprint for model '{model}': {e}", exc_info=True)
            return JsonResponse({"error": f"Failed to initialize blueprint: {e}"}, status=500)

        try:
            agent_map = blueprint_instance.get_agents()
            if not agent_map:
                logger.error(f"No agents found for blueprint model '{model}'.")
                return JsonResponse({"error": "No agents found for model."}, status=500)

            starting_agent = list(agent_map.values())[0]
            logger.debug(f"Using starting agent: {starting_agent.name}")
        except Exception as e:
            logger.error(f"Error retrieving agents for model '{model}': {e}", exc_info=True)
            return JsonResponse({"error": f"Error retrieving agents: {e}"}, status=500)

        # Initialize Swarm and execute
        try:
            logger.debug("Initializing Swarm instance")
            swarm_instance = Swarm()
            logger.debug(f"Swarm instance initialized. Running Swarm with starting agent '{starting_agent.name}'")

            # Prepare parameters for Swarm.run
            params = {
                "agent": starting_agent,
                "messages": messages,
                "context_variables": {},  # Extend as needed
                "model_override": openai_model,  # Pass the actual OpenAI model
                "debug": True,  # Enable debug logging
                "max_turns": 10,  # Adjust as needed
                "execute_tools": True,
            }

            logger.debug(f"Parameters for Swarm.run: {params}")

            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: swarm_instance.run(**params)
            )

            logger.debug(f"Swarm execution completed. Response: {response}")

            openai_response = construct_openai_response(response, openai_model)  # Use openai_model here
            return JsonResponse(openai_response, status=200)

        except Exception as e:
            logger.error(f"Error during Swarm execution for model '{model}': {e}", exc_info=True)
            return JsonResponse({"error": f"Internal server error during Swarm execution: {e}"}, status=500)

    except json.JSONDecodeError as jde:
        logger.error(f"JSON decode error: {jde}", exc_info=True)
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)
    except Exception as e:
        logger.error(f"Error processing /v1/chat/completions request: {e}", exc_info=True)
        return JsonResponse({"error": "Internal Server Error"}, status=500)


@csrf_exempt
async def list_models(request):
    """
    Lists discovered blueprint folders as 'models' (like OpenAI's /v1/models).
    """
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed. Use GET."}, status=405)

    try:
        data = [
            {
                "id": folder_name,
                "object": "model",
                "created": get_current_timestamp(),
                "owned_by": "open-swarm-mcp",
                "permissions": [],
                "root": None,
                "parent": None
            }
            for folder_name, metadata in blueprints_metadata.items()
        ]
        logger.debug(f"List of models prepared: {data}")
        return JsonResponse({"object": "list", "data": data}, status=200)

    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        return JsonResponse({"error": "Internal Server Error"}, status=500)
