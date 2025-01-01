# src/open_swarm_mcp/utils/mcp_session_manager.py

"""
MCP Session Manager

Handles the initialization, management, and cleanup of MCP sessions.
Provides a centralized way to interact with MCP servers.
"""

import asyncio
import json
import os
import logging
from typing import Optional, Dict, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture detailed logs

# Prevent adding multiple handlers if they already exist
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class MCPSessionManager:
    """
    Manages the MCP session lifecycle, including connection and cleanup.
    Provides a centralized way to interact with MCP servers.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MCP Session Manager.

        Args:
            config (Dict[str, Any]): The entire configuration dictionary loaded from 'mcp_server_config.json'.
        """
        self.config = config
        self.session: Optional[ClientSession] = None
        self.stdio_transport: Optional[tuple] = None
        logger.debug("MCPSessionManager instance created with provided configuration.")

    def load_server_config(self, server_name: str) -> dict:
        """
        Load the server configuration for a specific MCP server.

        Args:
            server_name (str): The name of the MCP server to load configuration for.

        Returns:
            dict: The configuration dictionary for the specified server.

        Raises:
            ValueError: If the specified server is not found in the configuration.
        """
        logger.debug(f"Attempting to load configuration for MCP server '{server_name}'.")
        mcp_servers = self.config.get("mcpServers", {})
        if server_name not in mcp_servers:
            error_msg = f"MCP server '{server_name}' not found in the configuration."
            logger.error(error_msg)
            raise ValueError(error_msg)

        server_config = mcp_servers[server_name]
        logger.debug(f"Loaded configuration for MCP server '{server_name}': {server_config}")
        return server_config

    async def initialize_session(self, server_name: str, allowed_path: str) -> ClientSession:
        """
        Initialize and connect to the specified MCP server.

        Args:
            server_name (str): The name of the MCP server to connect to.
            allowed_path (str): The path that the MCP server is allowed to access.

        Returns:
            ClientSession: An initialized MCP client session.

        Raises:
            Exception: If connection to the MCP server fails.
        """
        logger.info(f"Initializing MCP session for server '{server_name}' with allowed path '{allowed_path}'.")

        try:
            # Load server-specific configuration
            server_config = self.load_server_config(server_name)
        except ValueError as ve:
            logger.exception(f"Failed to load server configuration: {ve}")
            raise

        # Prepare server parameters for MCP connection
        server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config.get("args", []) + [allowed_path],
            env=server_config.get("env", {}).copy()  # Use copy to prevent mutation
        )
        logger.debug(f"Prepared StdioServerParameters: {server_params}")

        # Replace environment variable placeholders with actual values
        for key, value in server_params.env.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                actual_value = os.getenv(var_name)
                if actual_value is None:
                    logger.warning(f"Environment variable '{var_name}' is not set. Setting '{key}' to an empty string.")
                    server_params.env[key] = ""
                else:
                    server_params.env[key] = actual_value
                    logger.debug(f"Environment variable '{var_name}' set for '{key}': '{actual_value}'")
            else:
                logger.debug(f"Environment variable '{key}' set to '{value}'")

        try:
            # Establish stdio transport with the MCP server
            logger.debug("Establishing stdio transport with MCP server.")
            self.stdio_transport = await stdio_client(server_params)
            logger.info(f"Stdio transport established: {self.stdio_transport}")

            # Initialize MCP client session
            self.session = ClientSession(*self.stdio_transport)
            await self.session.initialize()
            logger.info("MCP session successfully initialized.")
            return self.session

        except Exception as e:
            error_msg = f"Failed to initialize MCP session for server '{server_name}': {e}"
            logger.exception(error_msg)
            raise Exception(error_msg)

    async def cleanup_session(self) -> None:
        """
        Clean up the MCP session and close the transport.

        Raises:
            Exception: If cleanup fails.
        """
        logger.info("Commencing MCP session cleanup.")

        try:
            if self.session:
                logger.debug("Closing MCP client session.")
                await self.session.close()
                logger.info("MCP client session closed successfully.")
            else:
                logger.warning("No active MCP client session to close.")

            if self.stdio_transport:
                logger.debug("Closing stdio transport.")
                await self.stdio_transport[0].close()
                logger.info("Stdio transport closed successfully.")
            else:
                logger.warning("No active stdio transport to close.")

        except Exception as e:
            error_msg = f"Error during MCP session cleanup: {e}"
            logger.exception(error_msg)
            raise Exception(error_msg)

        finally:
            # Reset session and transport to None after cleanup
            self.session = None
            self.stdio_transport = None
            logger.debug("MCPSessionManager state reset post-cleanup.")
            logger.info("MCP session and transport have been cleaned up.")

    async def reload_configuration(self) -> None:
        """
        Reload the MCP server configurations from 'mcp_server_config.json'.
        Useful if configurations change at runtime.
        """
        logger.info("Reloading MCP server configurations from 'mcp_server_config.json'.")
        try:
            self.config = self.load_config()
            logger.info("MCP server configurations reloaded successfully.")
        except Exception as e:
            logger.exception(f"Failed to reload MCP server configurations: {e}")
            raise

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
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Successfully loaded configuration from '{config_file}'.")
            logger.debug(f"Loaded configuration: {json.dumps(config, indent=4)}")
            return config
        except FileNotFoundError as e:
            error_msg = f"Configuration file '{config_file}' not found: {e}"
            logger.exception(error_msg)
            raise FileNotFoundError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in configuration file '{config_file}': {e}"
            logger.exception(error_msg)
            raise json.JSONDecodeError(error_msg, e.doc, e.pos)
        except Exception as e:
            error_msg = f"Unexpected error loading configuration: {e}"
            logger.exception(error_msg)
            raise Exception(error_msg)
