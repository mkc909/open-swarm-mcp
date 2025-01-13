"""
Local version of views.py that uses CONFIG_PATH from environment variables
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
from swarm.utils.logger_setup import setup_logger
from swarm.utils.redact import redact_sensitive_data

# Initialize logger for this module
logger = setup_logger(__name__)

# Load configuration from environment variable
CONFIG_PATH = Path(os.getenv('CONFIG_PATH', str(Path(settings.BASE_DIR) / "swarm_config.json")))
try:
    config = load_server_config(str(CONFIG_PATH))
    redacted_config = redact_sensitive_data(config)
    logger.debug(f"Loaded configuration from {CONFIG_PATH}: {redacted_config}")
except Exception as e:
    logger.critical(f"Failed to load configuration from {CONFIG_PATH}: {e}")
    raise e

# Rest of the file remains the same as views.py
# Discover blueprints
BLUEPRINTS_DIR = (Path(settings.BASE_DIR) / "blueprints").resolve()
try:
    blueprints_metadata = discover_blueprints([str(BLUEPRINTS_DIR)])
    redacted_blueprints_metadata = redact_sensitive_data(blueprints_metadata)
    logger.debug(f"Discovered blueprints metadata: {redacted_blueprints_metadata}")
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


def serialize_swarm_response(response: Any, model_name: str, context_variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize the raw Swarm response to OpenAI-like format.
    """
    messages = response.get("messages", []) if isinstance(response, dict) else getattr(response, "messages", [])
    active_agent = getattr(response, "agent", None)
    last_message = {"content": "", "role": "assistant"}  # Default empty message

    if messages:
        last_message = messages[-1]
        context_variables["active_agent"] = active_agent.name if active_agent else "unknown"

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
        "context_variables": context_variables,
    }


@csrf_exempt
def chat_completions(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        body = json.loads(request.body)
        model = body.get("model", "default")
        messages = body.get("messages", [])
        context_variables = body.get("context_variables", {})

        if not messages:
            return JsonResponse({"error": "Messages are required."}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    blueprint_meta = blueprints_metadata.get(model)
    if not blueprint_meta:
        return JsonResponse({"error": f"Model '{model}' not found."}, status=404)

    blueprint_class = blueprint_meta.get("blueprint_class")
    if not blueprint_class:
        return JsonResponse({"error": f"Blueprint class for model '{model}' is not defined."}, status=500)

    try:
        blueprint_instance = blueprint_class(config=config)
    except Exception as e:
        logger.error(f"Error initializing blueprint: {redact_sensitive_data(e)}", exc_info=True)
        return JsonResponse({"error": f"Error initializing blueprint: {redact_sensitive_data(str(e))}"}, status=500)

    try:
        result = blueprint_instance.run_with_context(messages, context_variables)
        response = result["response"]
        updated_context = result["context_variables"]

        return JsonResponse(
            serialize_swarm_response(response, model, updated_context), 
            status=200
        )
    except Exception as e:
        logger.error(f"Error during execution: {redact_sensitive_data(e)}", exc_info=True)
        return JsonResponse({"error": f"Error during execution: {redact_sensitive_data(str(e))}"}, status=500)


@csrf_exempt
def list_models(request):
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
