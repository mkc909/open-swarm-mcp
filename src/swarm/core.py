# src/swarm/core.py

"""
Swarm Core Module

Handles the initialization of the Swarm, agent management, and orchestration
of conversations between agents and MCP servers.
"""

# Standard library imports
import copy
import json
import logging
import uuid
from collections import defaultdict
from typing import List, Callable, Union, Optional, Dict, Any

# Package/library imports
import asyncio
from openai import OpenAI

# Local imports
from .util import function_to_json, debug_print, merge_chunk
from .types import (
    Agent,
    AgentFunction,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    Function,
    Response,
    Result,
    Tool,
)

from .extensions.config.config_loader import load_server_config, validate_api_keys, validate_mcp_server_env
from .extensions.mcp.mcp_client import MCPClientManager
from .extensions.mcp.mcp_tool_provider import MCPToolProvider
from .utils.redact import redact_sensitive_data

__CTX_VARS_NAME__ = "context_variables"

# Initialize logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

def repair_message_payload(messages: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Repair the message payload to ensure 'tool' messages have corresponding 'assistant' messages with 'tool_calls'.

    Args:
        messages (List[Dict[str, Any]]): The conversation history messages.
        debug (bool): Whether to enable debug logging.

    Returns:
        List[Dict[str, Any]]: The repaired message list.
    """
    tool_call_map = {}
    repaired_messages = []

    for i, message in enumerate(messages):
        # Collect tool_calls from assistant messages
        if message["role"] == "assistant" and message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                tool_call_map[tool_call["id"]] = message

        repaired_messages.append(message)

        if message["role"] == "tool":
            tool_call_id = message.get("tool_call_id")
            tool_name = message.get("tool_name")

            if not tool_call_id:
                debug_print(debug, f"Skipping tool message at index {i}: Missing 'tool_call_id'.")
                continue

            if not tool_name:
                debug_print(debug, f"Skipping tool message at index {i}: Missing 'tool_name'.")
                continue

            if tool_call_id not in tool_call_map:
                # Add a placeholder assistant message if it doesn't exist
                repaired_message = {
                    "role": "assistant",
                    "content": None,  # Content can be left blank
                    "tool_calls": [
                        {
                            "id": tool_call_id,
                            "function": {"name": tool_name, "arguments": "{}"},
                        }
                    ],
                }
                debug_print(debug, f"Repairing: Adding missing assistant message for tool_call_id {tool_call_id}.")
                repaired_messages.insert(-1, repaired_message)

    debug_print(debug, "Repaired message payload:", repaired_messages)
    return repaired_messages

class Swarm:
    def __init__(self, client=None, config: Optional[dict] = None):
        """
        Initialize the Swarm with an optional custom OpenAI client and preloaded configuration.

        Args:
            client: Custom OpenAI client instance.
            config (Optional[dict]): Preloaded configuration dictionary.
        """
        # Default settings
        self.model = "gpt-4o"
        self.temperature = 0.7
        self.tool_choice = "sequential"
        self.parallel_tool_calls = False
        self.agents: Dict[str, Agent] = {}
        self.mcp_tool_providers = {}
        self.config = config or {}

        try:
            # Validate API keys for the selected LLM profile
            validate_api_keys(self.config, selected_llm="default")
            logger.info("LLM API key validation successful.")

            # Validate MCP server environment variables
            mcp_servers = self.config.get("mcpServers", {})
            validate_mcp_server_env(mcp_servers)
            logger.info("MCP server environment validation successful.")

            # Override default settings from configuration
            llm_config = self.config.get("llm", {}).get("default", {})
            self.model = llm_config.get("model", self.model)
            self.temperature = llm_config.get("temperature", self.temperature)
            self.tool_choice = llm_config.get("tool_choice", self.tool_choice)
            self.parallel_tool_calls = llm_config.get(
                "parallel_tool_calls", self.parallel_tool_calls
            )

            logger.debug(f"Swarm initialized with model={self.model}, "
                         f"temperature={self.temperature}, tool_choice={self.tool_choice}, "
                         f"parallel_tool_calls={self.parallel_tool_calls}.")

            # Initialize the OpenAI client after processing the LLM configuration
            if not client:
                client_kwargs = {}
                if "api_key" in llm_config:
                    client_kwargs["api_key"] = llm_config["api_key"]
                if "base_url" in llm_config:
                    client_kwargs["base_url"] = llm_config["base_url"]

                # Log the client kwargs with sensitive data redacted
                redacted_kwargs = redact_sensitive_data(client_kwargs, sensitive_keys=["api_key"])
                logger.debug(f"Initializing OpenAI client with kwargs: {redacted_kwargs}")

                client = OpenAI(**client_kwargs)
            self.client = client

        except (ValueError, KeyError) as e:
            logger.error(f"Failed to initialize Swarm due to configuration error: {e}")
            raise

        logger.info("Swarm initialized successfully.")

    async def discover_and_merge_agent_tools(self, agent: Agent, debug: bool = False):
        if not agent.mcp_servers:
            logger.debug(f"Agent '{agent.name}' has no assigned MCP servers.")
            return agent.functions

        discovered_tools = []

        for server_name in agent.mcp_servers:
            logger.debug(f"Looking up MCP server '{server_name}' for agent '{agent.name}'.")

            # Extract the server-specific configuration
            server_config = self.config.get("mcpServers", {}).get(server_name)
            if not server_config:
                logger.warning(f"MCP server '{server_name}' not found in configuration.")
                continue

            try:
                # Pass server-specific config to MCPToolProvider
                tool_provider = MCPToolProvider(server_name, server_config)
                logger.info(f"Initialized MCPToolProvider for server '{server_name}'.")

                # Pass the agent to the discover_tools method
                tools = await tool_provider.discover_tools(agent)
                discovered_tools.extend(tools)

            except Exception as e:
                logger.error(f"Error discovering tools for server '{server_name}': {e}", exc_info=True)

        # Combine existing agent functions with discovered tools
        all_functions = agent.functions + discovered_tools
        return all_functions



    def get_chat_completion(
        self,
        agent: Agent,
        history: List[Dict[str, Any]],
        context_variables: dict,
        model_override: Optional[str],
        stream: bool,
        debug: bool,
    ) -> ChatCompletionMessage:
        """
        Prepare and send a chat completion request to the OpenAI API.

        Args:
            agent (Agent): The active agent.
            history (List[Dict[str, Any]]): Conversation history.
            context_variables (dict): Context variables for the conversation.
            model_override (Optional[str]): Model override if any.
            stream (bool): Whether to stream the response.
            debug (bool): Debug flag for verbose output.

        Returns:
            ChatCompletionMessage: The response from the OpenAI API.
        """
        # Ensure the context variables default to strings
        context_variables = defaultdict(str, context_variables)

        # Agent-specific instructions
        instructions = (
            agent.instructions(context_variables)
            if callable(agent.instructions)
            else agent.instructions
        )

        # Begin the message list with the agent's instructions
        messages = [{"role": "system", "content": instructions}] + history

        # Repair message payload before validation
        messages = repair_message_payload(messages, debug=debug)

        # Validate the sequence of messages
        for i in range(1, len(messages)):
            if messages[i]["role"] == "tool" and not messages[i - 1].get("tool_calls"):
                raise ValueError(
                    f"Invalid message sequence: 'tool' message at index {i} must follow an 'assistant' message with 'tool_calls'."
                )

        # Serialize agent functions into 'tools'
        serialized_functions = [function_to_json(f) for f in agent.functions]
        tools = [func_dict for func_dict in serialized_functions]

        # Debug: Log serialized tools
        debug_print(debug, "Serialized tools:", tools)
        print(f"[DEBUG] Serialized tools: {json.dumps(tools, indent=2)}")

        # Adjust tools to remove any reference to 'context_variables'
        for tool in tools:
            params = tool.get("parameters", {})
            properties = params.get("properties", {})
            if __CTX_VARS_NAME__ in properties:
                properties.pop(__CTX_VARS_NAME__)
            required = params.get("required", [])
            if __CTX_VARS_NAME__ in required:
                required.remove(__CTX_VARS_NAME__)

        # Construct the payload
        create_params = {
            "model": model_override or agent.model,
            "messages": messages,
            "tools": tools or None,
            "tool_choice": agent.tool_choice,
            "stream": stream,
        }

        # Include parallel tool calls only if tools are provided
        if tools:
            create_params["parallel_tool_calls"] = agent.parallel_tool_calls

        # Debug: Log the payload before sending
        debug_print(debug, "Chat completion payload:", create_params)
        print(f"[DEBUG] Chat completion payload: {json.dumps(create_params, indent=2)}")

        # Send the request to the OpenAI API
        try:
            return self.client.chat.completions.create(**create_params)
        except Exception as e:
            debug_print(debug, f"Error in chat completion request: {e}")
            raise

    def handle_function_result(self, result, debug) -> Result:
        """
        Process the result returned by an agent function.

        Args:
            result: The raw result returned by the agent function.
            debug (bool): Debug flag for verbose output.

        Returns:
            Result: The processed result object.

        Raises:
            TypeError: If the result cannot be cast to a string or Result object.
        """
        match result:
            case Result() as result_obj:
                return result_obj

            case Agent() as agent:
                return Result(
                    value=json.dumps({"assistant": agent.name}),
                    agent=agent,
                )
            case _:
                try:
                    return Result(value=str(result))
                except Exception as e:
                    error_message = f"Failed to cast response to string: {result}. " \
                                   f"Make sure agent functions return a string or Result object. Error: {str(e)}"
                    debug_print(debug, error_message)
                    raise TypeError(error_message)

    def handle_tool_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[AgentFunction],
        context_variables: dict,
        debug: bool,
    ) -> Response:
        function_map = {f.__name__: f for f in functions}
        partial_response = Response(messages=[], agent=None, context_variables={})

        for tool_call in tool_calls:
            name = tool_call.function.name
            if name not in function_map:
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": f"Error: Tool {name} not found.",
                    }
                )
                continue

            args = json.loads(tool_call.function.arguments)
            func = function_map[name]

            # Pass context variables if required
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = context_variables

            # Execute the function
            try:
                raw_result = func(**args)
                result: Result = self.handle_function_result(raw_result, debug)

                if isinstance(raw_result, Agent):  # Check if the result is an agent
                    partial_response.agent = raw_result  # Set the new active agent

                # Add the tool response
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": result.value if isinstance(result.value, str) else json.dumps(result.value),
                    }
                )
                partial_response.context_variables.update(result.context_variables)

            except Exception as e:
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": f"Error: {str(e)}",
                    }
                )

        return partial_response


    def run_and_stream(
        self,
        agent: Agent,
        messages: List[Dict[str, Any]],
        context_variables: dict = {},
        model_override: Optional[str] = None,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ):
        """
        Generator to run the conversation with streaming responses.

        Args:
            agent (Agent): The agent to run.
            messages (List[Dict[str, Any]]): Initial messages in the conversation.
            context_variables (dict, optional): Context variables for the conversation.
            model_override (Optional[str], optional): Model override if any.
            debug (bool): Whether to enable debug logging.
            max_turns (int): Maximum number of turns to execute.
            execute_tools (bool): Whether to execute tools.

        Yields:
            dict: Chunks of the response.
        """
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        while len(history) - init_len < max_turns:
            message = {
                "content": "",
                "sender": agent.name,
                "role": "assistant",
                "function_call": None,
                "tool_calls": defaultdict(
                    lambda: {
                        "function": {"arguments": "", "name": ""},
                        "id": "",
                        "type": "",
                    }
                ),
            }

            # Get completion with current history, agent
            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=True,
                debug=debug,
            )

            yield {"delim": "start"}
            for chunk in completion:
                try:
                    # Assuming 'delta' is a dict
                    delta = chunk.choices[0].delta
                except Exception as e:
                    print(f"[ERROR] Failed to process chunk: {e}")
                    continue

                if delta.get("role") == "assistant":
                    message["role"] = "assistant"
                if "sender" not in message:
                    message["sender"] = active_agent.name  # Ensure 'sender' is set
                yield delta

                # Merge the delta into the message
                merge_chunk(message, delta)
            yield {"delim": "end"}

            message["tool_calls"] = list(
                message.get("tool_calls", {}).values())
            if not message["tool_calls"]:
                message["tool_calls"] = None
            debug_print(debug, "Received completion:", message)
            history.append(message)

            if not message["tool_calls"] or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # Convert tool_calls to objects
            tool_calls = []
            for tool_call in message["tool_calls"]:
                function = Function(
                    arguments=tool_call["function"]["arguments"],
                    name=tool_call["function"]["name"],
                )
                tool_call_object = ChatCompletionMessageToolCall(
                    id=tool_call["id"], function=function, type=tool_call["type"]
                )
                tool_calls.append(tool_call_object)

            # Handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                tool_calls, active_agent.functions, context_variables, debug
            )
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent

        yield {
            "response": Response(
                messages=history[init_len:],
                agent=active_agent,
                context_variables=context_variables,
            )
        }

    def run(
        self,
        agent: Agent,
        messages: List[Dict[str, Any]],
        context_variables: dict = {},
        model_override: Optional[str] = None,
        stream: bool = False,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ) -> Response:
        """
        Runs the conversation synchronously.

        Args:
            agent (Agent): The agent to run.
            messages (List[Dict[str, Any]]): The conversation history.
            context_variables (dict): Additional context variables.
            model_override (Optional[str]): Model override if any.
            stream (bool): Whether to enable streaming responses.
            debug (bool): Whether to enable debug logging.
            max_turns (int): Maximum number of turns to run.
            execute_tools (bool): Whether to execute tools.

        Returns:
            Response: The response from the agent.
        """
        if stream:
            return self.run_and_stream(
                agent=agent,
                messages=messages,
                context_variables=context_variables,
                model_override=model_override,
                debug=debug,
                max_turns=max_turns,
                execute_tools=execute_tools,
            )
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        while len(history) - init_len < max_turns and active_agent:
            # Get completion with current history, agent
            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=stream,
                debug=debug,
            )
            try:
                message = completion.choices[0].message
            except Exception as e:
                debug_print(debug, f"Failed to get message from completion: {e}")
                print(f"[ERROR] Failed to get message from completion: {e}")
                break

            debug_print(debug, "Received completion:", message)
            message.sender = active_agent.name
            history.append(
                json.loads(message.model_dump_json())
            )  # To avoid OpenAI types (?)

            if not message.tool_calls or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # Handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                message.tool_calls, active_agent.functions, context_variables, debug
            )
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent

        return Response(
            id=f"response-{uuid.uuid4()}",  # Generate a unique ID for the response
            messages=history[init_len:],
            agent=active_agent,
            context_variables=context_variables,
        )
