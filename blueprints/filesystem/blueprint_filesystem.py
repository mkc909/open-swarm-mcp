# blueprints/filesystem/blueprint_filesystem.py
"""
Filesystem Integration Blueprint
This blueprint demonstrates filesystem operations using the Open Swarm MCP framework.
"""
from typing import Dict, Any, Optional, List
from swarm import Agent, Swarm
from open_swarm_mcp.blueprint_base import BlueprintBase
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import asyncio
import os

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
            "description": "Demonstrates filesystem operations with access to specified directories via the MCP filesystem server.",
            "required_mcp_servers": ["mcp-filesystem-server"],  # Updated to reflect the MCP server name
            "env_vars": ["ALLOWED_PATHS"]
        }
        self.client = Swarm()
        self.mcp_session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        logger.info("Initialized Filesystem Blueprint with Swarm.")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    async def connect_to_mcp_server(self):
        """Connect to the MCP filesystem server."""
        allowed_paths = os.getenv("ALLOWED_PATHS")
        if not allowed_paths:
            raise ValueError("Environment variable ALLOWED_PATHS is not set.")
        
        server_params = StdioServerParameters(
            command="mcp-filesystem-server",  # Command to launch the MCP server
            args=allowed_paths.split(",")  # Use ALLOWED_PATHS to specify allowed directories
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.mcp_session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.mcp_session.initialize()
        logger.info("Connected to MCP filesystem server.")

    def validate_env_vars(self) -> None:
        """Validate that required environment variables are set."""
        allowed_paths = os.getenv("ALLOWED_PATHS")
        if not allowed_paths:
            raise ValueError("Environment variable ALLOWED_PATHS is not set.")
        logger.info("Validated environment variables for Filesystem Blueprint.")

    def create_agent(self) -> Agent:
        """Create and configure the filesystem agent."""
        agent = Agent(
            name="FilesystemAgent",
            instructions="""You can perform filesystem operations in the allowed directories.
            Available operations include:
            - Reading file contents (read_file, read_multiple_files)
            - Writing files (write_file)
            - Creating directories (create_directory)
            - Listing directory contents (list_directory)
            - Moving files/directories (move_file)
            - Searching for files/directories (search_files)
            - Getting file/directory metadata (get_file_info)
            - Listing allowed directories (list_allowed_directories)
            Please ensure all operations stay within the allowed paths.""",
            functions=[
                self.read_file,
                self.read_multiple_files,
                self.write_file,
                self.create_directory,
                self.list_directory,
                self.move_file,
                self.search_files,
                self.get_file_info,
                self.list_allowed_directories
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

    async def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.
        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.
        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        self.validate_env_vars()
        await self.connect_to_mcp_server()
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

    async def interactive_mode(self) -> None:
        """
        Use Swarm's REPL loop, starting with the FilesystemAgent.
        """
        logger.info("Launching interactive mode with FilesystemAgent.")
        await self.connect_to_mcp_server()
        run_demo_loop(starting_agent=self.create_agent())

    # Filesystem operation functions
    async def read_file(self, path: str) -> str:
        """
        Read contents of the specified file using the MCP server.
        Args:
            path (str): Path to the file.
        Returns:
            str: File contents or error message.
        """
        try:
            response = await self.mcp_session.call_tool("read_file", {"path": path})
            contents = response.content[0].text
            logger.info(f"Read file '{path}'.")
            return f"Contents of '{path}':\n{contents}"
        except Exception as e:
            error_msg = f"Error reading file '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def read_multiple_files(self, paths: List[str]) -> str:
        """
        Read multiple files simultaneously using the MCP server.
        Args:
            paths (List[str]): List of file paths.
        Returns:
            str: Contents of the files or error message.
        """
        try:
            response = await self.mcp_session.call_tool("read_multiple_files", {"paths": paths})
            contents = "\n".join([content.text for content in response.content])
            logger.info(f"Read multiple files: {paths}")
            return f"Contents of files:\n{contents}"
        except Exception as e:
            error_msg = f"Error reading multiple files: {e}"
            logger.error(error_msg)
            return error_msg

    async def write_file(self, path: str, content: str) -> str:
        """
        Create or overwrite a file using the MCP server.
        Args:
            path (str): Path to the file.
            content (str): Content to write into the file.
        Returns:
            str: Success message or error message.
        """
        try:
            await self.mcp_session.call_tool("write_file", {"path": path, "content": content})
            logger.info(f"Wrote file '{path}'.")
            return f"File '{path}' written successfully."
        except Exception as e:
            error_msg = f"Error writing file '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def create_directory(self, path: str) -> str:
        """
        Create a new directory using the MCP server.
        Args:
            path (str): Path to the directory.
        Returns:
            str: Success message or error message.
        """
        try:
            await self.mcp_session.call_tool("create_directory", {"path": path})
            logger.info(f"Created directory '{path}'.")
            return f"Directory '{path}' created successfully."
        except Exception as e:
            error_msg = f"Error creating directory '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def list_directory(self, path: str) -> str:
        """
        List contents of the specified directory using the MCP server.
        Args:
            path (str): Path to the directory.
        Returns:
            str: Directory contents or error message.
        """
        try:
            response = await self.mcp_session.call_tool("list_directory", {"path": path})
            contents = response.content[0].text
            logger.info(f"Listed directory '{path}'.")
            return f"Contents of '{path}':\n{contents}"
        except Exception as e:
            error_msg = f"Error listing directory '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def move_file(self, source: str, destination: str) -> str:
        """
        Move or rename a file or directory using the MCP server.
        Args:
            source (str): Source path.
            destination (str): Destination path.
        Returns:
            str: Success message or error message.
        """
        try:
            await self.mcp_session.call_tool("move_file", {"source": source, "destination": destination})
            logger.info(f"Moved file/directory from '{source}' to '{destination}'.")
            return f"File/directory moved from '{source}' to '{destination}' successfully."
        except Exception as e:
            error_msg = f"Error moving file/directory from '{source}' to '{destination}': {e}"
            logger.error(error_msg)
            return error_msg

    async def search_files(self, path: str, pattern: str) -> str:
        """
        Search for files/directories using the MCP server.
        Args:
            path (str): Starting directory.
            pattern (str): Search pattern.
        Returns:
            str: Search results or error message.
        """
        try:
            response = await self.mcp_session.call_tool("search_files", {"path": path, "pattern": pattern})
            results = response.content[0].text
            logger.info(f"Searched for '{pattern}' in '{path}'.")
            return f"Search results:\n{results}"
        except Exception as e:
            error_msg = f"Error searching for '{pattern}' in '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def get_file_info(self, path: str) -> str:
        """
        Get metadata for a file or directory using the MCP server.
        Args:
            path (str): Path to the file/directory.
        Returns:
            str: Metadata or error message.
        """
        try:
            response = await self.mcp_session.call_tool("get_file_info", {"path": path})
            metadata = response.content[0].text
            logger.info(f"Retrieved metadata for '{path}'.")
            return f"Metadata for '{path}':\n{metadata}"
        except Exception as e:
            error_msg = f"Error retrieving metadata for '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def list_allowed_directories(self) -> str:
        """
        List all directories the server is allowed to access.
        Returns:
            str: Allowed directories or error message.
        """
        try:
            response = await self.mcp_session.call_tool("list_allowed_directories", {})
            directories = response.content[0].text
            logger.info("Listed allowed directories.")
            return f"Allowed directories:\n{directories}"
        except Exception as e:
            error_msg = f"Error listing allowed directories: {e}"
            logger.error(error_msg)
            return error_msg

