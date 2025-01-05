import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from swarm.core import Swarm
from swarm.repl import run_demo_loop
from swarm.utils.redact import redact_sensitive_data
from dotenv import load_dotenv
import argparse

logger = logging.getLogger(__name__)

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
            **kwargs: Additional parameters for customization.
        """
        logger.debug(f"Initializing BlueprintBase with config: {redact_sensitive_data(config)}")

        if not hasattr(self, 'metadata') or not isinstance(self.metadata, dict):
            raise AssertionError("Blueprint metadata must be defined and must be a dictionary.")

        # Load environment variables
        load_dotenv()
        logger.debug("Environment variables loaded from .env.")

        # Store configuration and initialize Swarm
        self.config = config
        self.swarm = Swarm(config=self.config)
        logger.info("Swarm instance created.")

        # Initialize context variables for active agent tracking
        self.context_variables: Dict[str, Any] = {}

        # Register agents and set starting agent
        self.starting_agent = None
        agents = self.create_agents()
        self.swarm.agents.update(agents)
        logger.info(f"Agents registered: {list(agents.keys())}")

        # Discover tools asynchronously for agents
        asyncio.run(self.async_discover_agent_tools())
        logger.info("Tool discovery completed.")

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
        logger.info("Discovering tools for agents...")
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
        Start the interactive REPL loop.

        Args:
            stream (bool): Enable streaming mode.
        """
        logger.info("Starting interactive mode.")
        if not self.starting_agent:
            logger.error("Starting agent is not set. Ensure `set_starting_agent` is called.")
            raise ValueError("Starting agent is not set.")

        try:
            run_demo_loop(
                starting_agent=self.starting_agent,
                context_variables=self.context_variables,
                stream=stream,
                debug=False,
            )
        except Exception as e:
            logger.error(f"Interactive mode failed: {e}")

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
        parser.add_argument(
            "--stream",
            action="store_true",
            help="Enable streaming mode for responses."
        )
        args = parser.parse_args()

        # Log CLI arguments
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(cls.__name__)
        logger.info(f"Launching blueprint with configuration file: {args.config}")
        logger.info(f"Streaming mode: {'enabled' if args.stream else 'disabled'}")

        # Load configuration and initialize the blueprint
        config = load_server_config(args.config)
        blueprint = cls(config=config)

        # Run based on the streaming mode
        if args.stream:
            blueprint.run(stream=True)
        else:
            blueprint.interactive_mode()
