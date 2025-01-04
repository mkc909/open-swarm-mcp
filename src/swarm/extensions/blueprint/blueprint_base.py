# swarm/extensions/blueprint/blueprint_base.py

import logging
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

from swarm import Swarm  # Ensure correct import path
from swarm.types import Agent  # Removed AgentFunctionDefinition import
from swarm.repl import run_demo_loop  # Import run_demo_loop from repl.py

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
            run_demo_loop(
                starting_agent=starting_agent or next(iter(getattr(self, 'agents', {}).values()), None),
                context_variables={},  # Add context variables if needed
                stream=stream,
                debug=False
            )
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
