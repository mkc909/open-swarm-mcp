# blueprints/filesystem/blueprint_filesystem.py

"""
FilesystemBlueprint Class for Open Swarm MCP.

This blueprint defines agents related to filesystem interactions.
It leverages the BlueprintBase to handle all configuration and MCP session management.
"""

import logging
from typing import Dict, Any, Callable

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent, AgentFunctionDefinition  # Updated import

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

        # Define filesystem interaction functions
        def read_file(content: str) -> str:
            """
            Reads the content of a specified file.

            Args:
                content (str): The path of the file to read.

            Returns:
                str: The content of the file.
            """
            try:
                with open(content, 'r') as file:
                    data = file.read()
                logger.info(f"Read file at {content}")
                return data
            except Exception as e:
                logger.error(f"Error reading file at {content}: {e}")
                return f"Failed to read file: {e}"

        def write_file(content: str, data: str) -> str:
            """
            Writes data to a specified file.

            Args:
                content (str): The path of the file to write to.
                data (str): The data to write into the file.

            Returns:
                str: Confirmation message.
            """
            try:
                with open(content, 'w') as file:
                    file.write(data)
                logger.info(f"Wrote data to file at {content}")
                return f"Successfully wrote to {content}"
            except Exception as e:
                logger.error(f"Error writing to file at {content}: {e}")
                return f"Failed to write to file: {e}"

        # Define transfer functions
        def transfer_to_filesystem() -> Agent:
            """
            Transfer control from TriageAgent to FilesystemAgent.
            """
            logger.debug("Transferring control from TriageAgent to FilesystemAgent.")
            return self.swarm.agents.get("FilesystemAgent")

        # Wrap filesystem functions using AgentFunctionDefinition
        read_file_func = AgentFunctionDefinition(
            name="read_file",
            description="Reads the content of a specified file.",
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The path of the file to read."
                    }
                },
                "required": ["content"]
            },
            func=read_file
        )

        write_file_func = AgentFunctionDefinition(
            name="write_file",
            description="Writes data to a specified file.",
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The path of the file to write to."
                    },
                    "data": {
                        "type": "string",
                        "description": "The data to write into the file."
                    }
                },
                "required": ["content", "data"]
            },
            func=write_file
        )

        # Wrap transfer function
        transfer_func = AgentFunctionDefinition(
            name="transfer_to_filesystem",
            description="Transfers control to the FilesystemAgent.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            func=transfer_to_filesystem
        )

        # Filesystem Agent
        filesystem_agent = Agent(
            name="FilesystemAgent",
            instructions=(
                "You are the FilesystemAgent. Manage and interact with the filesystem within the allowed paths. "
                "Use the available functions to read, write, or modify files and directories."
            ),
            mcp_servers=["filesystem"],
            env_vars={"ALLOWED_PATHS": allowed_paths},
            functions=[read_file_func, write_file_func],
            parallel_tool_calls=False  # Set based on your framework's requirements
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
            functions=[transfer_func],
            parallel_tool_calls=False
        )

        # Register agents with Swarm
        self.swarm.create_agent(filesystem_agent)
        self.swarm.create_agent(triage_agent)
        logger.info("FilesystemAgent and TriageAgent have been created and registered.")

    def run(self):
        """
        Run the blueprint interactively using the Swarm client.
        """
        logger.info("Starting FilesystemBlueprint.")
        # Start interactive mode with FilesystemAgent as the starting agent
        self.interactive_mode(starting_agent=self.swarm.agents.get("FilesystemAgent"))


if __name__ == "__main__":
    FilesystemBlueprint.main()
