
import logging
import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

from swarm import Swarm  # Ensure correct import path
from swarm.types import Agent, AgentFunctionDefinition  # Updated import

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Prevent adding multiple handlers if they already exist
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class BlueprintBase(ABC):
    """
    Base class for all blueprint implementations. It handles:
      - Environment variable loading (via dotenv)
      - Configuration loading
      - API key validation
      - Swarm initialization
      - Agent creation with dynamic tool discovery (based on agent -> MCP server mapping)
      - Interactive mode with multiple agents
    """

    def __init__(self, config_path: Optional[str] = None, **kwargs):
        """
        Initialize the BlueprintBase with a configuration file path and optional overrides.

        Args:
            config_path (Optional[str]): Path to config file or directory.
                                         Defaults to 'swarm_config.json' in the current working directory.
            **kwargs: Additional params for future extensibility.
        """
        logger.debug(f"Initializing BlueprintBase with config_path='{config_path}', kwargs={kwargs}")

        # Validate metadata
        if not hasattr(self, 'metadata') or not isinstance(self.metadata, dict):
            raise AssertionError("Blueprint metadata must be defined and must be a dictionary.")

        # Load environment variables from .env
        from dotenv import load_dotenv
        load_dotenv()
        logger.debug("Environment variables loaded from .env.")

        # Initialize Swarm
        self.swarm = Swarm(config_path=config_path)
        logger.info("Swarm instance created.")

        # Create Agents
        self.create_agents()

    # --------------------------
    # Abstract / Overridable
    # --------------------------

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Must be overridden by child classes to provide essential blueprint metadata.
        Example:
            {
                "title": "Some Title",
                "description": "Some description",
                "required_mcp_servers": ["sqlite", "brave-search"],
                "env_vars": ["SQLITE_DB_PATH", "BRAVE_API_KEY"],
            }
        """
        pass

    @abstractmethod
    def create_agents(self) -> None:
        """
        Must be overridden by child classes to define and create agents.
        """
        pass

    # --------------------------
    # REPL Helper Functions
    # --------------------------

    def process_and_print_streaming_response(self, response):
        """
        Processes and prints streaming responses.

        Args:
            response: An asynchronous generator yielding response chunks.
        """
        content = ""
        last_sender = ""

        async def process():
            nonlocal content, last_sender
            async for chunk in response:
                if "sender" in chunk:
                    last_sender = chunk["sender"]

                if "content" in chunk and chunk["content"] is not None:
                    if not content and last_sender:
                        print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                        last_sender = ""
                    print(chunk["content"], end="", flush=True)
                    content += chunk["content"]

                if "tool_calls" in chunk and chunk["tool_calls"] is not None:
                    for tool_call in chunk["tool_calls"]:
                        f = tool_call["function"]
                        name = f.get("name")
                        if not name:
                            continue
                        print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()", flush=True)

                if "delim" in chunk and chunk["delim"] == "end" and content:
                    print()  # End of response message
                    content = ""

                if "response" in chunk:
                    return chunk["response"]

        asyncio.run(process())

    def pretty_print_messages(self, messages) -> None:
        """
        Pretty prints non-streaming messages.

        Args:
            messages: List of message dictionaries.
        """
        for message in messages:
            if message["role"] != "assistant":
                continue

            # Print agent name in blue
            sender = message.get("sender", "Assistant")
            print(f"\033[94m{sender}\033[0m:", end=" ")

            # Print response, if any
            if message["content"]:
                print(message["content"])

            # Print tool calls in purple, if any
            tool_calls = message.get("tool_calls") or []
            if len(tool_calls) > 1:
                print()
            for tool_call in tool_calls:
                f = tool_call["function"]
                name, args = f.get("name"), f.get("arguments")
                if not name:
                    continue
                arg_str = json.dumps(json.loads(args)).replace(":", "=")
                print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")

    # --------------------------
    # Interactive Mode (REPL)
    # --------------------------

    async def cleanup_mcp(self) -> None:
        """
        Asynchronously cleans up the MCP sessions once done.
        """
        logger.info("Cleaning up MCP sessions.")
        await self.swarm.cleanup_async()

    async def interactive_mode_async(self, starting_agent: Optional[Agent] = None, stream: bool = False) -> None:
        """
        Asynchronous entry for interactive usage:
         - Run the agents
         - Keep a REPL loop for user interaction
         - Handle agent transfers based on function calls
         - Cleanup MCP sessions upon exit

        Args:
            starting_agent (Optional[Agent]): The agent to start the conversation with.
            stream (bool): Whether to enable streaming mode.
        """
        logger.info("Launching interactive_mode_async.")
        try:
            current_agent = starting_agent or next(iter(getattr(self, 'agents', {}).values()), None)
            if not current_agent:
                logger.error("No agents are defined in the blueprint.")
                return

            logger.info(f"Using initial agent: {current_agent.name}")

            messages = []

            while True:
                user_input = input("\033[90mUser\033[0m: ")
                if user_input.lower() in {"exit", "quit"}:
                    logger.info("Exiting interactive mode.")
                    break

                messages.append({"role": "user", "content": user_input})

                try:
                    response = await self.swarm.run_async(
                        agent=current_agent,
                        messages=messages,
                        context_variables={},  # Add context variables if needed
                        stream=stream,
                        debug=False,
                        max_turns=1,
                        execute_tools=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to run agent '{current_agent.name}': {e}")
                    continue

                # Display the response
                if stream:
                    self.process_and_print_streaming_response(response)
                else:
                    self.pretty_print_messages(response.messages)

                # Handle agent transfers if any
                if response.agent and response.agent != current_agent:
                    logger.info(f"Switching to agent: {response.agent.name}")
                    current_agent = response.agent

                # Update conversation history
                messages.extend(response.messages)

        except KeyboardInterrupt:
            logger.info("Interrupted by user. Exiting interactive mode.")
        except Exception as e:
            logger.error(f"Error in interactive_mode_async: {e}")
        finally:
            await self.cleanup_mcp()

    def interactive_mode(self, starting_agent: Optional[Agent] = None, stream: bool = False) -> None:
        """
        Blocking interactive usage with REPL loop.

        Args:
            starting_agent (Optional[Agent]): The agent to start the conversation with.
            stream (bool): Whether to enable streaming mode.
        """
        logger.info("Starting interactive_mode.")
        try:
            asyncio.run(self.interactive_mode_async(starting_agent, stream))
        except Exception as e:
            logger.error(f"Interactive mode failed: {e}")

    # --------------------------
    # Main
    # --------------------------
    @classmethod
    def main(cls, stream: bool = False):
        """
        For direct usage: python <blueprint>.py

        Args:
            stream (bool): Whether to enable streaming mode.
        """
        logger.info(f"Running blueprint '{cls.__name__}' as script.")
        blueprint = cls()
        blueprint.interactive_mode(stream=stream)
