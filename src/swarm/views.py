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
from typing import Any, Dict, List
from pathlib import Path

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render


from swarm.extensions.blueprint import discover_blueprints
from swarm.extensions.config.config_loader import (
    load_server_config,
    load_llm_config,
)
from swarm.utils.logger import setup_logger

# Initialize logger for this module
logger = setup_logger(__name__)

# Load configuration
CONFIG_PATH = Path(settings.BASE_DIR) / "swarm_config.json"
try:
    config = load_server_config(str(CONFIG_PATH))
    logger.debug(f"Loaded configuration from {CONFIG_PATH}: {config}")
except Exception as e:
    logger.critical(f"Failed to load configuration from {CONFIG_PATH}: {e}")
    raise e

# Discover blueprints
BLUEPRINTS_DIR = (Path(settings.BASE_DIR) / "blueprints").resolve()
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

    for blueprint in blueprints_metadata.values():
        blueprint["openai_model"] = llm_model
        blueprint["llm_provider"] = llm_provider
except ValueError as e:
    logger.critical(f"Failed to load LLM configuration: {e}")
    raise e

# def construct_openai_response(response: Any, openai_model: str) -> Dict[str, Any]:
#     logger.debug("Constructing OpenAI-like response.")

#     if response is None:
#         logger.error("Invalid response: response is None.")
#         raise ValueError("Invalid response: response is None.")

#     # Extract messages
#     messages = response.get("messages", []) if isinstance(response, dict) else getattr(response, "messages", [])
#     if not isinstance(messages, list):
#         logger.error("Invalid response: 'messages' is not a list.")
#         raise ValueError("Invalid response: 'messages' is not a list.")

#     # Initialize result containers
#     structured_messages = []
#     tool_calls_buffer = []

#     for msg in messages:
#         if msg.get("role") == "assistant":
#             # Ensure tool_calls are properly structured with all required fields
#             if tool_calls_buffer:
#                 for tool_call in tool_calls_buffer:
#                     tool_call["id"] = tool_call.get("tool_call_id", f"call_{uuid.uuid4()}")  # Assign id if missing
#                     tool_call["type"] = tool_call.get("type", "function")  # Assign default type
#             structured_message = {
#                 "role": "assistant",
#                 "content": msg.get("content"),
#                 "tool_calls": tool_calls_buffer if tool_calls_buffer else None,
#                 "sender": msg.get("sender", "Assistant"),
#             }
#             tool_calls_buffer = []  # Reset buffer
#             structured_messages.append(structured_message)
#         elif msg.get("role") == "tool":
#             tool_calls_buffer.append({
#                 "role": "tool",
#                 "tool_call_id": msg.get("tool_call_id"),
#                 "tool_name": msg.get("tool_name"),
#                 "content": msg.get("content"),
#                 "type": "function",  # Explicitly set type
#             })
#             structured_messages.append(tool_calls_buffer[-1])  # Add tool message immediately after
#         else:
#             structured_messages.append(msg)

#     assistant_messages = [m for m in structured_messages if m.get("role") == "assistant"]
#     if not assistant_messages:
#         assistant_message = {
#             "role": "assistant",
#             "content": "No response.",
#             "sender": "Assistant",
#         }
#         structured_messages.append(assistant_message)

#     assistant_message = assistant_messages[-1] if assistant_messages else structured_messages[-1]

#     response_id = f"swarm-chat-completion-{uuid.uuid4()}"
#     logger.debug(f"Generated response ID: {response_id}")

#     prompt_tokens = sum(len((msg.get("content") or "").split()) for msg in structured_messages if msg.get("role") in ["user", "system"])
#     completion_tokens = sum(len((msg.get("content") or "").split()) for msg in structured_messages if msg.get("role") not in ["user", "system"])
#     total_tokens = prompt_tokens + completion_tokens

#     logger.debug(f"Token counts - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")

#     return {
#         "id": response_id,
#         "object": "chat.completion",
#         "created": int(time.time()),
#         "model": openai_model,
#         "choices": [
#             {
#                 "index": 0,
#                 "message": assistant_message,
#                 "tool_calls": assistant_message.get("tool_calls"),
#                 "finish_reason": "stop",
#             }
#         ],
#         "usage": {
#             "prompt_tokens": prompt_tokens,
#             "completion_tokens": completion_tokens,
#             "total_tokens": total_tokens,
#         },
#     }

def serialize_swarm_response(response: Any, model_name: str) -> Dict[str, Any]:
    """
    Serialize the raw Swarm response to OpenAI-like format.
    """
    # Extract the last message and active agent
    messages = response.get("messages", []) if isinstance(response, dict) else getattr(response, "messages", [])
    active_agent = getattr(response, "agent", None)

    if messages:
        # Update the agent context if necessary
        last_message = messages[-1]
        context_variables["active_agent"] = active_agent.name

    # Format the response for OpenAI
    response_id = f"swarm-chat-completion-{uuid.uuid4()}"
    return {
        "id": response_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": last_message,
                "tool_calls": last_message.get("tool_calls", []),
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": sum(len((msg.get("content") or "").split()) for msg in messages),
            "completion_tokens": sum(len((msg.get("content") or "").split()) for msg in messages if msg.get("role") == "assistant"),
            "total_tokens": len(messages),
        },
    }

@csrf_exempt
def chat_completions(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        body = json.loads(request.body)
        model = body.get("model", "default")
        messages = body.get("messages", [])
        context_variables = body.get("context_variables", {})  # Pass full context

        if not messages:
            return JsonResponse({"error": "Messages are required."}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    # Validate and initialize the blueprint
    blueprint_meta = blueprints_metadata.get(model)
    if not blueprint_meta:
        return JsonResponse({"error": f"Model '{model}' not found."}, status=404)

    blueprint_class = blueprint_meta.get("blueprint_class")
    if not blueprint_class:
        return JsonResponse({"error": f"Blueprint class for model '{model}' is not defined."}, status=500)

    try:
        blueprint_instance = blueprint_class(config=config)
    except Exception as e:
        logger.error(f"Error initializing blueprint: {e}", exc_info=True)
        return JsonResponse({"error": f"Error initializing blueprint: {e}"}, status=500)

    try:
        # Run the blueprint with the provided messages and context
        result = blueprint_instance.run_with_context(messages, context_variables)
        response = result["response"]
        updated_context = result["context_variables"]

        # Construct the choices array for frontend compatibility
        choices = [
            {
                "index": i,
                "message": message,
                "tool_calls": message.get("tool_calls", []),
                "finish_reason": "stop",
            }
            for i, message in enumerate(response.messages)
        ]

        # Safely use the response ID
        return JsonResponse({
            "id": getattr(response, "id", "unknown"),
            "choices": choices,
            "context_variables": updated_context,
        }, status=200)
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        return JsonResponse({"error": f"Error during execution: {e}"}, status=500)

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