# blueprints/filesystem/blueprint_filesystem.py

"""
Filesystem Integration Blueprint
This blueprint demonstrates filesystem operations using the Open Swarm MCP framework.
"""

import json
import os
import asyncio
import logging
from typing import Dict, Any, Optional, List

from swarm import Agent, Swarm
from swarm.repl import run_demo_loop
from open_swarm_mcp.blueprint_base import BlueprintBase
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from concurrent.futures import ThreadPoolExecutor

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

CONFIG_FILE = 'mcp_server_config.json'  # Ensure this path is correct

def load_server_config(config_file: str = CONFIG_FILE) -> dict:
    """Load server configuration from the config file."""
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            logger.info(f"Loaded server configuration from {config_file}.")
            return config
    raise FileNotFoundError(f"Could not find config file {config_file}")


def create_server_parameters(server_config: dict, server_name: str) -> StdioServerParameters:
    """Create server parameters for a specific MCP server from the configuration."""
    if server_name not in server_config["mcpServers"]:
        raise ValueError(f"Server '{server_name}' not found in the configuration.")

    config = server_config["mcpServers"][server_name]
    server_parameter = StdioServerParameters(
        command=config["command"],
        args=config.get("args", []),
        env={**config.get("env", {}), "PATH": os.getenv("PATH", "")}
    )
    # Replace environment variable placeholders with actual values
    for key, value in server_parameter.env.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            server_parameter.env[key] = os.getenv(var_name, "")
    logger.info(f"Created server parameters for '{server_name}'.")
    return server_parameter


class FilesystemBlueprint(BlueprintBase):
    """
    Filesystem Integration Blueprint Implementation.
    """

    def __init__(self):
        self._metadata = {
            "title": "Filesystem Integration",
            "description": "Demonstrates filesystem operations with access to specified directories via the MCP filesystem server.",
            "required_mcp_servers": ["filesystem"],  # Updated to reflect the MCP server name in config
            "env_vars": ["ALLOWED_PATHS"]
        }
        self.client = Swarm()
        self.mcp_session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.executor = ThreadPoolExecutor(max_workers=10)  # Adjust number of workers as needed
        logger.info("Initialized Filesystem Blueprint with Swarm.")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def validate_env_vars(self) -> None:
        """Validate that required environment variables are set."""
        allowed_paths = os.getenv("ALLOWED_PATHS")
        if not allowed_paths:
            raise ValueError("Environment variable ALLOWED_PATHS is not set.")
        logger.info("Validated environment variables for Filesystem Blueprint.")

    async def connect_to_mcp_server(self):
        """Connect to the MCP filesystem server using configurations."""
        allowed_paths = os.getenv("ALLOWED_PATHS")
        if not allowed_paths:
            raise ValueError("Environment variable ALLOWED_PATHS is not set.")

        # Load server configurations
        server_config = load_server_config()

        # Create server parameters for the 'filesystem' server
        server_params = create_server_parameters(server_config, "filesystem")

        # Ensure ALLOWED_PATHS is correctly set in the environment variables
        server_params.env["ALLOWED_PATHS"] = allowed_paths

        # Add required environment variables
        # Dynamically fetch from environment or set defaults
        server_params.env["GOPATH"] = os.getenv("GOPATH", "/home/chatgpt/go")
        server_params.env["HOME"] = os.getenv("HOME", "/home/chatgpt")

        # Enter the MCP client context
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.mcp_session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.mcp_session.initialize()
        logger.info("Connected to MCP filesystem server.")

    def create_agent(self) -> Agent:
        """Create and configure the filesystem agent with synchronous wrappers."""
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
                self.sync_read_file,
                self.sync_read_multiple_files,
                self.sync_write_file,
                self.sync_create_directory,
                self.sync_list_directory,
                self.sync_move_file,
                self.sync_search_files,
                self.sync_get_file_info,
                self.sync_list_allowed_directories
            ],
            parallel_tool_calls=True
        )
        logger.info("Created FilesystemAgent with synchronous wrappers for filesystem operations.")
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
        # Run connect_to_mcp_server in the event loop using executor
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If the loop is running, schedule connect_to_mcp_server
            task = asyncio.ensure_future(self.connect_to_mcp_server())
            loop.run_until_complete(task)
        else:
            # If the loop is not running, use asyncio.run
            asyncio.run(self.connect_to_mcp_server())

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
        try:
            # Run the asynchronous interactive mode in the executor
            future = self.executor.submit(asyncio.run, self._interactive_mode_async())
            future.result()
        except Exception as e:
            print(f"Error during interactive mode: {e}")

    async def _interactive_mode_async(self) -> None:
        """
        Asynchronous helper for interactive_mode.
        """
        await self.connect_to_mcp_server()
        run_demo_loop(starting_agent=self.create_agent())

    # Synchronous wrappers for asynchronous filesystem operations
    def sync_read_file(self, path: str) -> str:
        try:
            return self.executor.submit(asyncio.run, self.read_file(path)).result()
        except Exception as e:
            logger.error(f"Sync read_file failed: {e}")
            return f"Error reading file '{path}': {e}"

    def sync_read_multiple_files(self, paths: List[str]) -> str:
        try:
            return self.executor.submit(asyncio.run, self.read_multiple_files(paths)).result()
        except Exception as e:
            logger.error(f"Sync read_multiple_files failed: {e}")
            return f"Error reading multiple files: {e}"

    def sync_write_file(self, path: str, content: str) -> str:
        try:
            return self.executor.submit(asyncio.run, self.write_file(path, content)).result()
        except Exception as e:
            logger.error(f"Sync write_file failed: {e}")
            return f"Error writing file '{path}': {e}"

    def sync_create_directory(self, path: str) -> str:
        try:
            return self.executor.submit(asyncio.run, self.create_directory(path)).result()
        except Exception as e:
            logger.error(f"Sync create_directory failed: {e}")
            return f"Error creating directory '{path}': {e}"

    def sync_list_directory(self, path: str) -> str:
        try:
            return self.executor.submit(asyncio.run, self.list_directory(path)).result()
        except Exception as e:
            logger.error(f"Sync list_directory failed: {e}")
            return f"Error listing directory '{path}': {e}"

    def sync_move_file(self, source: str, destination: str) -> str:
        try:
            return self.executor.submit(asyncio.run, self.move_file(source, destination)).result()
        except Exception as e:
            logger.error(f"Sync move_file failed: {e}")
            return f"Error moving file from '{source}' to '{destination}': {e}"

    def sync_search_files(self, path: str, pattern: str) -> str:
        try:
            return self.executor.submit(asyncio.run, self.search_files(path, pattern)).result()
        except Exception as e:
            logger.error(f"Sync search_files failed: {e}")
            return f"Error searching for '{pattern}' in '{path}': {e}"

    def sync_get_file_info(self, path: str) -> str:
        try:
            return self.executor.submit(asyncio.run, self.get_file_info(path)).result()
        except Exception as e:
            logger.error(f"Sync get_file_info failed: {e}")
            return f"Error retrieving metadata for '{path}': {e}"

    def sync_list_allowed_directories(self) -> str:
        try:
            return self.executor.submit(asyncio.run, self.list_allowed_directories()).result()
        except Exception as e:
            logger.error(f"Sync list_allowed_directories failed: {e}")
            return f"Error listing allowed directories: {e}"

    # Asynchronous filesystem operation functions
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

# Entry point for standalone execution
if __name__ == "__main__":
    blueprint = FilesystemBlueprint()
    try:
        blueprint.interactive_mode()
    except Exception as e:
        print(f"Error running Filesystem Blueprint: {e}")
