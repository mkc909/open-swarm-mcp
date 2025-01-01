# src/swarm/blueprints/filesystem/blueprint_filesystem.py

"""
Filesystem Integration Blueprint

This blueprint demonstrates filesystem operations using the MCP (Modular Command Protocol) server.
It provides functionalities to read, write, list, and manage files and directories within allowed paths.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional

from swarm.blueprint_base import BlueprintBase
from swarm.utils.mcp_session_manager import MCPSessionManager
from swarm import Agent, Swarm
from concurrent.futures import ThreadPoolExecutor

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
stream_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(stream_handler)


class FilesystemBlueprint(BlueprintBase):
    """
    Filesystem Integration Blueprint Implementation.
    Handles filesystem operations via the MCP server.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Filesystem Blueprint.
        Sets up the MCP session manager and executor for synchronous operations.
        
        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary. If not provided, it will be loaded by BlueprintBase.
        """
        super().__init__(config)
        # Override the executor if needed or use the one from BlueprintBase
        self.executor = ThreadPoolExecutor(max_workers=10)  # Adjust as needed
        logger.info("Initialized Filesystem Blueprint with MCP Session Manager and ThreadPoolExecutor.")

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata about the Filesystem Blueprint.

        Returns:
            Dict[str, Any]: Metadata dictionary containing title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "Filesystem Integration",
            "description": "Demonstrates filesystem operations with access to specified directories via the MCP filesystem server.",
            "required_mcp_servers": ["filesystem"],
            "env_vars": ["ALLOWED_PATHS"],
            "default_args": "--allowed-paths /tmp/"
        }

    def validate_env_vars(self) -> None:
        """
        Validate that required environment variables are set.

        Raises:
            ValueError: If any required environment variable is missing.
        """
        super().validate_env_vars()
        allowed_paths = self.get_env_var("ALLOWED_PATHS")
        if not allowed_paths:
            error_msg = "Environment variable 'ALLOWED_PATHS' is not set."
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.debug(f"Validated environment variable 'ALLOWED_PATHS': {allowed_paths}")

    async def connect_to_mcp(self) -> None:
        """
        Asynchronously connect to the MCP server using the session manager.

        Raises:
            Exception: If connection to the MCP server fails.
        """
        allowed_paths = self.get_env_var("ALLOWED_PATHS")
        if not allowed_paths:
            error_msg = "Environment variable 'ALLOWED_PATHS' is not set."
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            self.session = await self.mcp_session_manager.initialize_session("filesystem", allowed_paths)
            logger.debug("MCP session successfully established.")
        except Exception as e:
            error_msg = f"Failed to connect to MCP server: {e}"
            logger.error(error_msg)
            raise

    async def list_directory_async(self, path: str) -> str:
        """
        Asynchronously list the contents of a specified directory.

        Args:
            path (str): The directory path to list.

        Returns:
            str: Contents of the directory or an error message.
        """
        if not self.session:
            error_msg = "MCP session is not initialized."
            logger.error(error_msg)
            return error_msg

        logger.debug(f"Attempting to list directory: '{path}'")
        try:
            response = await self.session.call_tool("list_directory", {"path": path})
            directory_contents = response.content[0].text
            logger.info(f"Listed directory '{path}' successfully.")
            return f"Contents of '{path}':\n{directory_contents}"
        except Exception as e:
            error_msg = f"Error listing directory '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def cleanup(self) -> None:
        """
        Asynchronously clean up the MCP session.

        Raises:
            Exception: If cleanup fails.
        """
        await self.mcp_session_manager.cleanup_session()
        logger.debug("Filesystem Blueprint cleanup completed.")

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        logger.info("Executing Filesystem Blueprint in framework integration mode.")
        self.validate_env_vars()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.connect_to_mcp())
            agent = self.create_agent()
            messages = config.get('messages', [{
                "role": "user",
                "content": "List all files in the allowed directories."
            }]) if config else [{
                "role": "user",
                "content": "List all files in the allowed directories."
            }]
            response = self.run_swarm(agent, messages)
            return {
                "status": "success",
                "messages": response.messages,
                "metadata": self.metadata
            }
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "status": "failure",
                "messages": [{"role": "error", "content": str(e)}],
                "metadata": self.metadata
            }
        finally:
            loop.run_until_complete(self.cleanup())
            loop.close()
            logger.debug("Event loop closed after execution.")

    def run_swarm(self, agent: Agent, messages: List[Dict[str, Any]]) -> Any:
        """
        Run the Swarm client with the specified agent and messages.

        Args:
            agent (Agent): The agent to start the Swarm with.
            messages (List[Dict[str, Any]]): List of messages to initiate the conversation.

        Returns:
            Any: The response from the Swarm client.
        """
        logger.debug("Initializing Swarm client with the provided agent and messages.")
        swarm_client = Swarm()
        swarm_client.run(agent=agent, messages=messages)
        logger.debug("Swarm client run completed.")
        return swarm_client

    def create_agent(self) -> Agent:
        """
        Create and configure the filesystem agent with synchronous wrappers.

        Returns:
            Agent: The configured FilesystemAgent.
        """
        selected_model = self.get_model()
        selected_base_url = self.get_base_url()
        logger.info(f"Creating FilesystemAgent with model '{selected_model}' and base URL '{selected_base_url}'.")

        agent = Agent(
            name="FilesystemAgent",
            model=selected_model,  # Dynamically fetch model from config
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
            parallel_tool_calls=True,
            base_url=selected_base_url  # Pass the base URL to the agent if supported
        )
        logger.debug(f"FilesystemAgent created successfully with model '{selected_model}' and base URL '{selected_base_url}'.")
        return agent

    # Synchronous wrappers for asynchronous filesystem operations
    def sync_read_file(self, path: str) -> str:
        """
        Synchronously read the contents of a file.

        Args:
            path (str): Path to the file.

        Returns:
            str: File contents or an error message.
        """
        logger.debug(f"Synchronously reading file: '{path}'")
        try:
            result = self.executor.submit(asyncio.run, self.read_file(path)).result()
            logger.debug(f"File '{path}' read successfully.")
            return result
        except Exception as e:
            error_msg = f"Error reading file '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    def sync_read_multiple_files(self, paths: List[str]) -> str:
        """
        Synchronously read multiple files.

        Args:
            paths (List[str]): List of file paths.

        Returns:
            str: Contents of the files or an error message.
        """
        logger.debug(f"Synchronously reading multiple files: {paths}")
        try:
            result = self.executor.submit(asyncio.run, self.read_multiple_files(paths)).result()
            logger.debug("Multiple files read successfully.")
            return result
        except Exception as e:
            error_msg = f"Error reading multiple files: {e}"
            logger.error(error_msg)
            return error_msg

    def sync_write_file(self, path: str, content: str) -> str:
        """
        Synchronously write content to a file.

        Args:
            path (str): Path to the file.
            content (str): Content to write.

        Returns:
            str: Success message or an error message.
        """
        logger.debug(f"Synchronously writing to file: '{path}'")
        try:
            result = self.executor.submit(asyncio.run, self.write_file(path, content)).result()
            logger.debug(f"File '{path}' written successfully.")
            return result
        except Exception as e:
            error_msg = f"Error writing file '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    def sync_create_directory(self, path: str) -> str:
        """
        Synchronously create a directory.

        Args:
            path (str): Path to the directory.

        Returns:
            str: Success message or an error message.
        """
        logger.debug(f"Synchronously creating directory: '{path}'")
        try:
            result = self.executor.submit(asyncio.run, self.create_directory(path)).result()
            logger.debug(f"Directory '{path}' created successfully.")
            return result
        except Exception as e:
            error_msg = f"Error creating directory '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    def sync_list_directory(self, path: str) -> str:
        """
        Synchronously list the contents of a directory.

        Args:
            path (str): Path to the directory.

        Returns:
            str: Directory contents or an error message.
        """
        logger.debug(f"Synchronously listing directory: '{path}'")
        try:
            result = self.executor.submit(asyncio.run, self.list_directory(path)).result()
            logger.debug(f"Directory '{path}' listed successfully.")
            return result
        except Exception as e:
            error_msg = f"Error listing directory '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    def sync_move_file(self, source: str, destination: str) -> str:
        """
        Synchronously move or rename a file or directory.

        Args:
            source (str): Source path.
            destination (str): Destination path.

        Returns:
            str: Success message or an error message.
        """
        logger.debug(f"Synchronously moving '{source}' to '{destination}'")
        try:
            result = self.executor.submit(asyncio.run, self.move_file(source, destination)).result()
            logger.debug(f"Moved '{source}' to '{destination}' successfully.")
            return result
        except Exception as e:
            error_msg = f"Error moving '{source}' to '{destination}': {e}"
            logger.error(error_msg)
            return error_msg

    def sync_search_files(self, path: str, pattern: str) -> str:
        """
        Synchronously search for files/directories matching a pattern.

        Args:
            path (str): Starting directory path.
            pattern (str): Search pattern.

        Returns:
            str: Search results or an error message.
        """
        logger.debug(f"Synchronously searching for pattern '{pattern}' in '{path}'")
        try:
            result = self.executor.submit(asyncio.run, self.search_files(path, pattern)).result()
            logger.debug(f"Search for pattern '{pattern}' in '{path}' completed successfully.")
            return result
        except Exception as e:
            error_msg = f"Error searching for '{pattern}' in '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    def sync_get_file_info(self, path: str) -> str:
        """
        Synchronously retrieve metadata for a file or directory.

        Args:
            path (str): Path to the file or directory.

        Returns:
            str: Metadata information or an error message.
        """
        logger.debug(f"Synchronously getting file info for '{path}'")
        try:
            result = self.executor.submit(asyncio.run, self.get_file_info(path)).result()
            logger.debug(f"File info for '{path}' retrieved successfully.")
            return result
        except Exception as e:
            error_msg = f"Error retrieving metadata for '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    def sync_list_allowed_directories(self) -> str:
        """
        Synchronously list all allowed directories.

        Returns:
            str: List of allowed directories or an error message.
        """
        logger.debug("Synchronously listing allowed directories.")
        try:
            result = self.executor.submit(asyncio.run, self.list_allowed_directories()).result()
            logger.debug("Allowed directories listed successfully.")
            return result
        except Exception as e:
            error_msg = f"Error listing allowed directories: {e}"
            logger.error(error_msg)
            return error_msg

    # Asynchronous filesystem operation functions
    async def read_file(self, path: str) -> str:
        """
        Asynchronously read the contents of a file using the MCP server.

        Args:
            path (str): Path to the file.

        Returns:
            str: File contents or an error message.
        """
        logger.debug(f"Asynchronously reading file: '{path}'")
        try:
            response = await self.session.call_tool("read_file", {"path": path})
            contents = response.content[0].text
            logger.info(f"Read file '{path}' successfully.")
            return f"Contents of '{path}':\n{contents}"
        except Exception as e:
            error_msg = f"Error reading file '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def read_multiple_files(self, paths: List[str]) -> str:
        """
        Asynchronously read multiple files using the MCP server.

        Args:
            paths (List[str]): List of file paths.

        Returns:
            str: Combined contents of the files or an error message.
        """
        logger.debug(f"Asynchronously reading multiple files: {paths}")
        try:
            response = await self.session.call_tool("read_multiple_files", {"paths": paths})
            contents = "\n".join([content.text for content in response.content])
            logger.info(f"Read multiple files {paths} successfully.")
            return f"Contents of files:\n{contents}"
        except Exception as e:
            error_msg = f"Error reading multiple files: {e}"
            logger.error(error_msg)
            return error_msg

    async def write_file(self, path: str, content: str) -> str:
        """
        Asynchronously write content to a file using the MCP server.

        Args:
            path (str): Path to the file.
            content (str): Content to write.

        Returns:
            str: Success message or an error message.
        """
        logger.debug(f"Asynchronously writing to file: '{path}'")
        try:
            await self.session.call_tool("write_file", {"path": path, "content": content})
            logger.info(f"Wrote to file '{path}' successfully.")
            return f"File '{path}' written successfully."
        except Exception as e:
            error_msg = f"Error writing file '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def create_directory(self, path: str) -> str:
        """
        Asynchronously create a directory using the MCP server.

        Args:
            path (str): Path to the directory.

        Returns:
            str: Success message or an error message.
        """
        logger.debug(f"Asynchronously creating directory: '{path}'")
        try:
            await self.session.call_tool("create_directory", {"path": path})
            logger.info(f"Directory '{path}' created successfully.")
            return f"Directory '{path}' created successfully."
        except Exception as e:
            error_msg = f"Error creating directory '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def list_directory(self, path: str) -> str:
        """
        Asynchronously list the contents of a directory using the MCP server.

        Args:
            path (str): Path to the directory.

        Returns:
            str: Directory contents or an error message.
        """
        logger.debug(f"Asynchronously listing directory: '{path}'")
        try:
            response = await self.session.call_tool("list_directory", {"path": path})
            directory_contents = response.content[0].text
            logger.info(f"Listed directory '{path}' successfully.")
            return f"Contents of '{path}':\n{directory_contents}"
        except Exception as e:
            error_msg = f"Error listing directory '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def move_file(self, source: str, destination: str) -> str:
        """
        Asynchronously move or rename a file or directory using the MCP server.

        Args:
            source (str): Source path.
            destination (str): Destination path.

        Returns:
            str: Success message or an error message.
        """
        logger.debug(f"Asynchronously moving '{source}' to '{destination}'")
        try:
            await self.session.call_tool("move_file", {"source": source, "destination": destination})
            logger.info(f"Moved '{source}' to '{destination}' successfully.")
            return f"File/directory moved from '{source}' to '{destination}' successfully."
        except Exception as e:
            error_msg = f"Error moving '{source}' to '{destination}': {e}"
            logger.error(error_msg)
            return error_msg

    async def search_files(self, path: str, pattern: str) -> str:
        """
        Asynchronously search for files/directories matching a pattern using the MCP server.

        Args:
            path (str): Starting directory path.
            pattern (str): Search pattern.

        Returns:
            str: Search results or an error message.
        """
        logger.debug(f"Asynchronously searching for pattern '{pattern}' in '{path}'")
        try:
            response = await self.session.call_tool("search_files", {"path": path, "pattern": pattern})
            search_results = response.content[0].text
            logger.info(f"Searched for '{pattern}' in '{path}' successfully.")
            return f"Search results:\n{search_results}"
        except Exception as e:
            error_msg = f"Error searching for '{pattern}' in '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def get_file_info(self, path: str) -> str:
        """
        Asynchronously retrieve metadata for a file or directory using the MCP server.

        Args:
            path (str): Path to the file or directory.

        Returns:
            str: Metadata information or an error message.
        """
        logger.debug(f"Asynchronously getting file info for '{path}'")
        try:
            response = await self.session.call_tool("get_file_info", {"path": path})
            metadata = response.content[0].text
            logger.info(f"Retrieved metadata for '{path}' successfully.")
            return f"Metadata for '{path}':\n{metadata}"
        except Exception as e:
            error_msg = f"Error retrieving metadata for '{path}': {e}"
            logger.error(error_msg)
            return error_msg

    async def list_allowed_directories(self) -> str:
        """
        Asynchronously list all directories the server is allowed to access.

        Returns:
            str: List of allowed directories or an error message.
        """
        logger.debug("Asynchronously listing allowed directories.")
        try:
            response = await self.session.call_tool("list_allowed_directories", {})
            allowed_dirs = response.content[0].text
            logger.info("Listed allowed directories successfully.")
            return f"Allowed directories:\n{allowed_dirs}"
        except Exception as e:
            error_msg = f"Error listing allowed directories: {e}"
            logger.error(error_msg)
            return error_msg

    async def _interactive_mode_async(self) -> None:
        """
        Asynchronous helper method for interactive mode.
        Connects to MCP and starts the Swarm REPL loop.
        """
        await self.connect_to_mcp()
        try:
            logger.info("Launching interactive mode with FilesystemAgent.")
            agent = self.create_agent()
            swarm = Swarm()
            swarm.run(agent=agent, messages=[])
            logger.debug("Swarm REPL loop has been initiated.")
        except Exception as e:
            logger.error(f"Error during interactive mode: {e}")
        finally:
            await self.cleanup()

    def interactive_mode(self) -> None:
        """
        Run the blueprint in interactive standalone mode.
        Uses asyncio to handle asynchronous operations.
        """
        logger.info("Starting interactive mode for Filesystem Blueprint.")
        try:
            try:
                # Check if there's an existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If running, create a new task
                    logger.debug("Existing event loop detected. Creating a new task for interactive mode.")
                    asyncio.create_task(self._interactive_mode_async())
                else:
                    # If not running, run normally
                    logger.debug("No existing event loop. Running interactive mode normally.")
                    asyncio.run(self._interactive_mode_async())
            except RuntimeError as re:
                # If no event loop is present, create a new one
                logger.debug("RuntimeError detected. Creating a new event loop for interactive mode.")
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(self._interactive_mode_async())
                new_loop.close()
        except Exception as e:
            logger.error(f"Interactive mode failed: {e}", exc_info=True)
            print(f"Interactive mode failed: {e}")

    def get_agents(self) -> Dict[str, Agent]:
        """
        Return the dictionary of agents used by this blueprint.

        Returns:
            Dict[str, Agent]: Mapping of agent names to Agent instances.
        """
        # Currently, only one agent is defined. Expand as needed.
        return {"FilesystemAgent": self.create_agent()}

    def create_agent(self) -> Agent:
        """
        Create and configure the filesystem agent with synchronous wrappers.

        Returns:
            Agent: The configured FilesystemAgent.
        """
        selected_model = self.get_model()
        selected_base_url = self.get_base_url()
        logger.info(f"Creating FilesystemAgent with model '{selected_model}' and base URL '{selected_base_url}'.")

        agent = Agent(
            name="FilesystemAgent",
            model=selected_model,  # Dynamically fetch model from config
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
            parallel_tool_calls=True,
            base_url=selected_base_url  # Pass the base URL to the agent if supported
        )
        logger.debug(f"FilesystemAgent created successfully with model '{selected_model}' and base URL '{selected_base_url}'.")
        return agent

    # You can expand this blueprint with additional methods as needed.


# Allow blueprint to be run directly
if __name__ == "__main__":
    try:
        # Initialize the blueprint with configuration
        blueprint = FilesystemBlueprint()
        blueprint.validate_env_vars()
        blueprint.interactive_mode()
    except Exception as e:
        logger.error(f"Error during blueprint execution: {e}")
        print(f"Error during blueprint execution: {e}")
