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
)

__CTX_VARS_NAME__ = "context_variables"

# Function Registry
def echo_function(content: str) -> str:
    """
    Echoes the user input.

    Args:
        content (str): The user's input.

    Returns:
        str: The echoed content.
    """
    return content

# Add more functions as needed
def filesystem_function(operation: str, path: str) -> str:
    """
    Performs filesystem operations.

    Args:
        operation (str): The filesystem operation to perform.
        path (str): The file or directory path.

    Returns:
        str: The result of the operation.
    """
    # Placeholder implementation
    if operation == "read":
        return f"Reading from {path}"
    elif operation == "write":
        return f"Writing to {path}"
    else:
        return f"Unknown operation '{operation}' on {path}"

# Update the FUNCTION_REGISTRY
FUNCTION_REGISTRY = {
    "echo_function": echo_function,
    "filesystem_function": filesystem_function,
    # Add more functions here as needed
}

class Swarm:
    def __init__(self, client=None, config_path: Optional[str] = None):
        """
        Initialize the Swarm with an optional custom OpenAI client.
        If no client is provided, a default OpenAI client is created.
        Optionally load configurations from a JSON file.

        Args:
            client: Custom OpenAI client instance.
            config_path (Optional[str]): Path to the configuration file.
        """
        if not client:
            client = OpenAI()
        self.client = client

        # Initialize default settings
        self.model = "gpt-4o"
        self.temperature = 0.7
        self.tool_choice = "sequential"
        self.parallel_tool_calls = False
        self.agents: Dict[str, Agent] = {}

        # Load configurations if config_path is provided
        self.config = {}
        if config_path:
            self.config = self.load_configuration(config_path)
            debug_print(True, f"Configuration loaded from {config_path}: {self.config}")
            print(f"[INFO] Configuration loaded from {config_path}.")

            # Override client settings based on configuration
            api_key = self.config.get("api_key")
            if api_key:
                self.client.api_key = api_key
                debug_print(True, "API key set from configuration.")
                print("[INFO] API key set from configuration.")

            model = self.config.get("model")
            if model:
                self.model = model
                debug_print(True, f"Model set to {model} from configuration.")
                print(f"[INFO] Model set to {model} from configuration.")

            temperature = self.config.get("temperature", 0.7)
            self.temperature = temperature
            debug_print(True, f"Temperature set to {temperature} from configuration.")
            print(f"[INFO] Temperature set to {temperature} from configuration.")

            tool_choice = self.config.get("tool_choice", "sequential")
            self.tool_choice = tool_choice
            debug_print(True, f"Tool choice set to {tool_choice} from configuration.")
            print(f"[INFO] Tool choice set to {tool_choice} from configuration.")

            self.parallel_tool_calls = self.config.get("parallel_tool_calls", False)
            debug_print(True, f"Parallel tool calls set to {self.parallel_tool_calls} from configuration.")
            print(f"[INFO] Parallel tool calls set to {self.parallel_tool_calls} from configuration.")

            # Note: Removed `register_agents()` since agents are instantiated by blueprints
        else:
            print("[INFO] No configuration file provided. Using default settings.")

    def load_configuration(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from a JSON file.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            Dict[str, Any]: The loaded configuration dictionary.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        if not os.path.exists(config_path):
            error_msg = f"Configuration file '{config_path}' does not exist."
            debug_print(True, error_msg)
            raise FileNotFoundError(error_msg)

        with open(config_path, "r") as f:
            try:
                config = json.load(f)
                # Replace environment variable placeholders
                for key, value in config.items():
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_var = value[2:-1]
                        config[key] = os.getenv(env_var, "")
                return config
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON in configuration file '{config_path}': {e}"
                debug_print(True, error_msg)
                raise json.JSONDecodeError(error_msg, e.doc, e.pos)

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
        context_variables = defaultdict(str, context_variables)
        instructions = (
            agent.instructions(context_variables)
            if callable(agent.instructions)
            else agent.instructions
        )
        messages = [{"role": "system", "content": instructions}] + history
        debug_print(debug, "Getting chat completion for...", messages)

        # Serialize agent functions to 'tools'
        serialized_functions = [function_to_json(f) for f in agent.functions]
        tools = [func_dict for func_dict in serialized_functions]

        # Debug: Inspect serialized tools
        debug_print(debug, "Serialized tools:", tools)
        print(f"[DEBUG] Serialized tools: {json.dumps(tools, indent=2)}")

        # Remove context_variables from the tools' parameters
        for tool in tools:
            params = tool.get("parameters", {})
            properties = params.get("properties", {})
            if __CTX_VARS_NAME__ in properties:
                properties.pop(__CTX_VARS_NAME__)
            required = params.get("required", [])
            if __CTX_VARS_NAME__ in required:
                required.remove(__CTX_VARS_NAME__)

        # Construct payload with 'tools' instead of 'functions'
        create_params = {
            "model": model_override or agent.model,
            "messages": messages,
            "tools": tools or None,
            "tool_choice": agent.tool_choice,
            "stream": stream,
        }

        # Include 'parallel_tool_calls' only if 'tools' are specified
        if tools:
            create_params["parallel_tool_calls"] = agent.parallel_tool_calls

        # Debug: Print the payload being sent to OpenAI
        debug_print(debug, "Chat completion payload:", create_params)
        print(f"[DEBUG] Chat completion payload: {json.dumps(create_params, indent=2)}")

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

        for tool_call in tool_calls:
            name = tool_call.function.name
            # Handle missing tool case, skip to next tool
            if name not in function_map:
                debug_print(debug, f"Tool {name} not found in function map.")
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
            debug_print(
                debug, f"Processing tool call: {name} with arguments {args}")

            func = function_map[name]
            # Pass context_variables to agent functions if required
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = context_variables
            raw_result = func(**args)

            result: Result = self.handle_function_result(raw_result, debug)
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
                "sender": agent.name,  # Include 'sender'
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
            messages=history[init_len:],
            agent=active_agent,
            context_variables=context_variables,
        )
