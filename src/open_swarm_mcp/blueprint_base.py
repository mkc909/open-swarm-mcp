# src/open_swarm_mcp/blueprint_base.py

"""
BlueprintBase Class for Open Swarm MCP.

This module provides a base class for blueprints, handling configuration,
MCP server interactions, and agent initialization.
"""

import logging
from typing import Any, Dict

from open_swarm_mcp.config.config_loader import (
    load_server_config,
    validate_api_keys,
)
from open_swarm_mcp.agent.agent_builder import build_agent_with_mcp_tools
from open_swarm_mcp.utils.mcp_session_manager import MCPSessionManager

logger = logging.getLogger(__name__)


class BlueprintBase:
    def __init__(self, config_path: str):
        """
        Initialize the BlueprintBase with a configuration file path.
        """
        logger.debug("Initializing BlueprintBase.")
        self.config_path = config_path
        self.config = None
        self.mcp_session_manager = None

        self.load_configuration()
        self.validate_api_keys()
        self.initialize_mcp_session_manager()

    def load_configuration(self):
        """
        Load and resolve the configuration from the provided file path.
        """
        logger.debug(f"Attempting to load configuration from '{self.config_path}'.")
        self.config = load_server_config(self.config_path)
        logger.info(f"Successfully loaded configuration from '{self.config_path}'.")
        logger.debug(f"Loaded configuration: {self.config}")

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
