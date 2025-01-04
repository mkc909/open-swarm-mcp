# swarm/extensions/blueprint/blueprint_base.py

import asyncio  # Add asyncio for asynchronous operations
import logging
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

from swarm import Swarm  # Ensure correct import path
from swarm.types import Agent
from swarm.repl import run_demo_loop  # Import run_demo_loop from repl.py

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class BlueprintBase(ABC):
    """
    Base class for all blueprint implementations.
    Handles environment variable loading, configuration, agent creation,
    and interactive mode with dynamic tool discovery.
    """

    def __init__(self, config_path: Optional[str] = None, **kwargs):
        """
        Initialize the BlueprintBase with configuration and environment variables.

        Args:
            config_path (Optional[str]): Path to config file or directory.
                                         Defaults to 'swarm_config.json' in the current working directory.
            **kwargs: Additional params for extensibility.
        """
        logger.debug(f"Initializing BlueprintBase with config_path='{config_path}', kwargs={kwargs}")

        if not hasattr(self, 'metadata') or not isinstance(self.metadata, dict):
            raise AssertionError("Blueprint metadata must be defined and must be a dictionary.")

        from dotenv import load_dotenv
        load_dotenv()
        logger.debug("Environment variables loaded from .env.")

        self.swarm = Swarm(config_path=config_path)
        logger.info("Swarm instance created.")

        self.create_agents()

    # --------------------------
    # Abstract / Overridable
    # --------------------------

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Must be overridden to provide metadata like title, description,
        required MCP servers, and environment variables.
        """
        pass

    @abstractmethod
    def create_agents(self) -> None:
        """
        Must be overridden to define and create agents.
        """
        pass

    # --------------------------
    # Agent Tool Discovery
    # --------------------------

    async def async_discover_agent_tools(self, debug: bool = False) -> None:
        """
        Asynchronously discover tools for all agents and merge them into their definitions.

        Args:
            debug (bool): Whether to enable debug logging.
        """
        logger.info("Discovering tools for agents...")
        for agent_name, agent in self.swarm.agents.items():
            logger.debug(f"Discovering tools for agent: {agent_name}")
            try:
                discovered_tools = await self.swarm.discover_and_merge_agent_tools(agent, debug=debug)
                logger.debug(f"Discovered tools for agent '{agent_name}': {discovered_tools}")
            except Exception as e:
                logger.error(f"Failed to discover tools for agent '{agent_name}': {e}")

    # --------------------------
    # Interactive Mode (REPL)
    # --------------------------

    def interactive_mode(self, starting_agent: Optional[Agent] = None, stream: bool = False) -> None:
        """
        Blocking interactive usage with REPL loop using run_demo_loop.

        Args:
            starting_agent (Optional[Agent]): The agent to start the conversation with.
            stream (bool): Whether to enable streaming mode.
        """
        logger.info("Starting interactive_mode.")
        try:
            asyncio.run(self.async_discover_agent_tools())  # Ensure tools are discovered before REPL starts
            run_demo_loop(
                starting_agent=starting_agent or next(iter(self.swarm.agents.values()), None),
                context_variables={},  # Add context variables if needed
                stream=stream,
                debug=False
            )
        except Exception as e:
            logger.error(f"Interactive mode failed: {e}")

    # --------------------------
    # Main Entry Point
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
