import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from swarm.extensions.config.config_loader import load_server_config
from swarm.repl import run_demo_loop
from dotenv import load_dotenv
import argparse

logger = logging.getLogger(__name__)


class BlueprintBase(ABC):
    """
    Abstract base class for all Swarm blueprints.
    Subclasses must implement metadata and create_agents methods.
    """

    def __init__(self, config: dict, **kwargs):
        """
        Initialize the blueprint.

        Args:
            config (dict): The preloaded configuration dictionary.
            **kwargs: Additional keyword arguments for customization.
        """
        logger.debug(f"Initializing {self.__class__.__name__} with config={config}, kwargs={kwargs}")

        # Ensure metadata is defined in subclasses
        if not hasattr(self, 'metadata') or not isinstance(self.metadata, dict):
            raise AssertionError("Blueprint metadata must be defined and must be a dictionary.")

        # Set up environment variables
        from dotenv import load_dotenv
        load_dotenv()
        logger.debug("Environment variables loaded from .env.")

        # Store the configuration
        self.config = config

        # Initialize Swarm
        from swarm.core import Swarm
        self.swarm = Swarm(config=self.config)
        logger.info("Swarm instance created.")

        # Register agents and discover tools
        self.starting_agent = None
        agents = self.create_agents()
        self.swarm.agents.update(agents)
        logger.info(f"Agents registered: {list(agents.keys())}")

        asyncio.run(self.async_discover_agent_tools())
        logger.info("Tool discovery completed.")

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the blueprint.
        This must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def create_agents(self) -> Dict[str, Any]:
        """
        Create and return agents for the blueprint.
        This must be implemented by subclasses.
        """
        raise NotImplementedError

    async def async_discover_agent_tools(self) -> None:
        """
        Discover tools for all agents asynchronously.
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

    def interactive_mode(self, stream: bool = False) -> None:
        """
        Blocking interactive usage with REPL loop using run_demo_loop.

        Args:
            stream (bool): Whether to enable streaming mode.
        """
        logger.info("Starting interactive_mode.")
        if not self.starting_agent:
            logger.error("Starting agent is not set. Ensure `set_starting_agent` is called.")
            raise ValueError("Starting agent is not set.")
        try:
            run_demo_loop(
                starting_agent=self.starting_agent,
                context_variables={},  # Add context variables if needed
                stream=stream,
                debug=False,
            )
        except Exception as e:
            logger.error(f"Interactive mode failed: {e}")


    @classmethod
    def main(cls):
        """
        The main entry point for running a blueprint in CLI mode.
        """
        # Parse CLI arguments
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

        # Log the configuration file path and streaming mode
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(cls.__name__)
        logger.info(f"Launching blueprint with configuration file: {args.config}")
        logger.info(f"Streaming mode: {'enabled' if args.stream else 'disabled'}")

        # Load the configuration
        from swarm.extensions.config.config_loader import load_server_config
        config = load_server_config(args.config)

        # Pass arguments as kwargs
        kwargs = vars(args)  # Convert Namespace to a dictionary
        kwargs.pop("config")  # Remove 'config', as it's already loaded
        blueprint = cls(config=config, **kwargs)

        # Run the blueprint
        if args.stream:
            blueprint.run(stream=True)
        else:
            blueprint.interactive_mode()
