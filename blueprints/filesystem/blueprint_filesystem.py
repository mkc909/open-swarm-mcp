# blueprints/filesystem/blueprint_filesystem.py

"""
FilesystemBlueprint Class for Open Swarm (MCP).

This blueprint defines agents related to filesystem interactions.
It leverages the BlueprintBase to handle all configuration and MCP session management.
"""

import logging
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.settings import DEBUG
from swarm.types import Agent

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Prevent adding multiple handlers if they already exist
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class FilesystemBlueprint(BlueprintBase):
    """
    A blueprint that defines two agents:
      - FilesystemAgent: Interacts with the filesystem via the 'filesystem' MCP server.
      - TriageAgent: Performs triage tasks without accessing any MCP server.
    """

    # def __init__(self, config: dict, **kwargs):
    #     super().__init__(config=config, **kwargs)

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the FilesystemBlueprint.

        Returns:
            Dict[str, Any]: Dictionary containing title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "Filesystem Integration Blueprint",
            "description": "Enables interaction with the filesystem via MCP server tools and includes a triage agent.",
            "required_mcp_servers": ["filesystem"],
            "env_vars": ["ALLOWED_PATHS"],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create agents for the FilesystemBlueprint.

        Returns:
            Dict[str, Agent]: Dictionary containing all created agents.
        """
        import os

        # Retrieve environment variables
        allowed_paths = os.getenv("ALLOWED_PATHS")
        if not allowed_paths:
            raise EnvironmentError("Environment variable 'ALLOWED_PATHS' is not set.")

        # Define agents dictionary
        agents = {}

        # Define transfer function with explicit reference to `agents`
        def transfer_to_filesystem() -> Agent:
            """
            Transfer control from TriageAgent to FilesystemAgent.
            """
            logger.debug("Transferring control from TriageAgent to FilesystemAgent.")
            return agents["FilesystemAgent"]

        # Create Filesystem Agent
        filesystem_agent = Agent(
            name="FilesystemAgent",
            instructions=(
                "You are the FilesystemAgent. Manage and interact with the filesystem within the allowed paths. "
                "Use the available functions provided by your MCP server to perform filesystem operations."
            ),
            mcp_servers=["filesystem"],
            env_vars={"ALLOWED_PATHS": allowed_paths},
            functions=[],  # Functions are provided by the MCP server
            parallel_tool_calls=False,  # Set based on your framework's requirements
        )

        # Create Triage Agent
        triage_agent = Agent(
            name="TriageAgent",
            instructions=(
                "You are the TriageAgent, responsible for categorizing and managing tasks. "
                "You do not have access to any external MCP servers."
            ),
            mcp_servers=[],
            env_vars={},
            functions=[transfer_to_filesystem],  # Pass the closure function
            parallel_tool_calls=False,
        )

        # Populate agents dictionary
        agents["FilesystemAgent"] = filesystem_agent
        agents["TriageAgent"] = triage_agent

        logger.debug("FilesystemAgent and TriageAgent have been created.")
        self.set_starting_agent(filesystem_agent)
        return agents

if __name__ == "__main__":
    FilesystemBlueprint.main()
