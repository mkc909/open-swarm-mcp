# blueprints/filesystem/blueprint_filesystem.py

"""
Filesystem Integration Blueprint

This blueprint demonstrates filesystem operations using the Open Swarm MCP framework.
"""

import os
from typing import Dict, Any, Optional
from swarm import Agent, Swarm
from open_swarm_mcp.blueprint_base import BlueprintBase
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class FilesystemBlueprint(BlueprintBase):
    """
    Filesystem Integration Blueprint Implementation.
    """

    def __init__(self):
        self._metadata = {
            "title": "Filesystem Integration",
            "description": "Demonstrates filesystem operations with access to specified directories via MCP servers.",
            "required_mcp_servers": ["filesystem"],
            "env_vars": ["ALLOWED_PATHS"]
        }
        self.client = Swarm()
        logger.info("Initialized Filesystem Blueprint with Swarm.")

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
        logger.info("Validated environment variables for Filesystem Blueprint.")

    def create_agent(self) -> Agent:
        """Create and configure the filesystem agent."""
        agent = Agent(
            name="FilesystemAgent",
            instructions="""You can perform filesystem operations in the allowed directories.
Available operations include:
- Listing directory contents
- Reading file contents
- Creating new files
- Moving files between allowed directories
Please ensure all operations stay within the allowed paths.""",
            functions=[
                self.list_directory,
                self.read_file,
                self.create_file,
                self.move_file
            ],
            parallel_tool_calls=True
        )
        logger.info("Created FilesystemAgent with filesystem operation functions.")
        return agent

    def get_agents(self) -> Dict[str, Agent]:
        """
        Returns a dictionary of agents.
        """
        return {"FilesystemAgent": self.create_agent()}

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

    def interactive_mode(self) -> None:
        """
        Use Swarm's REPL loop, starting with the FilesystemAgent.
        """
        logger.info("Launching interactive mode with FilesystemAgent.")
        run_demo_loop(starting_agent=self.create_agent())

    # Filesystem operation functions

    def list_directory(self, directory: str) -> str:
        """
        List contents of the specified directory.

        Args:
            directory (str): Path to the directory.

        Returns:
            str: Directory contents or error message.
        """
        allowed_paths = os.getenv("ALLOWED_PATHS", "").split(",")
        directory = directory.strip()
        if not any(os.path.commonpath([directory, ap]).startswith(ap) for ap in allowed_paths):
            error_msg = f"Access to '{directory}' is not allowed."
            logger.warning(error_msg)
            return error_msg
        try:
            contents = os.listdir(directory)
            contents_str = "\n".join(contents)
            logger.info(f"Listed directory '{directory}'.")
            return f"Contents of '{directory}':\n{contents_str}"
        except Exception as e:
            error_msg = f"Error listing directory '{directory}': {e}"
            logger.error(error_msg)
            return error_msg

    def read_file(self, file_path: str) -> str:
        """
        Read contents of the specified file.

        Args:
            file_path (str): Path to the file.

        Returns:
            str: File contents or error message.
        """
        allowed_paths = os.getenv("ALLOWED_PATHS", "").split(",")
        file_path = file_path.strip()
        if not any(os.path.commonpath([file_path, ap]).startswith(ap) for ap in allowed_paths):
            error_msg = f"Access to '{file_path}' is not allowed."
            logger.warning(error_msg)
            return error_msg
        try:
            with open(file_path, 'r') as f:
                contents = f.read()
            logger.info(f"Read file '{file_path}'.")
            return f"Contents of '{file_path}':\n{contents}"
        except Exception as e:
            error_msg = f"Error reading file '{file_path}': {e}"
            logger.error(error_msg)
            return error_msg

    def create_file(self, file_path: str, content: str = "") -> str:
        """
        Create a new file with the specified content.

        Args:
            file_path (str): Path to the new file.
            content (str): Content to write into the file.

        Returns:
            str: Success message or error message.
        """
        allowed_paths = os.getenv("ALLOWED_PATHS", "").split(",")
        file_path = file_path.strip()
        if not any(os.path.commonpath([file_path, ap]).startswith(ap) for ap in allowed_paths):
            error_msg = f"Access to '{file_path}' is not allowed."
            logger.warning(error_msg)
            return error_msg
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            logger.info(f"Created file '{file_path}'.")
            return f"File '{file_path}' created successfully."
        except Exception as e:
            error_msg = f"Error creating file '{file_path}': {e}"
            logger.error(error_msg)
            return error_msg

    def move_file(self, source: str, destination: str) -> str:
        """
        Move a file from source to destination.

        Args:
            source (str): Source file path.
            destination (str): Destination file path.

        Returns:
            str: Success message or error message.
        """
        allowed_paths = os.getenv("ALLOWED_PATHS", "").split(",")
        source = source.strip()
        destination = destination.strip()
        if not (any(os.path.commonpath([source, ap]).startswith(ap) for ap in allowed_paths) and
                any(os.path.commonpath([destination, ap]).startswith(ap) for ap in allowed_paths)):
            error_msg = f"Access to '{source}' or '{destination}' is not allowed."
            logger.warning(error_msg)
            return error_msg
        try:
            os.rename(source, destination)
            logger.info(f"Moved file from '{source}' to '{destination}'.")
            return f"File moved from '{source}' to '{destination}' successfully."
        except Exception as e:
            error_msg = f"Error moving file from '{source}' to '{destination}': {e}"
            logger.error(error_msg)
            return error_msg
