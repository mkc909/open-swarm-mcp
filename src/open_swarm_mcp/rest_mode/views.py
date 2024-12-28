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
BLUEPRINTS_DIR = (Path(settings.BASE_DIR) / "blueprints").resolve()
logger.debug(f"Attempting to locate blueprints at: {BLUEPRINTS_DIR}")
blueprints_metadata = discover_blueprints([str(BLUEPRINTS_DIR)])

logger.debug(f"Loaded blueprints metadata for REST views: {blueprints_metadata}")


def get_file_modification_timestamp(file_path: str) -> int:
    """
    Get the modification timestamp of a file.

    Args:
        file_path (str): Path to the file.

    Returns:
        int: Timestamp of the last modification.
    """
    try:
        return int(os.path.getmtime(file_path))
    except Exception as e:
        logger.error(f"Error getting modification timestamp for {file_path}: {e}")
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

    # Guard: Ensure openai_model is not None or empty
    if not openai_model:
        logger.error("Invalid openai_model: openai_model is None or empty.")
        raise ValueError("Invalid openai_model: openai_model is None or empty.")

    # Select the first assistant message with non-None content
    assistant_message = next(
        (m for m in messages if m.get("role") == "assistant" and m.get("content") is not None),
        {"content": "No response."}
    )
    logger.debug(f"Selected assistant message: {assistant_message}")

    # Generate a unique response ID
    response_id = f"swarm-chat-completion-{uuid.uuid4()}"

    # Calculate token counts
    prompt_tokens = sum(len(msg['content'].split()) for msg in messages if msg['role'] in ['user', 'system'])
    completion_tokens = len(assistant_message['content'].split()) if assistant_message['content'] != "No response." else 0
    total_tokens = prompt_tokens + completion_tokens

    logger.debug(
        f"Constructed OpenAI-like response: response_id={response_id}, prompt_tokens={prompt_tokens}, "
        f"completion_tokens={completion_tokens}, total_tokens={total_tokens}, assistant_message={assistant_message}"
    )

    # Return the formatted response
    return {
        "id": response_id,
        "object": "chat.completion",
        "created": get_file_modification_timestamp(openai_model),
        "model": openai_model,  # Use the actual OpenAI model name
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

async def run_swarm_sync(swarm_instance, **params):
    """
    Wraps the synchronous `swarm_instance.run` method in an asynchronous context.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: swarm_instance.run(**params))

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
        
        # Validate messages
        if 'messages' not in body or not body['messages']:
            logger.warning("Empty or missing messages in request")
            return JsonResponse({"error": "Messages are required"}, status=400)
        
        messages = body['messages']
        
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
            
            # Use the helper function to run the Swarm synchronously
            response = await run_swarm_sync(swarm_instance, **params)
            
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
    if request.method != "GET":
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

        return JsonResponse({"object": "list", "data": data}, status=200)
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        return JsonResponse({"error": "Internal Server Error"}, status=500)

@csrf_exempt
def blueprint_webpage(request, blueprint_name):
    if blueprint_name not in blueprints_metadata:
        available_blueprints = "".join(f"<li>{bp}</li>" for bp in blueprints_metadata)
        return HttpResponse(
            f"<h1>Blueprint '{blueprint_name}' not found.</h1><p>Available blueprints:</p><ul>{available_blueprints}</ul>",
            status=404,
        )

    return render(request, "rest_mode/blueprint_page.html", {"blueprint_name": blueprint_name})
