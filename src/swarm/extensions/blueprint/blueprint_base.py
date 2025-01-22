import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from swarm.core import Swarm
from swarm.extensions.config.config_loader import load_server_config
from swarm.repl import run_demo_loop
from swarm.settings import DEBUG
from swarm.utils.redact import redact_sensitive_data
from dotenv import load_dotenv
import argparse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

class BlueprintBase(ABC):
    """
    Abstract base class for Swarm blueprints.
    Manages agents, tools, and active context for executing tasks.
    """

    def __init__(self, config: dict, **kwargs):
        """
        Initialize the blueprint and register agents.

        Args:
            config (dict): Configuration dictionary.
            **kwargs: Additional parameters for customization (e.g., existing swarm_instance).
        """
        logger.debug(f"Initializing BlueprintBase with config: {redact_sensitive_data(config)}")

        if not hasattr(self, 'metadata') or not isinstance(self.metadata, dict):
            raise AssertionError("Blueprint metadata must be defined and must be a dictionary.")

        # Load environment variables
        load_dotenv()
        logger.debug("Environment variables loaded from .env.")

        # Store configuration
        self.config = config

        # Check if a shared Swarm instance was passed in; otherwise create new
        self.swarm = kwargs.get('swarm_instance')
        if self.swarm is not None:
            logger.debug("Using shared swarm instance from kwargs.")
        else:
            logger.debug("No shared swarm instance provided; creating a new one.")
            self.swarm = Swarm(config=self.config)

        logger.debug("Swarm instance created.")

        # Initialize context variables for active agent tracking
        self.context_variables: Dict[str, Any] = {}

        # Register agents and set starting agent
        self.starting_agent = None
        agents = self.create_agents()
        self.swarm.agents.update(agents)
        logger.debug(f"Agents registered: {list(agents.keys())}")
        # Validate required environment variables based on blueprint metadata
        required_env_vars = set(self.metadata.get('env_vars', []))
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.debug("Required environment variables validation successful.")

        # Discover tools asynchronously for agents
        asyncio.run(self.async_discover_agent_tools())
        logger.debug("Tool discovery completed.")

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the blueprint, including title, description, and dependencies.
        Subclasses must implement this.
        """
        raise NotImplementedError

    @abstractmethod
    def create_agents(self) -> Dict[str, Any]:
        """
        Create and return the agents for this blueprint.
        Subclasses must implement this.
        """
        raise NotImplementedError

    async def async_discover_agent_tools(self) -> None:
        """
        Discover and register tools for each agent asynchronously.
        """
        logger.debug("Discovering tools for agents...")
        for agent_name, agent in self.swarm.agents.items():
            logger.debug(f"Discovering tools for agent: {agent_name}")
            try:
                tools = await self.swarm.discover_and_merge_agent_tools(agent)
                logger.debug(f"Discovered tools for agent '{agent_name}': {tools}")
            except Exception as e:
                logger.error(f"Failed to discover tools for agent '{agent_name}': {e}")

    def set_starting_agent(self, agent: Any) -> None:
        """
        Set the starting agent for the blueprint.

        Args:
            agent (Any): The agent to set as the starting agent.
        """
        logger.debug(f"Setting starting agent to: {agent.name}")
        self.starting_agent = agent
        self.context_variables["active_agent_name"] = agent.name

    def determine_active_agent(self) -> Any:
        """
        Determine the active agent based on `context_variables`.

        Returns:
            Any: The active agent instance.
        """
        active_agent_name = self.context_variables.get("active_agent_name")
        if active_agent_name and active_agent_name in self.swarm.agents:
            logger.debug(f"Active agent determined: {active_agent_name}")
            return self.swarm.agents[active_agent_name]

        logger.debug("Falling back to the starting agent as the active agent.")
        return self.starting_agent

    def run_with_context(self, messages: list, context_variables: dict) -> dict:
        """
        Execute a task with the given messages and context variables.

        Args:
            messages (list): Conversation history.
            context_variables (dict): Variables to maintain conversation context.

        Returns:
            dict: Response and updated context variables.
        """
        # Update internal context variables
        self.context_variables.update(context_variables)
        logger.debug(f"Context variables before execution: {self.context_variables}")

        # Determine the active agent
        active_agent = self.determine_active_agent()
        logger.debug(f"Running with active agent: {active_agent.name}")

        # Execute the Swarm task
        response = self.swarm.run(
            agent=active_agent,
            messages=messages,
            context_variables=self.context_variables,
            stream=False,
            debug=True,
        )

        # Log the response and update context variables
        logger.debug(f"Swarm response: {response}")
        if response.agent:
            self.context_variables["active_agent_name"] = response.agent.name
            logger.debug(f"Active agent updated to: {response.agent.name}")

        return {
            "response": response,
            "context_variables": self.context_variables,
        }

    def set_active_agent(self, agent_name: str) -> None:
        """
        Explicitly set the active agent.

        Args:
            agent_name (str): Name of the agent to set as active.
        """
        if agent_name in self.swarm.agents:
            self.context_variables["active_agent_name"] = agent_name
            logger.debug(f"Active agent set to: {agent_name}")
        else:
            logger.error(f"Agent '{agent_name}' not found. Cannot set as active agent.")

    def interactive_mode(self, stream: bool = False) -> None:
        """
        Start the interactive REPL loop directly using the blueprint's Swarm instance.

        Args:
            stream (bool): Enable streaming mode.
        """
        logger.debug("Starting interactive mode.")
        
        if not self.starting_agent:
            logger.error("Starting agent is not set. Ensure `set_starting_agent` is called.")
            raise ValueError("Starting agent is not set.")

        if not self.swarm:
            logger.error("Swarm instance is not initialized.")
            raise ValueError("Swarm instance is not initialized.")

        try:
            print("Blueprint Interactive Mode 🐝")
            messages = []
            agent = self.starting_agent

            while True:
                # Get user input
                user_input = input("\033[90mUser\033[0m: ")
                if user_input.lower() in {"exit", "quit"}:
                    print("Exiting interactive mode.")
                    break
                
                # Append user input to messages
                messages.append({"role": "user", "content": user_input})

                # Run Swarm instance with the current agent and messages
                response = self.swarm.run(
                    agent=agent,
                    messages=messages,
                    context_variables=self.context_variables or {},
                    stream=stream,
                    debug=False,
                )

                # Process and display the response
                if stream:
                    self._process_and_print_streaming_response(response)
                else:
                    self._pretty_print_response(response.messages)

                # Update messages and agent for the next iteration
                messages.extend(response.messages)
                agent = response.agent

        except Exception as e:
            logger.error(f"Interactive mode failed: {e}")

    def _process_and_print_streaming_response(self, response):
        """
        Process and display the streaming response from Swarm.
        """
        content = ""
        last_sender = ""

        for chunk in response:
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
                    tool_function = tool_call["function"]
                    name = getattr(tool_function, "name", None)
                    if not name:
                        name = tool_function.get("__name__", "Unnamed Tool")
                    print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")

            if "delim" in chunk and chunk["delim"] == "end" and content:
                print()  # End of response message
                content = ""

            if "response" in chunk:
                return chunk["response"]

    def _pretty_print_response(self, messages) -> None:
        """
        Pretty print the messages returned by the Swarm.
        """
        for message in messages:
            if message["role"] != "assistant":
                continue

            # Print agent name in blue
            print(f"\033[94m{message['sender']}\033[0m:", end=" ")

            # Print response, if any
            if message["content"]:
                print(message["content"])

            # Print tool calls in purple, if any
            tool_calls = message.get("tool_calls") or []
            if len(tool_calls) > 1:
                print()
            for tool_call in tool_calls:
                f = tool_call["function"]
                name, args = f["name"], f["arguments"]
                arg_str = json.dumps(json.loads(args)).replace(":", "=")
                print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")


    @classmethod
    def main(cls):
        """
        Main entry point for running a blueprint in CLI mode.
        """
        parser = argparse.ArgumentParser(description=f"Launch the {cls.__name__} blueprint.")
        parser.add_argument(
            "--config",
            type=str,
            default="./swarm_config.json",
            help="Path to the configuration file (default: ./swarm_config.json)"
        )
        args = parser.parse_args()

        # Log CLI arguments
        logger.debug(f"Launching blueprint with configuration file: {args.config}")

        # Load configuration and initialize the blueprint
        config = load_server_config(args.config)
        blueprint = cls(config=config)

        blueprint.interactive_mode()
