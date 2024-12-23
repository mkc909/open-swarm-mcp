# blueprints/filesystem/blueprint_filesystem.py

"""
Filesystem Integration Blueprint

This blueprint demonstrates filesystem operations using the Open Swarm MCP framework.
"""

import os
from typing import Dict, Any, Optional
from swarm import Agent
from open_swarm_mcp.blueprint_base import BlueprintBase

class FilesystemBlueprint(BlueprintBase):
    """
    Filesystem Integration Blueprint Implementation.
    """

    def __init__(self):
        super().__init__()
        self._metadata = {
            "title": "Filesystem Integration",
            "description": "Demonstrates filesystem operations with access to specified directories via MCP servers.",
            "required_mcp_servers": ["filesystem"],
            "env_vars": ["ALLOWED_PATHS"]
        }

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def validate_env_vars(self) -> None:
        """Validate that required environment variables are set and directories exist."""
        allowed_paths = os.getenv("ALLOWED_PATHS")
        if not allowed_paths:
            raise ValueError("Environment variable ALLOWED_PATHS is not set.")

        for path in allowed_paths.split(","):
            path = path.strip()
            if not os.path.exists(path):
                raise ValueError(f"Directory does not exist: {path}")

    def create_agent(self) -> Agent:
        """Create and configure the filesystem agent."""
        return Agent(
            name="FilesystemAgent",
            instructions="""You can perform filesystem operations in the allowed directories.
Available operations include:
- Listing directory contents
- Reading file contents
- Creating new files
- Moving files between allowed directories
Please ensure all operations stay within the allowed paths."""
        )

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        self.validate_env_vars()
        agent = self.create_agent()

        # Allow for message override from framework config
        default_message = {
            "role": "user",
            "content": "List all PDF files in the allowed directories."
        }
        messages = config.get('messages', [default_message]) if config else [default_message]

        response = self.client.run(agent=agent, messages=messages)

        return {
            "status": "success",
            "messages": response.messages,
            "metadata": self.metadata
        }

# Entry point for standalone execution
if __name__ == "__main__":
    blueprint = FilesystemBlueprint()
    try:
        blueprint.interactive_mode()
    except Exception as e:
        print(f"Error running Filesystem Blueprint: {e}")
