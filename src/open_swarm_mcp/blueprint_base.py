# src/open_swarm_mcp/blueprint_base.py

import os
import json
import logging
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import anyio

from open_swarm_mcp.config.config_loader import (
    load_server_config,
    validate_api_keys,
)
from open_swarm_mcp.agent.agent_builder import build_agent_with_mcp_tools
from open_swarm_mcp.utils.logger import setup_logger
from swarm.repl import run_demo_loop
from swarm import Agent

from concurrent.futures import ThreadPoolExecutor

logger = setup_logger(__name__)


# src/open_swarm_mcp/blueprint_base.py

class BlueprintBase(ABC):
    """
    Abstract Base Class for all Blueprints.
    Handles configuration loading, MCP session management, and agent building.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """
        Initialize the blueprint by loading configuration, validating API keys,
        setting up MCP sessions, and building agents.

        Args:
            config (Optional[Dict[str, Any]]): Optional configuration dictionary.
                If not provided, it will be loaded from 'mcp_server_config.json'.
            **kwargs: Additional keyword arguments (e.g., model_override).

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If API key validation fails.
            Exception: If MCP Session Manager or agents fail to initialize.
        """
        logger.debug("Initializing BlueprintBase.")

        # Load configuration
        self.config = config or self.load_config()
        logger.debug(f"Configuration loaded: {self.config}")

        # Handle model_override if provided
        model_override = kwargs.get('model_override')
        if model_override:
            selected_llm = self.config.get('selected_llm', 'default')
            if selected_llm in self.config['llm_providers']:
                original_model = self.config['llm_providers'][selected_llm].get('model')
                self.config['llm_providers'][selected_llm]['model'] = model_override
                logger.debug(
                    f"Model overridden from '{original_model}' to '{model_override}' for LLM provider '{selected_llm}'."
                )
            else:
                error_msg = f"Selected LLM '{selected_llm}' not found in configuration."
                logger.error(error_msg)
                raise ValueError(error_msg)

        # Validate API keys
        validate_api_keys(self.config)
        logger.debug("API keys validated successfully.")

        # Initialize MCP Session Manager
        self.mcp_session_manager = self.initialize_mcp_session_manager()
        logger.debug("MCP Session Manager initialized.")

        # Build agents using the core framework
        self.agents = self.build_agents()
        logger.debug(f"Agents built: {list(self.agents.keys())}")

        # Initialize ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=10)  # Adjust as needed
        logger.debug("ThreadPoolExecutor initialized.")

        logger.debug("BlueprintBase initialization complete.")

    def load_config(self) -> Dict[str, Any]:
        """
        Load the MCP server and LLM configurations from 'mcp_server_config.json'.

        Returns:
            Dict[str, Any]: Parsed configuration dictionary.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            json.JSONDecodeError: If the configuration file contains invalid JSON.
            Exception: For any other unexpected errors during loading.
        """
        config_file = 'mcp_server_config.json'
        logger.debug(f"Attempting to load configuration from '{config_file}'.")

        try:
            config = load_server_config(config_file)
            logger.info(f"Successfully loaded configuration from '{config_file}'.")
            logger.debug(f"Loaded configuration: {json.dumps(config, indent=4)}")
            return config
        except FileNotFoundError as e:
            logger.error(f"Configuration file '{config_file}' not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file '{config_file}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            raise

    def initialize_mcp_session_manager(self) -> Any:
        """
        Initialize the MCP Session Manager using the loaded configuration.

        Returns:
            Any: An instance of MCP Session Manager.

        Raises:
            Exception: If MCP Session Manager fails to initialize.
        """
        logger.debug("Initializing MCP Session Manager.")
        try:
            from open_swarm_mcp.utils.mcp_session_manager import MCPSessionManager
            mcp_session_manager = MCPSessionManager(self.config)
            logger.info("MCP Session Manager initialized successfully.")
            return mcp_session_manager
        except Exception as e:
            logger.error(f"Failed to initialize MCP Session Manager: {e}")
            raise

    def build_agents(self) -> Dict[str, Agent]:
        """
        Build agents using the core framework's agent builder.

        Returns:
            Dict[str, Agent]: Dictionary of built agents.

        Raises:
            Exception: If agent building fails.
        """
        logger.debug("Building agents using the core framework.")
        try:
            agents = build_agent_with_mcp_tools(self.config)
            if not agents:
                logger.warning("No agents were built. Ensure agent configurations are correct.")
            else:
                logger.info(f"Successfully built agents: {list(agents.keys())}")
            return agents
        except Exception as e:
            logger.error(f"Failed to build agents: {e}")
            raise

    @abstractmethod
    def validate_env_vars(self) -> None:
        """
        Validate that required environment variables are set and any necessary conditions are met.

        Raises:
            ValueError: If any required environment variable is missing or invalid.
        """
        pass

    @abstractmethod
    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint's main functionality.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.

        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        pass

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata about the blueprint.

        Returns:
            Dict[str, Any]: Metadata dictionary containing title, description, etc.

        Raises:
            NotImplementedError: If the property is not implemented by the subclass.
        """
        pass

    @abstractmethod
    def get_agents(self) -> Dict[str, Agent]:
        """
        Return the dictionary of agents used by this blueprint.

        Returns:
            Dict[str, Agent]: Dictionary of agents.

        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        pass

    def get_starting_agent(self) -> Agent:
        """
        Select a starting agent from the available agents.

        Returns:
            Agent: The selected starting agent.

        Raises:
            ValueError: If no agents are defined in the blueprint.
        """
        agent_map = self.get_agents()
        if not agent_map:
            error_msg = "No agents defined in this blueprint."
            logger.error(error_msg)
            raise ValueError(error_msg)

        starting_agent = random.choice(list(agent_map.values()))
        logger.debug(f"Selected starting agent: {starting_agent.name}")
        return starting_agent

    async def interactive_mode_async(self) -> None:
        """
        Asynchronous interactive mode that uses the starting agent.
        Handles proper shutdown to prevent runtime errors.
        """
        logger.info("Starting asynchronous interactive mode.")
        try:
            starting_agent = self.get_starting_agent()
            logger.info(f"Starting agent: {starting_agent.name}")
            await run_demo_loop(starting_agent=starting_agent)
        except Exception as e:
            logger.error(f"Error during interactive mode: {e}")
            raise
        finally:
            await self.shutdown()

    def interactive_mode(self) -> None:
        """
        Synchronous wrapper for the asynchronous interactive_mode_async.
        Uses anyio to manage the asynchronous context.
        """
        logger.debug("Entering synchronous interactive mode wrapper.")
        try:
            anyio.run(self.interactive_mode_async)
            logger.debug("Interactive mode completed successfully.")
        except Exception as e:
            logger.error(f"Interactive mode failed: {e}")
            raise

    async def shutdown(self) -> None:
        """
        Perform any necessary cleanup during shutdown.
        Ensures that asynchronous tasks and executors are properly terminated.
        """
        logger.info("Shutting down BlueprintBase and performing cleanup.")
        if hasattr(self, 'executor') and self.executor:
            logger.debug("Shutting down ThreadPoolExecutor.")
            self.executor.shutdown(wait=True)
            logger.info("ThreadPoolExecutor shut down successfully.")
        # Add additional cleanup logic here if necessary
        logger.info("Cleanup completed successfully.")

    def validate_metadata(self) -> None:
        """
        Validate that the metadata property meets the required structure.

        Raises:
            ValueError: If metadata is invalid or missing required fields.
        """
        required_fields = ["title", "description"]
        for field in required_fields:
            if field not in self.metadata:
                error_msg = f"Missing required metadata field: {field}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        logger.debug("Metadata validation passed.")

    def summarize_agents(self) -> Dict[str, str]:
        """
        Provide a summary of all agents defined in the blueprint.

        Returns:
            Dict[str, str]: A dictionary mapping agent names to their instructions.
        """
        summary = {name: agent.instructions for name, agent in self.get_agents().items()}
        logger.debug(f"Agent summaries: {summary}")
        return summary
