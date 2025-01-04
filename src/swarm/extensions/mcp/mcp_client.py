# mcp_client.py

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


class MCPClientManager:
    """
    A class for interacting with MCP servers using JSON-RPC requests.
    """

    def __init__(self, command: str = "npx", args: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None, timeout: int = 30):
        self.command = command
        self.args = [os.path.expandvars(arg) for arg in (args or [])]
        self.env = {**os.environ.copy(), **(env or {})}
        self.timeout = timeout
        logger.debug(f"Initialized MCPClientManager with command='{self.command}', args={self.args}, timeout={self.timeout}")

    async def _send_request(self, process: asyncio.subprocess.Process, request: dict):
        """
        Sends a JSON-RPC request to the server.

        Args:
            process (asyncio.subprocess.Process): The running MCP server process.
            request (dict): JSON-RPC request.
        """
        request_str = json.dumps(request) + "\n"
        logger.debug(f"Sending request: {request}")
        process.stdin.write(request_str.encode())
        await process.stdin.drain()

    async def _read_stream(self, stream: asyncio.StreamReader, callback: Callable[[str], None]):
        """
        Reads lines from a given stream and processes them with a callback.

        Args:
            stream (asyncio.StreamReader): The stream to read from.
            callback (Callable): The function to process each line.
        """
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded = line.decode().strip()
            if decoded:
                callback(decoded)

    async def _read_responses(self, process: asyncio.subprocess.Process, count: int) -> List[dict]:
        """
        Reads JSON-RPC responses from the server.

        Args:
            process (asyncio.subprocess.Process): The running MCP server process.
            count (int): Number of responses to read.

        Returns:
            list: Parsed JSON-RPC responses.
        """
        responses = []
        buffer = ""
        try:
            while len(responses) < count:
                chunk = await asyncio.wait_for(process.stdout.read(1024), timeout=self.timeout)
                if not chunk:
                    break
                buffer += chunk.decode()
                logger.debug(f"Read chunk: {chunk}")

                while True:
                    try:
                        json_data, idx = json.JSONDecoder().raw_decode(buffer)
                        responses.append(json_data)
                        buffer = buffer[idx:].lstrip()
                        if len(responses) == count:
                            break
                    except json.JSONDecodeError:
                        break
        except asyncio.TimeoutError:
            logger.error("Timed out waiting for JSON responses.")
        return responses

    async def _run_with_process(self, requests: List[dict]) -> List[dict]:
        """
        Runs the MCP server process and sends requests.

        Args:
            requests (list): List of JSON-RPC requests.

        Returns:
            list: JSON-RPC responses.
        """
        process = await asyncio.create_subprocess_exec(
            self.command, *self.args,
            env=self.env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        logger.debug(f"Started process: {self.command} {' '.join(self.args)}")

        try:
            # Start reading stderr in the background to prevent blocking
            asyncio.create_task(self._read_stream(process.stderr, lambda line: logger.debug(f"MCP Server stderr: {line}")))

            for request in requests:
                await self._send_request(process, request)

            responses = await self._read_responses(process, len(requests))
            logger.debug(f"Received responses: {responses}")
            return responses
        finally:
            process.terminate()
            await process.wait()
            logger.debug("Process terminated.")

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
                "clientInfo": {"name": "test-client", "version": "0.1"}
            }
        }

        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        responses = await self._run_with_process([initialize_request, list_tools_request])

        tools = []
        for response in responses:
            if 'result' in response and 'tools' in response['result']:
                for tool_info in response['result']['tools']:
                    tool = Tool(
                        name=tool_info.get('name', 'UnnamedTool'),
                        description=tool_info.get('description', 'No description provided.'),
                        func=self._create_tool_callable(tool_info.get('name')),
                        input_schema=tool_info.get('input_schema')
                    )
                    tools.append(tool)
            elif 'error' in response:
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
        async def tool_callable(**kwargs):
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
                    "arguments": kwargs
                }
            }

            responses = await self._run_with_process([call_tool_request])

            for response in responses:
                if 'result' in response:
                    return response['result']
                elif 'error' in response:
                    logger.error(f"Error in tool call '{tool_name}': {response['error']}")
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
                "clientInfo": {"name": "test-client", "version": "0.1"}
            }
        }

        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        responses = await self._run_with_process([initialize_request, list_tools_request])
        return responses

    async def test_methods(self, tools: List[Tool]):
        """
        Tests the MCPClientManager methods by calling a sample tool.

        Args:
            tools (List[Tool]): List of discovered tools.
        """
        logger.info(f"Initialization and List Tools Responses: {tools}")

        if tools:
            # Example: Call the first discovered tool with sample arguments
            sample_tool = tools[0]
            logger.info(f"Running tool '{sample_tool.name}' with sample arguments.")
            # Define sample arguments based on tool's input_schema or description
            sample_arguments = {"query": "SELECT * FROM courses LIMIT 1"}  # Modify as needed
            try:
                result = await self.call_tool(sample_tool, sample_arguments)
                logger.info(f"Result from '{sample_tool.name}': {result}")
            except Exception as e:
                logger.error(f"Error calling tool '{sample_tool.name}': {e}")
        else:
            logger.warning("No tools found or invalid response.")

    async def main(self):
        """
        Main entry point for running the MCPClientManager.
        """
        tools = await self.discover_tools()
        await self.test_methods(tools)


if __name__ == "__main__":
    client = MCPClientManager(
        command="npx",
        args=["-y", "mcp-server-sqlite-npx", "./artificial_university.db"]
    )
    asyncio.run(client.main())
