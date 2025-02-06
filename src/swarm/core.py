# src/swarm/core.py

"""
Swarm Core Module

Handles the initialization of the Swarm, agent management, and orchestration
of conversations between agents and MCP servers.
"""

# Standard library imports
import os
import copy
import inspect
import json
import logging
import uuid
from collections import defaultdict
from typing import List, Optional, Dict, Any

# Package/library imports
import asyncio
from openai import OpenAI

# Local imports
from .util import function_to_json, merge_chunk
from .types import (
    Agent,
    AgentFunction,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    Function,
    Response,
    Result,
)

from .extensions.config.config_loader import (
    load_llm_config,
)
from .extensions.mcp.mcp_tool_provider import MCPToolProvider
from .settings import DEBUG
from .utils.redact import redact_sensitive_data

__CTX_VARS_NAME__ = "context_variables"

# Initialize logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
stream_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(stream_handler)


class Swarm:
    def __init__(self, client=None, config: Optional[dict] = None):
        """
        Initialize the Swarm with an optional custom OpenAI client and preloaded configuration.

        Args:
            client: Custom OpenAI client instance.
            config (Optional[dict]): Preloaded configuration dictionary.
        """
        # Fetch the selected LLM from the environment variable 'LLM', defaulting to 'default'
        self.model = os.getenv("LLM", "default")
        logger.debug(f"Initialized Swarm with model: {self.model}")

        self.temperature = 0.7
        self.tool_choice = "auto"
        self.parallel_tool_calls = False
        self.agents: Dict[str, Agent] = {}
        self.mcp_tool_providers: Dict[str, MCPToolProvider] = {}  # Cache for MCPToolProvider instances
        self.config = config or {}
        try:
            self.current_llm_config = load_llm_config(self.config, self.model)
        except ValueError:
            logger.warning(f"LLM config for model '{self.model}' not found. Falling back to 'default'.")
            self.current_llm_config = load_llm_config(self.config, "default")

        if not self.current_llm_config.get("api_key"):
            if not os.getenv("SUPPRESS_DUMMY_KEY"):
                self.current_llm_config["api_key"] = "sk-DUMMYKEY"
            else:
                logger.debug("SUPPRESS_DUMMY_KEY is set; leaving API key empty.")

        if not client:
            client_kwargs = {}
            if "api_key" in self.current_llm_config:
                client_kwargs["api_key"] = self.current_llm_config["api_key"]
            if "base_url" in self.current_llm_config:
                client_kwargs["base_url"] = self.current_llm_config["base_url"]

            # Log the client kwargs with sensitive data redacted
            redacted_kwargs = redact_sensitive_data(client_kwargs, sensitive_keys=["api_key"])
            logger.debug(f"Initializing OpenAI client with kwargs: {redacted_kwargs}")

            client = OpenAI(**client_kwargs)
        self.client = client

        logger.info("Swarm initialized successfully.")

    async def discover_and_merge_agent_tools(self, agent: Agent, debug: bool = False):
        """
        Discover and merge tools for the given agent from assigned MCP servers.

        Args:
            agent (Agent): The agent for which to discover and merge tools.
            debug (bool): Whether to enable additional debug logging.

        Returns:
            List[AgentFunction]: Combined list of agent's existing functions and newly discovered tools.
        """
        if not agent.mcp_servers:
            logger.debug(f"Agent '{agent.name}' has no assigned MCP servers.")
            return agent.functions

        discovered_tools = []
        # logger.debug(f"Starting tool discovery for agent '{agent.name}' with MCP servers: {agent.mcp_servers}")
        # print(f"Starting tool discovery for agent '{agent.name}' with MCP servers: {agent.mcp_servers}")

        for server_name in agent.mcp_servers:
            logger.debug(f"Looking up MCP server '{server_name}' for agent '{agent.name}'.")

            # Extract the server-specific configuration
            server_config = self.config.get("mcpServers", {}).get(server_name)
            if not server_config:
                logger.warning(f"MCP server '{server_name}' not found in configuration.")
                continue

            # Check if MCPToolProvider for this server is already cached
            if server_name not in self.mcp_tool_providers:
                try:
                    # Initialize and cache the MCPToolProvider
                    tool_provider = MCPToolProvider(server_name, server_config)
                    self.mcp_tool_providers[server_name] = tool_provider
                    logger.debug(f"Initialized MCPToolProvider for server '{server_name}'.")
                except Exception as e:
                    logger.error(f"Failed to initialize MCPToolProvider for server '{server_name}': {e}", exc_info=True)
                    if debug:
                        logger.debug(f"[DEBUG] Exception during MCPToolProvider initialization for server '{server_name}': {e}")
                    continue
            else:
                # Retrieve the cached MCPToolProvider
                tool_provider = self.mcp_tool_providers[server_name]
                logger.debug(f"Using cached MCPToolProvider for server '{server_name}'.")

            try:
                # Discover tools using the cached MCPToolProvider
                tools = await tool_provider.discover_tools(agent)
                if tools:
                    logger.debug(f"Discovered {len(tools)} tools from server '{server_name}' for agent '{agent.name}': {[tool.name for tool in tools if hasattr(tool, 'name')]}")
                    discovered_tools.extend(tools)
                else:
                    logger.warning(f"No tools discovered from server '{server_name}' for agent '{agent.name}'.")
            except Exception as e:
                logger.error(f"Error discovering tools for server '{server_name}': {e}", exc_info=True)
                if debug:
                    logger.debug(f"[DEBUG] Exception during tool discovery for server '{server_name}': {e}")

        # Combine existing agent functions with discovered tools
        all_functions = agent.functions + discovered_tools
        logger.debug(f"Total functions for agent '{agent.name}': {len(all_functions)} (Existing: {len(agent.functions)}, Discovered: {len(discovered_tools)})")
        if debug:
            logger.debug(f"[DEBUG] Existing functions: {[func.name for func in agent.functions if hasattr(func, 'name')]}")
            logger.debug(f"[DEBUG] Discovered tools: {[tool.name for tool in discovered_tools if hasattr(tool, 'name')]}")
            logger.debug(f"[DEBUG] Combined functions: {[func.name for func in all_functions if hasattr(func, 'name')]}")
        
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
        # Load the new llm config from config_loader
        try:
            new_llm_config = load_llm_config(self.config, agent.model or "default")
        except ValueError:
            logger.warning(f"LLM config for model '{agent.model}' not found. Falling back to 'default'.")
            new_llm_config = load_llm_config(self.config, "default")

        # If no API key is provided, insert a dummy key unless SUPPRESS_DUMMY_KEY is set
        if not new_llm_config.get("api_key"):
            if not os.getenv("SUPPRESS_DUMMY_KEY"):
                new_llm_config["api_key"] = "sk-DUMMYKEY"
            else:
                logger.debug("SUPPRESS_DUMMY_KEY is set; leaving API key empty.")

        # Only re-init if the base_url changed
        if new_llm_config.get("base_url") != self.current_llm_config.get("base_url"):
            logger.info(f"Detected base_url change. Re-initializing client for agent '{agent.name}' model '{self.model}'.")

            client_kwargs = {}
            if "api_key" in new_llm_config:
                client_kwargs["api_key"] = new_llm_config["api_key"]
            if "base_url" in new_llm_config:
                client_kwargs["base_url"] = new_llm_config["base_url"]

            redacted_kwargs = redact_sensitive_data(client_kwargs, sensitive_keys=["api_key"])
            logger.debug(f"Re-initializing OpenAI client with new kwargs: {redacted_kwargs}")

            self.client = OpenAI(**client_kwargs)

        self.current_llm_config = new_llm_config

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
        messages = self.repair_message_payload(messages)

        # Serialize agent functions into 'tools'
        serialized_functions = [function_to_json(f) for f in agent.functions]
        tools = [func_dict for func_dict in serialized_functions]

        # Debug: Log serialized tools
        logger.debug(f"Serialized tools: {tools}")
        logger.debug(f"[DEBUG] Serialized tools: {json.dumps(tools, indent=2)}")

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
            "model": model_override or new_llm_config.get("model"),
            "messages": messages,
            "tools": tools or None,
            "tool_choice": agent.tool_choice or "auto",
            "stream": stream,
        }
        if "temperature" in new_llm_config:
            create_params["temperature"] = new_llm_config["temperature"]
        if "reasoning_effort" in new_llm_config:
            create_params["reasoning_effort"] = new_llm_config["reasoning_effort"]
        # Include parallel tool calls only if tools are provided
        # if tools:
        #     create_params["parallel_tool_calls"] = agent.parallel_tool_calls

        # Debug: Log the payload before sending
        logger.debug("Chat completion payload:", create_params)
        logger.debug(f"[DEBUG] Chat completion payload: {json.dumps(create_params, indent=2)}")

        # Send the request to the OpenAI API
        try:
            return self.client.chat.completions.create(**create_params)
        except Exception as e:
            logger.debug(f"Error in chat completion request: {e}")
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
                # When an Agent is returned, encapsulate it within a Result object
                return Result(
                    value=json.dumps({"assistant": agent.name}),
                    agent=agent,
                )
            case _:
                try:
                    return Result(value=str(result))
                except Exception as e:
                    error_message = (
                        f"Failed to cast response to string: {result}. "
                        f"Make sure agent functions return a string or Result object. Error: {str(e)}"
                    )
                    logger.debug(error_message)
                    raise TypeError(error_message)

    def handle_tool_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[AgentFunction],
        context_variables: dict,
        debug: bool,
    ) -> Response:
        """
        Handles tool calls, executing functions and processing results.

        Args:
            tool_calls (List[ChatCompletionMessageToolCall]): The list of tool calls to process.
            functions (List[AgentFunction]): The list of available functions (tools).
            context_variables (dict): Shared context variables for tools.
            debug (bool): Whether to enable debug logging.

        Returns:
            Response: A Response object with tool results.
        """
        # Create a function map for quick lookup
        function_map = {f.__name__: f for f in functions}
        partial_response = Response(messages=[], agent=None, context_variables={})

        for tool_call in tool_calls:
            name = tool_call.function.name
            tool_call_id = tool_call.id

            # Check if the tool exists
            if name not in function_map:
                error_msg = f"Tool {name} not found in function map."
                logger.error(error_msg)
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "tool_name": name,
                        "content": f"Error: {error_msg}",
                    }
                )
                continue

            func = function_map[name]
            args = json.loads(tool_call.function.arguments)

            # Inject context variables if the function accepts them
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = context_variables

            try:
                # Execute the tool
                if getattr(func, "dynamic", False):
                    # For dynamic tools (async)
                    raw_result = asyncio.run(func(**args))
                else:
                    # For static tools (sync)
                    raw_result = func(**args)
                    if inspect.iscoroutine(raw_result):
                        logger.debug("Awaiting coroutine from static tool.")
                        raw_result = asyncio.run(raw_result)

                # Process the result and add it to the response
                result = self.handle_function_result(raw_result, debug)
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "tool_name": name,
                        "content": json.dumps(result.value),
                    }
                )
                partial_response.context_variables.update(result.context_variables)

                # **✅ Updated Agent Switching Logic**
                # Check if the tool call resulted in an agent handoff
                if result.agent:
                    new_agent_name = result.agent.name
                    if new_agent_name and new_agent_name in self.agents:
                        partial_response.agent = result.agent
                        context_variables["active_agent_name"] = new_agent_name  # 🔥 Update context variable
                        logger.debug(f"🔄 Active agent updated to: {new_agent_name}")

                        # **✅ Reload tools for the new agent**
                        new_agent = self.agents[new_agent_name]
                        new_agent.functions = asyncio.run(self.discover_and_merge_agent_tools(new_agent, debug=debug))
                        logger.debug(f"✅ Reloaded tools for new agent: {new_agent_name}")

            except Exception as e:
                error_msg = f"Error executing tool {name}: {str(e)}"
                logger.error(error_msg)
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "tool_name": name,
                        "content": f"Error: {error_msg}",
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

        # Ensure initial active agent name is set
        context_variables["active_agent_name"] = active_agent.name
        if debug:
            logger.debug(f"Initial active_agent_name set to: {active_agent.name}")

        # Discover and merge tools before starting the conversation
        all_functions = asyncio.run(self.discover_and_merge_agent_tools(agent, debug=debug))
        active_agent.functions = all_functions  # Update agent's functions with discovered tools

        while len(history) - init_len < max_turns:
            message = {
                "content": "",
                "sender": active_agent.name,
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
            try:
                completion = self.get_chat_completion(
                    agent=active_agent,
                    history=history,
                    context_variables=context_variables,
                    model_override=model_override,
                    stream=True,
                    debug=debug,
                )
            except Exception as e:
                logger.error(f"Failed to get chat completion: {e}")
                if debug:
                    logger.debug(f"[DEBUG] Exception during get_chat_completion: {e}")
                break

            yield {"delim": "start"}
            for chunk in completion:
                try:
                    # Assuming 'delta' is a dict
                    delta = chunk.choices[0].delta
                except Exception as e:
                    logger.debug(f"[ERROR] Failed to process chunk: {e}")
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
                message.get("tool_calls", {}).values()
            )
            if not message["tool_calls"]:
                message["tool_calls"] = None
            logger.debug(f"Received completion: {message}")
            history.append(message)

            if not message["tool_calls"] or not execute_tools:
                logger.debug("No tool calls or tool execution disabled. Ending turn.")
                break

            # Convert tool_calls to objects
            tool_calls = []
            for tool_call in message["tool_calls"]:
                function = Function(
                    arguments=tool_call["function"]["arguments"],
                    name=tool_call["function"]["name"],
                )
                tool_call_object = ChatCompletionMessageToolCall(
                    id=tool_call["id"],
                    function=function,
                    type=tool_call["type"]
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
                context_variables["active_agent_name"] = active_agent.name  # Update context variable
                if debug:
                    logger.debug(f"Active agent switched to: {active_agent.name}")

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
        """

        all_functions = asyncio.run(self.discover_and_merge_agent_tools(agent, debug=debug))
        agent.functions = all_functions
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

        # Ensure active agent name is set
        context_variables["active_agent_name"] = active_agent.name

        turn_count = 0
        while turn_count < max_turns and active_agent:
            turn_count += 1

            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=stream,
                debug=debug,
            )

            # 1) Extract the completion message from GPT
            try:
                message = completion.choices[0].message
            except Exception as e:
                logger.error(f"Failed to extract message from completion: {e}")
                break

            message.sender = active_agent.name

            # 2) Check the content & tool calls
            raw_content = message.content or ""
            has_tool_calls = bool(message.tool_calls)

            if debug:
                logger.debug(
                    f"[DEBUG] Received message from {message.sender}, "
                    f"raw_content={raw_content!r}, has_tool_calls={has_tool_calls}"
                )

            # **Always** append the assistant message (preserves conversation flow)
            # even if content = None, because it might contain relevant tool_calls
            # or mark an agent switch
            history.append(json.loads(message.model_dump_json()))

            # 3) If the LLM wants to call a tool/function
            if has_tool_calls and execute_tools:
                partial_response = self.handle_tool_calls(
                    message.tool_calls,
                    active_agent.functions,
                    context_variables,
                    debug,
                )
                # Store the tool responses in history
                history.extend(partial_response.messages)
                context_variables.update(partial_response.context_variables)

                # Possibly the agent changes
                if partial_response.agent:
                    active_agent = partial_response.agent
                    context_variables["active_agent_name"] = active_agent.name
                    logger.debug(f"Switched active agent to: {active_agent.name}")

                # After handling tool calls, do NOT break – let the loop continue
                continue

            # 4) If there's actual user-facing content (non-empty text) from GPT
            # we can break out or do another turn if needed
            if raw_content.strip():
                # This is an actual final assistant response to the user
                break
            else:
                # If there's no text and no tool calls, there is no next step
                logger.debug("Empty assistant message with no tool calls. Ending.")
                break

        # 5) Optionally filter out internal system messages, or keep them:
        final_messages = history[init_len:]

        return Response(
            id=f"response-{uuid.uuid4()}",
            messages=final_messages,
            agent=active_agent,
            context_variables=context_variables,
        )

    def validate_message_sequence(self, messages: List[Dict[str, Any]]):
        """
        Validate the sequence of messages to ensure compliance with the expected format.

        Args:
            messages (list): The sequence of messages to validate.

        Raises:
            ValueError: If the sequence is invalid.
        """
        expected_tool_call_ids = set()

        for i, message in enumerate(messages):
            if message["role"] == "assistant":
                # If the assistant message has tool_calls, add their IDs to the expected set
                if message.get("tool_calls"):
                    for tool_call in message["tool_calls"]:
                        expected_tool_call_ids.add(tool_call["id"])
            elif message["role"] == "tool":
                tool_call_id = message.get("tool_call_id")
                if not tool_call_id:
                    raise ValueError(
                        f"Invalid tool message at index {i}: Missing 'tool_call_id'."
                    )
                if tool_call_id not in expected_tool_call_ids:
                    raise ValueError(
                        f"Invalid message sequence: 'tool' message at index {i} with tool_call_id '{tool_call_id}' does not have a corresponding 'assistant' message with 'tool_calls'."
                    )
                # Remove the tool_call_id once it's been validated
                expected_tool_call_ids.remove(tool_call_id)
            else:
                # For other roles, no action needed
                pass

        if expected_tool_call_ids:
            missing = ", ".join(expected_tool_call_ids)
            raise ValueError(f"Missing tool messages for tool_call_ids: {missing}")

    def repair_message_payload(self, messages: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
        """
        Repairs the message sequence by ensuring every assistant message with tool_calls
        is followed by the corresponding tool messages.

        Args:
            messages (List[Dict[str, Any]]): The sequence of chat messages.
            debug (bool): Whether to enable debug logging.

        Returns:
            List[Dict[str, Any]]: The repaired sequence of messages.
        """
        repaired_messages = []
        tool_call_map = {}

        # Step 1: Collect all tool_call_ids from assistant messages
        for idx, message in enumerate(messages):
            if message["role"] == "assistant" and message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    tool_call_id = tool_call.get("id")
                    if not tool_call_id:
                        continue
                    if "function" not in tool_call:
                        logger.warning(f"Missing 'function' in tool_call with id {tool_call_id}. Skipping this tool call.")
                        continue
                    tool_call_map[tool_call_id] = {
                        "function": tool_call["function"],
                        "type": tool_call.get("type", ""),
                        "name": tool_call["function"].get("name", ""),
                    }

        # Step 2: Iterate and ensure that each assistant message with tool_calls is followed by tool messages
        i = 0
        while i < len(messages):
            message = messages[i]
            repaired_messages.append(message)

            if message["role"] == "assistant" and message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    tool_call_id = tool_call["id"]

                    # Ensure a corresponding tool message exists after the assistant message
                    tool_message_exists = False
                    for j in range(i + 1, len(messages)):
                        next_message = messages[j]
                        if next_message["role"] == "tool" and next_message.get("tool_call_id") == tool_call_id:
                            tool_message_exists = True
                            break
                        if next_message["role"] == "assistant":
                            break  # Stop checking if we hit another assistant message

                    if not tool_message_exists:
                        logger.warning(f"Missing tool message for tool_call_id: {tool_call_id}. Repairing...")
                        placeholder_tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "tool_name": tool_call["function"]["name"],
                            "content": "Automatically repaired tool response.",
                        }
                        repaired_messages.append(placeholder_tool_message)

            i += 1

        # Step 3: **Fix orphaned tool messages** that have no corresponding assistant request
        valid_tool_call_ids = set(tool_call_map.keys())
        filtered_messages = []

        for msg in repaired_messages:
            if msg["role"] == "tool":
                if msg.get("tool_call_id") not in valid_tool_call_ids:
                    logger.error(
                        f"[ERROR] Removing orphaned tool message at index {i}: {msg}. No corresponding assistant tool call found."
                    )
                    continue  # Remove the invalid tool message
            filtered_messages.append(msg)

        # Step 4: Validate the repaired sequence
        try:
            self.validate_message_sequence(filtered_messages)
        except ValueError as e:
            logger.error(f"[ERROR] Validation failed after repair: {e}")
            raise

        if debug:
            logger.debug("[DEBUG] Repaired message payload:")
            logger.debug(json.dumps(filtered_messages, indent=2))

        return filtered_messages
