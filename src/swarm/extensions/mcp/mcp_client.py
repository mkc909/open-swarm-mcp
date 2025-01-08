# src/swarm/extensions/mcp/mcp_client.py

"""
MCP Client Manager for JSON-RPC
-------------------------------
This client interacts with MCP servers using JSON-RPC. It manages tool discovery
and tool invocation, returning instances of the Tool class for better integration.

Features:
- Initializes the MCP server and discovers available tools.
- Calls specific tools with arguments.
- Parses JSON-RPC responses into Tool instances.
- Configurable command, arguments, and environment variables.
"""

import asyncio
import json
import logging
import os
from typing import List, Callable, Dict, Any, Optional
from pydantic import BaseModel

from swarm.types import Tool  # Ensure this import path is correct

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCPClient manages the subprocess communication with an MCP server.
    """

    def __init__(
        self,
        command: str = "npx",
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 30,  # Increased default timeout for robustness
    ):
        self.command = command
        self.args = [os.path.expandvars(arg) for arg in (args or [])]
        self.env = {**os.environ.copy(), **(env or {})}
        self.timeout = timeout
        self._tools_cache: Optional[List[Tool]] = None  # Cache for discovered tools
        logger.debug(
            f"Initialized MCPClient with command='{self.command}', args={self.args}, timeout={self.timeout}"
        )

    async def _send_request(self, process: asyncio.subprocess.Process, request: dict):
        """
        Sends a JSON-RPC request to the MCP server.

        Args:
            process (asyncio.subprocess.Process): The running MCP server process.
            request (dict): JSON-RPC request.
        """
        request_str = json.dumps(request) + "\n"
        logger.debug(f"Sending request: {request}")
        try:
            # Write asynchronously to the process's stdin
            process.stdin.write(request_str.encode())
            await asyncio.wait_for(process.stdin.drain(), timeout=self.timeout)
            logger.debug("Request sent successfully.")
        except asyncio.TimeoutError:
            logger.error("Timeout while sending request to MCP server.")
            raise
        except Exception as e:
            logger.error(f"Error while sending request: {e}")
            raise

    async def _read_responses(
        self, process: asyncio.subprocess.Process, count: int
    ) -> List[dict]:
        """
        Reads JSON-RPC responses from the MCP server.

        Args:
            process (asyncio.subprocess.Process): The running MCP server process.
            count (int): Number of expected responses.

        Returns:
            list: JSON-RPC responses.
        """
        responses = []
        buffer = ""
        try:
            while len(responses) < count:
                chunk = await asyncio.wait_for(process.stdout.read(1024), timeout=self.timeout)
                if not chunk:
                    logger.warning("No more data from MCP server.")
                    break
                buffer += chunk.decode()
                logger.debug(f"Read chunk from stdout: {chunk}")

                while True:
                    try:
                        json_data, idx = json.JSONDecoder().raw_decode(buffer)
                        responses.append(json_data)
                        buffer = buffer[idx:].lstrip()
                        logger.debug(f"Parsed JSON-RPC response: {json_data}")
                        if len(responses) == count:
                            break
                    except json.JSONDecodeError:
                        logger.debug("Incomplete JSON detected, awaiting more data.")
                        break
        except asyncio.TimeoutError:
            logger.error("Timeout while reading responses from MCP server.")
            raise
        except Exception as e:
            logger.error(f"Error reading responses: {e}")
            raise
        logger.debug(f"Final parsed responses: {responses}")
        return responses

    async def _run_with_process(self, requests: List[dict]) -> List[dict]:
        """
        Runs the MCP server process and sends requests, with an overarching timeout.

        Args:
            requests (list): List of JSON-RPC requests.

        Returns:
            list: JSON-RPC responses.

        Raises:
            asyncio.TimeoutError: If the entire process takes too long.
            Exception: For any unexpected errors.
        """
        try:
            # Define a single timeout for the entire operation
            timeout = self.timeout * 2  # Allow double the timeout for safety

            async def process_runner():
                process = await asyncio.create_subprocess_exec(
                    self.command,
                    *self.args,
                    env=self.env,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                logger.debug(f"Started process: {self.command} {' '.join(self.args)}")

                try:
                    # Read stderr in the background
                    asyncio.create_task(
                        self._read_stream(
                            process.stderr,
                            lambda line: logger.debug(f"MCP Server stderr: {line}"),
                        )
                    )

                    # Send requests
                    for request in requests:
                        await self._send_request(process, request)

                    # Read responses
                    responses = await self._read_responses(process, len(requests))
                    logger.debug(f"Received responses: {responses}")
                    return responses
                finally:
                    try:
                        process.terminate()
                        await asyncio.wait_for(process.wait(), timeout=self.timeout)
                        logger.debug("Process terminated cleanly.")
                    except asyncio.TimeoutError:
                        logger.warning("Terminate timeout exceeded; killing process.")
                        process.kill()
                        await process.wait()
                        logger.debug("Process killed.")

            # Run the process runner within the timeout
            return await asyncio.wait_for(process_runner(), timeout=timeout)

        except asyncio.TimeoutError:
            logger.error(f"Operation exceeded timeout of {timeout} seconds.")
            raise

        except Exception as e:
            logger.error(f"Unexpected error during _run_with_process: {e}")
            raise

    async def discover_tools(self) -> List[Tool]:
        """
        Initializes the MCP server and discovers available tools.

        Returns:
            list: List of Tool instances.
        """
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "server_name": "example-client",
                "protocolVersion": "1.0",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.1"},
            },
        }

        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        responses = await self._run_with_process([initialize_request, list_tools_request])
        logger.debug(f"Raw tool discovery responses: {responses}")

        tools = []
        for response in responses:
            if "result" in response and "tools" in response["result"]:
                for tool_info in response["result"]["tools"]:
                    tool = Tool(
                        name=tool_info.get("name", "UnnamedTool"),
                        description=tool_info.get("description", "No description provided."),
                        func=self._create_tool_callable(tool_info.get("name")),
                        input_schema=tool_info.get("input_schema", {}),
                    )
                    tools.append(tool)
            elif "error" in response:
                logger.error(f"Error in tool discovery: {response['error']}")

        logger.info(f"Discovered tools: {[tool.name for tool in tools]}")
        return tools

    def _create_tool_callable(self, tool_name: str) -> Callable[..., Any]:
        """
        Creates a callable function for the given tool name.

        Args:
            tool_name (str): The name of the tool.

        Returns:
            Callable[..., Any]: The function to execute the tool.
        """

        async def tool_callable(**kwargs) -> Any:
            """
            A generic tool callable that sends a JSON-RPC request to call the tool.

            Args:
                **kwargs: Arguments for the tool.

            Returns:
                Any: The result from the tool.
            """
            call_tool_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": kwargs,
                },
            }

            responses = await self._run_with_process([call_tool_request])

            for response in responses:
                if "result" in response:
                    return response["result"]
                elif "error" in response:
                    logger.error(
                        f"Error in tool call '{tool_name}': {response['error']}"
                    )
                    raise Exception(f"Tool call error: {response['error']}")

        return tool_callable

    async def call_tool(self, tool: Tool, arguments: Dict[str, Any]) -> Any:
        """
        Calls a specific tool on the MCP server.

        Args:
            tool (Tool): The tool to call.
            arguments (dict): Arguments for the tool.

        Returns:
            Any: The result from the tool.
        """
        logger.debug(f"Calling tool '{tool.name}' with arguments: {arguments}")
        return await tool.func(**arguments)

    async def initialize_and_list_tools(self) -> List[dict]:
        """
        Initializes the MCP server and lists available tools.

        Returns:
            list: JSON-RPC responses.
        """
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "server_name": "example-client",
                "protocolVersion": "1.0",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.1"},
            },
        }

        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        responses = await self._run_with_process([initialize_request, list_tools_request])
        return responses

    async def _read_stream(
        self, stream: asyncio.StreamReader, callback: Callable[[str], None]
    ):
        """
        Reads lines from a given stream and processes them with a callback.

        Args:
            stream (asyncio.StreamReader): The stream to read from.
            callback (Callable): The function to process each line.
        """
        while True:
            try:
                line = await asyncio.wait_for(stream.readline(), timeout=self.timeout)
                if not line:
                    break
                if isinstance(line, bytes):
                    decoded = line.decode().strip()
                    if decoded:
                        logger.debug(f"Read line from stream: {decoded}")
                        callback(decoded)
                else:
                    logger.error(f"Unexpected line type: {type(line)}")
            except asyncio.TimeoutError:
                logger.error("Timeout while reading from stream.")
                break
            except Exception as e:
                logger.error(f"Error reading stream: {e}")
                break

    async def get_tools(self, agent_name: str) -> List[Tool]:
        """
        Retrieves the list of tools from the MCP server, utilizing caching.

        Args:
            agent_name (str): The name of the agent requesting tools.

        Returns:
            list: List of Tool instances.

        Raises:
            RuntimeError: If tool discovery fails.
        """
        if self._tools_cache is not None:
            logger.debug("Returning cached tools.")
            return self._tools_cache

        logger.debug("No cached tools found. Discovering tools now.")
        tools = await self.discover_tools()
        self._tools_cache = tools  # Cache the discovered tools
        return tools
