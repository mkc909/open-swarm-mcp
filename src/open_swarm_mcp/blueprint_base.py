# src/open_swarm_mcp/blueprint_base.py

"""
BlueprintBase Class for Open Swarm MCP.

This module provides a base class for blueprints, handling configuration,
MCP server interactions, and agent initialization.
"""

import logging
from typing import Any, Dict
from pathlib import Path

from open_swarm_mcp.config.config_loader import (
    load_server_config,
    validate_api_keys,
)
from open_swarm_mcp.agent.agent_builder import build_agent_with_mcp_tools
from open_swarm_mcp.utils.mcp_session_manager import MCPSessionManager

logger = logging.getLogger(__name__)


class BlueprintBase:
    def __init__(self, config_path: str = None):
        """
        Initialize the BlueprintBase with a configuration file path.

        Args:
            config_path (str, optional): Path to the configuration file or directory.
                                         If not provided, defaults to 'mcp_server_config.json' in the current directory.
        """
        logger.debug("Initializing BlueprintBase.")
        self.config_path = config_path or self._get_default_config_path()
        self.config = {}
        self.mcp_session_manager = None

        self.load_configuration()
        self.validate_api_keys()
        self.initialize_mcp_session_manager()

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
        """
        logger.debug(f"Attempting to load configuration from '{self.config_path}'.")
        config_path = Path(self.config_path)
        if config_path.is_dir():
            config_file = config_path / "config.json"
            if config_file.exists():
                self.config = load_server_config(str(config_file))
            else:
                logger.warning(f"Configuration file 'config.json' not found in directory '{self.config_path}'. Using empty configuration.")
                self.config = {}
        else:
            try:
                self.config = load_server_config(self.config_path)
                logger.info(f"Successfully loaded configuration from '{self.config_path}'.")
                logger.debug(f"Loaded configuration: {self.config}")
            except FileNotFoundError:
                logger.warning(f"Configuration file '{self.config_path}' not found. Using empty configuration.")
                self.config = {}

    def validate_api_keys(self):
        """
        Validate the API keys for the selected LLM provider.
        """
        selected_llm = self.config.get("selectedLLM", None)
        logger.info("Validating API keys.")
        validate_api_keys(self.config, selected_llm)
        logger.debug("API keys validated successfully.")

    def initialize_mcp_session_manager(self):
        """
        Initialize the MCP Session Manager with the configuration.
        """
        logger.debug("Initializing MCP Session Manager.")
        self.mcp_session_manager = MCPSessionManager(self.config)
        logger.info("MCP Session Manager initialized successfully.")

    def build_agents(self):
        """
        Build agents using MCP tools.
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
