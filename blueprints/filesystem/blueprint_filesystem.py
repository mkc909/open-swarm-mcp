# blueprints/filesystem/blueprint_filesystem.py

"""
FilesystemBlueprint Class for Open Swarm MCP.

This blueprint defines agents related to filesystem interactions.
It leverages the BlueprintBase to handle all configuration and MCP session management.
"""

import logging
from typing import Dict, Any, Callable

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent  # Removed AgentFunctionDefinition import

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
      - FilesystemAgent: Interacts with the filesystem via the 'filesystem' MCP server.
      - TriageAgent: Performs triage tasks without accessing any MCP server.
    """

    def __init__(self):
        super().__init__()
        self.create_agents()

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

    def create_agents(self) -> None:
        """
        Create agents for the FilesystemBlueprint.
        """
        import os

        # Retrieve environment variables
        allowed_paths = os.getenv("ALLOWED_PATHS")
        if not allowed_paths:
            raise EnvironmentError("Environment variable 'ALLOWED_PATHS' is not set.")

        # Define transfer function
        def transfer_to_filesystem() -> Agent:
            """
            Transfer control from TriageAgent to FilesystemAgent.
            """
            logger.debug("Transferring control from TriageAgent to FilesystemAgent.")
            return self.filesystem_agent  # Directly return the FilesystemAgent

        # Create Filesystem Agent
        self.filesystem_agent = Agent(
            name="FilesystemAgent",
            instructions=(
                "You are the FilesystemAgent. Manage and interact with the filesystem within the allowed paths. "
                "Use the available functions provided by your MCP server to perform filesystem operations."
            ),
            mcp_servers=["filesystem"],
            env_vars={"ALLOWED_PATHS": allowed_paths},
            functions=[],  # Functions are provided by the MCP server
            parallel_tool_calls=False  # Set based on your framework's requirements
        )

        # Create Triage Agent
        self.triage_agent = Agent(
            name="TriageAgent",
            instructions=(
                "You are the TriageAgent, responsible for categorizing and managing tasks. "
                "You do not have access to any external MCP servers."
            ),
            mcp_servers=[],
            env_vars={},
            functions=[transfer_to_filesystem],  # Passing function directly
            parallel_tool_calls=False
        )

        logger.info("FilesystemAgent and TriageAgent have been created and assigned.")

    def run(self):
        """
        Run the blueprint interactively using the Swarm client.
        """
        logger.info("Starting FilesystemBlueprint.")
        # Start interactive mode with TriageAgent as the starting agent
        self.interactive_mode(starting_agent=self.triage_agent)


if __name__ == "__main__":
    import argparse

    # Parse command-line arguments for streaming mode
    parser = argparse.ArgumentParser(description="Run FilesystemBlueprint REPL.")
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming mode for responses."
    )
    args = parser.parse_args()

    # Instantiate the blueprint
    blueprint = FilesystemBlueprint()

    # Run the blueprint's interactive REPL loop with the TriageAgent
    blueprint.run()
