import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from swarm import Swarm  # Ensure correct import path
from swarm.types import Agent

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
        if not self.metadata or not isinstance(self.metadata, dict):
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
    # Interactive Mode
    # --------------------------

    async def cleanup_mcp(self) -> None:
        """
        Clean up the MCP sessions once done.
        """
        await self.swarm.cleanup()

    async def interactive_mode_async(self, initial_messages: Optional[List[Dict[str, str]]] = None) -> None:
        """
        Asynchronous entry for interactive usage:
         - Run the agents
         - Possibly keep a loop or do further instructions
         - Cleanup
        """
        logger.info("Launching interactive_mode_async.")
        try:
            initial_messages = initial_messages or []
            # Assuming there's a designated primary agent
            primary_agent = self.swarm.agents.get("PrimaryAgent")
            if not primary_agent:
                logger.error("No 'PrimaryAgent' defined in agents.")
                return
            response = self.swarm.run(
                agent=primary_agent,
                messages=initial_messages,
            )
            logger.info("Run completed. Final response:")
            logger.info(response.messages[-1]["content"])
        except Exception as e:
            logger.error(f"Error in interactive_mode_async: {e}")
        finally:
            await self.cleanup_mcp()

    def get_agents(self) -> Dict[str, Agent]:
        """
        Return the agents managed by this blueprint's Swarm instance.
        """
        if not self.swarm:
            raise RuntimeError("Swarm instance is not initialized.")
        return self.swarm.agents

    def interactive_mode(self, initial_messages: Optional[List[Dict[str, str]]] = None) -> None:
        """
        Blocking interactive usage.
        """
        logger.info("Starting interactive_mode.")
        try:
            import asyncio
            asyncio.run(self.interactive_mode_async(initial_messages))
        except Exception as e:
            logger.error(f"Interactive mode failed: {e}")

    # --------------------------
    # Main
    # --------------------------
    @classmethod
    def main(cls):
        """
        For direct usage: python <blueprint>.py
        """
        logger.info(f"Running blueprint '{cls.__name__}' as script.")
        blueprint = cls()
        blueprint.interactive_mode()
