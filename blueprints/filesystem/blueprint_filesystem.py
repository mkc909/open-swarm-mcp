# blueprints/filesystem/blueprint_filesystem.py

"""
FilesystemBlueprint Class for Open Swarm MCP.

This blueprint defines agents related to filesystem interactions.
It leverages the BlueprintBase to handle all configuration and MCP session management.
"""

import logging
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Prevent adding multiple handlers if they already exist
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class FilesystemBlueprint(BlueprintBase):
    """
    A blueprint that defines two agents:
      - FilesystemAgent: Interacts with the filesystem via the 'npx-filesystem' MCP server.
      - TriageAgent: Performs triage tasks without accessing any MCP server.
    """

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
            "required_mcp_servers": ["npx-filesystem"],
            "env_vars": ["ALLOWED_PATHS"],
        }

    def create_agents(self) -> None:
        """
        Create agents for the FilesystemBlueprint.
        """
        import os

        # Retrieve environment variables
        allowed_paths = os.getenv("ALLOWED_PATHS")
        if not allowed_paths:
            raise EnvironmentError("Environment variable 'ALLOWED_PATHS' is not set.")

        # Define transfer functions
        def transfer_to_filesystem() -> Agent:
            """
            Transfer control from TriageAgent to FilesystemAgent.
            """
            logger.debug("Transferring control from TriageAgent to FilesystemAgent.")
            return self.swarm.agents.get("FilesystemAgent")

        # Filesystem Agent
        filesystem_agent = Agent(
            name="FilesystemAgent",
            instructions=(
                "You are the FilesystemAgent. Manage and interact with the filesystem within the allowed paths. "
                "Use the available functions to read, write, or modify files and directories."
            ),
            mcp_servers=["npx-filesystem"],
            env_vars={"ALLOWED_PATHS": allowed_paths},
            functions=[],
        )

        # Triage Agent
        triage_agent = Agent(
            name="TriageAgent",
            instructions=(
                "You are the TriageAgent, responsible for categorizing and managing tasks. "
                "You do not have access to any external MCP servers."
            ),
            mcp_servers=[],
            env_vars={},
            functions=[
                # Attach transfer function directly
                transfer_to_filesystem,
            ],
        )

        # Register agents with Swarm
        self.swarm.create_agent(filesystem_agent)
        self.swarm.create_agent(triage_agent)

    def run(self):
        """
        Run the blueprint interactively using the Swarm client.
        """
        logger.info("Starting FilesystemBlueprint.")
        # Example initial message
        initial_messages = [
            {"role": "user", "content": "Organize the documents in the allowed paths."}
        ]
        response = self.swarm.run(
            agent=self.swarm.agents.get("FilesystemAgent"),
            messages=initial_messages,
        )
        logger.info("Run completed. Final response:")
        logger.info(response.messages[-1]["content"])


if __name__ == "__main__":
    FilesystemBlueprint.main()
