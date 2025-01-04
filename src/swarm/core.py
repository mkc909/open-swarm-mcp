# src/swarm/core.py

"""
Swarm Core Module

Handles the initialization of the Swarm, agent management, and orchestration
of conversations between agents and MCP servers.
"""

# Standard library imports
import copy
import json
import os
from collections import defaultdict
from typing import List, Callable, Union, Optional, Dict, Any

# Third-party imports
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
    Tool,  # Added Tool import
)
from .extensions.mcp.mcp_client import MCPClientManager

# Configure logger
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

__CTX_VARS_NAME__ = "context_variables"


class Swarm:
    """
    The core Swarm class for running Agents and orchestrating
    their dynamic behaviors, including optional MCP tool loading
    and environment variable usage.
    """

    def __init__(self, client=None, config_path: Optional[str] = None):
        """
        Initialize the Swarm with an optional custom OpenAI client.
        If no client is provided, a default is created.

        Args:
            client: Custom OpenAI client instance.
            config_path (Optional[str]): Path to the configuration file.
        """
        logger.debug("Initializing Swarm instance.")
        if not client:
            client = OpenAI()
            logger.debug("No OpenAI client provided. Created default client.")
        self.client = client

        # Initialize MCP Client Managers
        self.mcp_clients: Dict[str, MCPClientManager] = {}
        logger.debug("Initialized MCP clients dictionary.")

        # Initialize agents
        self.agents: Dict[str, Agent] = {}

        # Load configuration and validate API keys
        self.config_path = config_path or self._get_default_config_path()
        logger.debug(f"Config path set to: {self.config_path}")
        self.config = self.load_configuration()
        selected_llm = self.config.get("selectedLLM")
        self.validate_api_keys(selected_llm)

        # Flag to indicate whether MCP sessions have been initialized
        self.mcp_initialized = False

        logger.debug("Swarm instance initialized successfully.")

    def _get_default_config_path(self) -> str:
        """
        Return the default config file path 'swarm_config.json' in the current working directory.

        Returns:
            str: The default configuration file path.
        """
        from pathlib import Path

        default_path = str(Path.cwd() / "swarm_config.json")
        logger.debug(f"Default configuration path: {default_path}")
        return default_path

    def load_configuration(self) -> dict:
        """
        Load configuration from the given path or use a default empty config.

        Returns:
            dict: The loaded configuration.
        """
        logger.debug(f"Loading configuration from: {self.config_path}")
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file '{self.config_path}' not found. Using an empty config.")
            return {}

        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from '{self.config_path}'.")
                logger.debug(f"Configuration content: {config}")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file '{self.config_path}': {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading configuration file '{self.config_path}': {e}")
            raise

    def validate_api_keys(self, selected_llm: Optional[str] = None):
        """
        Validates API keys for the LLM configuration.
        - If `api_key` is an empty string, no validation is performed.
        - If `api_key` contains a placeholder like '${SOME_API_KEY}', the corresponding environment variable must be set.
        - Validation applies only to the selected LLM provider.

        Args:
            selected_llm (Optional[str]): The selected LLM profile.

        Raises:
            ValueError: If a required environment variable is missing for the selected LLM profile.
        """
        logger.debug(f"Validating API keys with selected LLM: {selected_llm}")
        if not selected_llm:
            selected_llm = "default"
            logger.info(f"No selected LLM profile provided. Falling back to default profile: '{selected_llm}'.")

        llm_config = self.config.get("llm", {}).get(selected_llm, {})
        api_key = llm_config.get("api_key", "")

        if not api_key:
            logger.info(f"No API key validation required for LLM profile '{selected_llm}' (empty API key).")
            return

        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            env_value = os.getenv(env_var)
            logger.debug(f"Checking environment variable '{env_var}': {env_value}")

            if not env_value:
                error_msg = (
                    f"Environment variable '{env_var}' required for API key in LLM profile '{selected_llm}' "
                    f"is not set or empty."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.debug(f"Environment variable '{env_var}' found with value: {env_value} (masked).")
        else:
            logger.debug(f"Static API key provided for LLM profile '{selected_llm}': {api_key} (masked).")

    def create_agent(self, agent: Agent) -> Agent:
        """
        Extend the agent with dynamic tools from MCP servers and attach environment variables.

        Args:
            agent (Agent): The agent to be created.

        Returns:
            Agent: The created agent with attached tools.
        """
        debug_print(True, f"Swarm: Creating agent '{agent.name}' with MCP servers {agent.mcp_servers} and env_vars {agent.env_vars}")
        logger.debug(f"Swarm: Creating agent '{agent.name}' with MCP servers {agent.mcp_servers} and env_vars {agent.env_vars}")

        # Register the agent
        self.agents[agent.name] = agent
        logger.info(f"Agent '{agent.name}' registered with Swarm.")
        logger.debug(f"Registered agents: {list(self.agents.keys())}")
        logger.debug(f"Agent '{agent.name}' functions: {[f.__name__ for f in agent.functions]}")

        # Collect required MCP servers
        required_servers = set(agent.mcp_servers) if agent.mcp_servers else set()

        # Initialize MCP sessions if not already done and there are required servers
        if not self.mcp_initialized and required_servers:
            self.initialize_mcp_sessions(required_servers)

        # Dynamically load tools if mcp_servers are specified and sessions are initialized
        if agent.mcp_servers and self.mcp_initialized:
            self._load_tools_for_agent(agent)

        # Handle environment variables if specified
        if agent.env_vars:
            self._handle_env_vars(agent)

        return agent

    def initialize_mcp_sessions(self, required_servers: set) -> None:
        """
        Initialize the MCP Client Managers and connect to required MCP servers.

        Args:
            required_servers (set): A set of MCP server names to initialize.

        Raises:
            ValueError: If MCP server configuration is missing.
            RuntimeError: If MCP server fails to initialize or list tools.
        """
        logger.debug("Initializing MCP sessions.")
        logger.debug(f"Required MCP servers to initialize: {required_servers}")

        if not required_servers:
            debug_print(True, "No MCP servers needed by any agent. Skipping MCP Client Managers initialization.")
            logger.info("No MCP servers needed by any agent. Skipping MCP Client Managers initialization.")
            return

        for server_name in required_servers:
            if server_name in self.mcp_clients:
                logger.debug(f"MCP Client for server '{server_name}' already initialized.")
                continue  # Skip if already initialized

            server_config = self.config.get("mcpServers", {}).get(server_name)
            if not server_config:
                error_msg = f"MCP server configuration for '{server_name}' not found."
                debug_print(True, error_msg)
                logger.error(error_msg)
                raise ValueError(error_msg)

            command = server_config.get("command", "npx")
            args = server_config.get("args", [])
            env = server_config.get("env", {})

            mcp_client = MCPClientManager(command=command, args=args, env=env, timeout=30)
            self.mcp_clients[server_name] = mcp_client
            logger.debug(f"MCP ClientManager for server '{server_name}' initialized.")

            # Initialize the MCP server and list tools
            try:
                tools = asyncio.run(mcp_client.discover_tools())
                if tools:
                    logger.info(f"MCP server '{server_name}' initialized and {len(tools)} tools discovered successfully.")
                else:
                    logger.warning(f"MCP server '{server_name}' initialized but no tools were discovered.")
            except Exception as e:
                error_msg = f"Failed to initialize MCP server '{server_name}': {e}"
                debug_print(True, error_msg)
                logger.error(error_msg)
                raise

        self.mcp_initialized = True
        logger.debug("All MCP sessions initialized successfully.")

    def _load_tools_for_agent(self, agent: Agent):
        """
        Attach discovered tools to the agent.

        Args:
            agent (Agent): The agent to which tools will be attached.
        """
        debug_print(True, f"Swarm: Loading tools for agent '{agent.name}'.")
        logger.debug(f"Swarm: Loading tools for agent '{agent.name}'.")

        for server_name in agent.mcp_servers:
            mcp_client = self.mcp_clients.get(server_name)
            if not mcp_client:
                debug_print(True, f"No MCP client available for server '{server_name}'. Skipping tool loading.")
                logger.warning(f"No MCP client available for server '{server_name}'. Skipping tool loading.")
                continue

            try:
                tools = asyncio.run(mcp_client.discover_tools())
                debug_print(True, f"Discovered {len(tools)} tools from '{server_name}' for agent '{agent.name}'.")
                logger.info(f"Discovered {len(tools)} tools from '{server_name}' for agent '{agent.name}'.")

                for tool in tools:
                    # Attach the tool's callable to the agent's functions
                    agent.functions.append(tool.func)
                    logger.debug(f"Attached tool '{tool.name}' from '{server_name}' to agent '{agent.name}'.")
            except Exception as e:
                debug_print(True, f"Failed to load tools from '{server_name}': {e}")
                logger.error(f"Failed to load tools from '{server_name}': {e}")

    def _wrap_mcp_tool(self, server_name: str, tool_name: str, desc: str) -> Callable:
        """
        Deprecated. Use MCPClientManager's discover_tools method to obtain Tool instances.
        """
        # This method can be removed if not used elsewhere.
        pass

    def _handle_env_vars(self, agent: Agent):
        """
        Ensure that all required environment variables are set for the agent.

        Args:
            agent (Agent): The agent for which to handle environment variables.

        Raises:
            EnvironmentError: If any required environment variable is missing.
        """
        missing_vars = [var for var in agent.env_vars.keys() if not os.getenv(var)]
        if missing_vars:
            error_msg = f"Agent '{agent.name}' is missing environment variables: {', '.join(missing_vars)}"
            debug_print(True, error_msg)
            logger.error(error_msg)
            raise EnvironmentError(error_msg)
        debug_print(True, f"Swarm: All required environment variables for agent '{agent.name}' are set.")
        logger.info(f"Swarm: All required environment variables for agent '{agent.name}' are set.")

    def get_chat_completion(
        self,
        agent: Agent,
        history: List,
        context_variables: dict,
        model_override: Optional[str],
        stream: bool,
        debug: bool,
    ) -> Any:
        """
        Get chat completion from the LLM provider.

        Args:
            agent (Agent): The active agent.
            history (List): Conversation history.
            context_variables (dict): Context variables for the conversation.
            model_override (Optional[str]): Model override if any.
            stream (bool): Whether to stream the response.
            debug (bool): Debug flag for verbose output.

        Returns:
            Any: The chat completion response from the LLM provider.
        """
        context_variables = defaultdict(str, context_variables)
        instructions = (
            agent.instructions(context_variables)
            if callable(agent.instructions)
            else agent.instructions
        )
        messages = [{"role": "system", "content": instructions}] + history
        debug_print(debug, "Getting chat completion for...", messages)
        logger.debug(f"Getting chat completion for {agent.name}: {messages}")

        # Convert agent.functions to 'tools' for LLM provider
        tools = [function_to_json(f) for f in agent.functions]
        logger.debug(f"Converted agent functions to tools: {tools}")

        # Remove context_variables from tool schema
        for tool in tools:
            function_def = tool.get("function", {})
            tool_name = function_def.get("name", "unknown")
            params = function_def.get("parameters", {})
            if __CTX_VARS_NAME__ in params:
                params.pop(__CTX_VARS_NAME__, None)
                logger.debug(f"Removed '{__CTX_VARS_NAME__}' from tool parameters for tool '{tool_name}'")
            if "required" in params and __CTX_VARS_NAME__ in params["required"]:
                params["required"].remove(__CTX_VARS_NAME__)
                logger.debug(f"Removed '{__CTX_VARS_NAME__}' from required parameters for tool '{tool_name}'")

        create_params = {
            "model": model_override or agent.model,
            "messages": messages,
            "tools": tools or None,
            "tool_choice": agent.tool_choice,
            "stream": stream,
        }

        if tools:
            create_params["parallel_tool_calls"] = agent.parallel_tool_calls

        logger.debug(f"Chat completion parameters: {create_params}")
        return self.client.chat.completions.create(**create_params)

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
        logger.debug(f"Handling function result: {result}")
        match result:
            case Result() as result_obj:
                logger.debug(f"Result object returned: {result_obj}")
                return result_obj
            case Agent() as agent_obj:
                logger.debug(f"Agent object returned: {agent_obj}")
                return Result(
                    value=json.dumps({"assistant": agent_obj.name}),
                    agent=agent_obj,
                )
            case _:
                try:
                    return Result(value=str(result))
                except Exception as e:
                    error_message = f"Failed to cast response to string: {result}. " \
                                   f"Make sure agent functions return a string or Result object. Error: {str(e)}"
                    debug_print(debug, error_message)
                    logger.error(error_message)
                    raise TypeError(error_message)

    def handle_tool_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[AgentFunction],
        context_variables: dict,
        debug: bool,
    ) -> Response:
        """
        Execute tool calls and collect responses.

        Args:
            tool_calls (List[ChatCompletionMessageToolCall]): List of tool calls to execute.
            functions (List[AgentFunction]): List of agent functions.
            context_variables (dict): Current context variables.
            debug (bool): Debug flag for verbose output.

        Returns:
            Response: The aggregated response from all tool calls.
        """
        function_map = {f.__name__: f for f in functions}
        partial_response = Response(messages=[], agent=None, context_variables={})

        logger.debug(f"Function map: {list(function_map.keys())}")
        logger.debug(f"Tool calls received: {[tc.function.name for tc in tool_calls]}")

        for tool_call in tool_calls:
            name = tool_call.function.name
            logger.debug(f"Processing tool call: {name}")
            if name not in function_map:
                debug_print(debug, f"Tool '{name}' not found in function map.")
                logger.warning(f"Tool '{name}' not found in function map.")
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": f"Error: Tool '{name}' not found.",
                    }
                )
                continue

            try:
                args = json.loads(tool_call.function.arguments)
                logger.debug(f"Tool '{name}' arguments: {args}")
            except json.JSONDecodeError as e:
                error_msg = f"Invalid arguments for tool '{name}': {tool_call.function.arguments}"
                debug_print(debug, error_msg)
                logger.error(error_msg)
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": error_msg,
                    }
                )
                continue

            debug_print(debug, f"Processing tool call: {name} with arguments {args}")
            logger.debug(f"Executing tool '{name}' with arguments: {args}")

            func = function_map[name]
            # Pass context_variables to agent functions if they expect it
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = context_variables
                logger.debug(f"Added context_variables to arguments for tool '{name}': {context_variables}")

            try:
                raw_result = func(**args)
                logger.debug(f"Raw result from tool '{name}': {raw_result}")
            except Exception as e:
                error_msg = f"Error executing tool '{name}': {e}"
                debug_print(debug, error_msg)
                logger.error(error_msg)
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": error_msg,
                    }
                )
                continue

            result: Result = self.handle_function_result(raw_result, debug)
            logger.debug(f"Processed result from tool '{name}': {result}")

            partial_response.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "tool_name": name,
                    "content": result.value,
                }
            )
            partial_response.context_variables.update(result.context_variables)
            if result.agent:
                partial_response.agent = result.agent
                logger.debug(f"Switched to agent: {result.agent.name}")

        logger.debug(f"Partial response after handling tool calls: {partial_response}")
        return partial_response

    def run_and_stream(
        self,
        agent: Agent,
        messages: List,
        context_variables: dict = {},
        model_override: Optional[str] = None,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ):
        """
        Run the conversation with streaming responses.
        Yields chunks of responses as they are received.

        Args:
            agent (Agent): The agent to run.
            messages (List): Initial messages in the conversation.
            context_variables (dict, optional): Context variables for the conversation.
            model_override (Optional[str], optional): Model override if any.
            debug (bool, optional): Debug flag for verbose output.
            max_turns (int, optional): Maximum number of turns to execute.
            execute_tools (bool, optional): Whether to execute tools.

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
                "sender": active_agent.name,
                "role": "assistant",
                "function_call": None,
                "tool_calls": [],
            }

            # Get completion with current history and agent
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
                    delta = json.loads(chunk.choices[0].delta.json())
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode chunk: {e}")
                    continue

                if delta.get("role") == "assistant":
                    delta["sender"] = active_agent.name
                yield delta
                delta.pop("role", None)
                delta.pop("sender", None)
                merge_chunk(message, delta)
            yield {"delim": "end"}

            # Convert tool_calls to a list if not already
            message["tool_calls"] = list(message.get("tool_calls", {}))
            debug_print(debug, "Received completion:", message)
            logger.debug(f"Received completion: {message}")
            history.append(message)

            if not message["tool_calls"] or not execute_tools:
                debug_print(debug, "Ending turn.")
                logger.debug("Ending turn.")
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
        messages: List,
        context_variables: dict = {},
        model_override: Optional[str] = None,
        stream: bool = False,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ) -> Union[Response, Any]:
        """
        The main run loop. If streaming is enabled, it returns a generator.
        Otherwise, it returns a full Response.

        Args:
            agent (Agent): The agent to run.
            messages (List): Initial messages in the conversation.
            context_variables (dict, optional): Context variables for the conversation.
            model_override (Optional[str], optional): Model override if any.
            stream (bool, optional): Whether to stream the response.
            debug (bool, optional): Debug flag for verbose output.
            max_turns (int, optional): Maximum number of turns to execute.
            execute_tools (bool, optional): Whether to execute tools.

        Returns:
            Union[Response, Any]: The conversation response or a generator if streaming.
        """
        # Extend the agent with dynamic tools and handle env_vars
        self.create_agent(agent)

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
            # Get completion with current history and agent
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
                logger.debug(f"Received message from OpenAI: {message}")
            except IndexError:
                logger.error("No choices returned in chat completion.")
                break

            debug_print(debug, "Received completion:", message)
            logger.debug(f"Received completion: {message}")
            message.sender = active_agent.name
            try:
                history.append(
                    json.loads(message.model_dump_json())
                )  # to avoid OpenAI types (?)
                logger.debug(f"Appended message to history: {message}")
            except AttributeError as e:
                logger.error(f"Failed to append message to history: {e}")
                history.append({"role": message.role, "content": message.content, "sender": message.sender})

            if not message.tool_calls or not execute_tools:
                debug_print(debug, "Ending turn.")
                logger.debug("Ending turn.")
                break

            # Handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                message.tool_calls, active_agent.functions, context_variables, debug
            )
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                logger.debug(f"Switched agent to: {partial_response.agent.name}")
                active_agent = partial_response.agent

        return Response(
            messages=history[init_len:],
            agent=active_agent,
            context_variables=context_variables,
        )
