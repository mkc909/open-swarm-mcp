# src/open_swarm_mcp/blueprint_base.py

"""
BlueprintBase Class for Open Swarm MCP.

This module provides a base class for blueprints, handling configuration,
MCP server interactions, and agent initialization. The BlueprintBase is designed
to be extended by specific blueprint implementations.
"""

import logging
from typing import Any, Dict, Optional
from pathlib import Path

from open_swarm_mcp.config.config_loader import (
    load_server_config,
    validate_api_keys,
)
from open_swarm_mcp.agent.agent_builder import build_agent_with_mcp_tools
from open_swarm_mcp.utils.mcp_session_manager import MCPSessionManager
from swarm.utils.redact import redact_sensitive_values

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set DEBUG level for detailed output


class BlueprintBase:
    """
    Base class for all blueprint implementations. Provides common functionality such as
    configuration loading, MCP session management, and agent building.
    """

    def __init__(self, config_path: Optional[str] = None, **kwargs):
        """
        Initialize the BlueprintBase with a configuration file path and optional overrides.

        Args:
            config_path (Optional[str]): Path to the configuration file or directory. Defaults to
                                         'mcp_server_config.json' in the current working directory.
            **kwargs: Additional keyword arguments for future extensibility.
        """
        logger.debug(f"Initializing BlueprintBase with config_path='{config_path}' and kwargs={kwargs}.")

        # Guard: Ensure no unexpected arguments remain
        if kwargs:
            logger.warning(f"Unused keyword arguments in BlueprintBase initialization: {kwargs}")

        self.config_path = config_path or self._get_default_config_path()
        self.config = {}
        self.mcp_session_manager = None

        # Initialization sequence
        self.load_configuration()
        self.validate_api_keys()

        # Conditional initialization of MCP Session Manager
        if self.requires_mcp_servers():
            self.initialize_mcp_session_manager()
        else:
            logger.info("No MCP servers required. Skipping MCP Session Manager initialization.")

    def _get_default_config_path(self) -> str:
        """
        Get the default configuration file path.

        Returns:
            str: Path to the default configuration file.
        """
        default_config_file = "mcp_server_config.json"
        default_config_path = Path.cwd() / default_config_file
        logger.debug(f"Using default configuration file: {default_config_path}")
        return str(default_config_path)

    def load_configuration(self):
        """
        Load and resolve the configuration from the provided file path or directory.

        If the configuration path is a directory, it attempts to load 'config.json' within it.
        """
        logger.debug(f"Attempting to load configuration from '{self.config_path}'.")
        config_path = Path(self.config_path)

        if config_path.is_dir():
            # Guard: Check for the expected 'config.json' in directory
            config_file = config_path / "config.json"
            if config_file.exists():
                logger.info(f"Found 'config.json' in directory '{self.config_path}'. Loading configuration.")
                self.config = load_server_config(str(config_file))
            else:
                logger.warning(f"No 'config.json' found in directory '{self.config_path}'. Using empty configuration.")
                self.config = {}
        else:
            try:
                self.config = load_server_config(self.config_path)
                redacted_config = redact_sensitive_values(self.config)
                logger.info(f"Successfully loaded configuration from '{self.config_path}'.")
                logger.debug(f"Loaded configuration (redacted): {redacted_config}")
            except FileNotFoundError:
                logger.error(f"Configuration file '{self.config_path}' not found. Using empty configuration.")
                self.config = {}

    def validate_api_keys(self):
        """
        Validate the API keys for the selected LLM provider.

        Raises:
            ValueError: If validation fails due to missing or invalid API keys.
        """
        selected_llm = self.config.get("selectedLLM", "default")
        logger.info(f"Validating API keys for LLM profile '{selected_llm}'.")

        try:
            validate_api_keys(self.config, selected_llm)
            logger.info(f"API keys validated successfully for profile '{selected_llm}'.")
        except ValueError as e:
            logger.critical(f"API key validation failed: {e}")
            raise

    def requires_mcp_servers(self) -> bool:
        """
        Check if the blueprint requires MCP servers.

        Returns:
            bool: True if MCP servers are required, False otherwise.
        """
        metadata = self.metadata if hasattr(self, "metadata") else {}
        required_servers = metadata.get("required_mcp_servers", [])
        logger.debug(f"Metadata 'required_mcp_servers': {required_servers}")
        return bool(required_servers)

    def initialize_mcp_session_manager(self):
        """
        Initialize the MCP Session Manager with the loaded configuration.

        The MCP Session Manager manages connections to MCP servers required by the blueprint.
        """
        logger.debug("Initializing MCP Session Manager.")
        try:
            self.mcp_session_manager = MCPSessionManager(self.config)
            logger.info("MCP Session Manager initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize MCP Session Manager: {e}")
            raise

    def build_agents(self):
        """
        Build agents using MCP tools.

        Returns:
            Agent: The constructed Agent instance.

        Raises:
            Exception: If agent building fails.
        """
        logger.debug("Building agents using the core framework.")
        try:
            agent = build_agent_with_mcp_tools(self.config)
            if not agent:
                logger.warning("No agents were built. Ensure agent configurations are correct.")
            else:
                logger.info(f"Successfully built Agent '{agent.name}' with {len(agent.functions)} tools.")
            return agent
        except Exception as e:
            logger.error(f"Failed to build agents: {e}")
            raise
