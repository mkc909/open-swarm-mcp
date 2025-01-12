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

CHANGELOG:
- Always re-initialize (ID=1) before listing (ID=2) or calling (ID=2) a tool,
  creating a new process each time. This avoids lock-ups on subsequent calls.
"""

import asyncio
import json
import logging
import os
from typing import List, Callable, Dict, Any, Optional

from pydantic import BaseModel
from swarm.settings import DEBUG
from swarm.types import Tool

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)


class MCPClient:
    """
    MCPClient manages the subprocess communication with an MCP server.
    Each operation (listing or calling a tool) launches a fresh process:
      1) ID=1 for "initialize"
      2) ID=2 for either "tools/list" or "tools/call"
    """

    def __init__(
        self,
        command: str = "npx",
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        self.command = command
        self.args = [os.path.expandvars(arg) for arg in (args or [])]
        self.env = {**os.environ.copy(), **(env or {})}
        self.timeout = timeout

        # If you previously cached discovered tools, you can remove or keep this.
        # In this example, we do not rely on caching because each request spawns a fresh server.
        self._tools_cache: Optional[List[Tool]] = None

        logger.debug(
            f"Initialized MCPClient with command='{self.command}', args={self.args}, timeout={self.timeout}"
        )
        logger.debug(f"SQLITE_DB_PATH environment variable: {self.env.get('SQLITE_DB_PATH')}")

    async def _send_request(self, process: asyncio.subprocess.Process, request: dict):
        """
        Sends a JSON-RPC request to the server.

        Args:
            process (asyncio.subprocess.Process): The running MCP server process.
            request (dict): JSON-RPC request.
        """
        request_str = json.dumps(request) + "\n"
        logger.debug(f"Sending request: {request}")
        try:
            process.stdin.write(request_str.encode())
            await asyncio.wait_for(process.stdin.drain(), timeout=self.timeout)
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
        Reads JSON-RPC responses from the server.

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
        except Exception as e:
            logger.error(f"Error reading responses: {e}")
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
        """
        try:
            total_timeout = self.timeout * 2  # e.g. 2 requests => 2 x timeout

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
                    stderr_buffer = []

                    async def stderr_reader():
                        while True:
                            line = await process.stderr.readline()
                            if not line:
                                break
                            decoded_line = line.decode().strip()
                            stderr_buffer.append(decoded_line)
                            logger.debug(f"MCP Server stderr: {decoded_line}")

                    asyncio.create_task(stderr_reader())

                    # Small delay for the server to come up
                    await asyncio.sleep(1)

                    # Send all requests
                    for req in requests:
                        await self._send_request(process, req)

                    # Collect responses
                    responses = await self._read_responses(process, len(requests))
                    logger.debug(f"Received responses: {responses}")

                    # Wait a moment for any final stderr
                    await asyncio.sleep(0.5)
                    if stderr_buffer:
                        logger.debug(
                            f"MCP Server stderr output: {' | '.join(stderr_buffer)}"
                        )

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

            return await asyncio.wait_for(process_runner(), timeout=total_timeout)

        except asyncio.TimeoutError:
            logger.error(f"Operation exceeded timeout of {total_timeout} seconds.")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during _run_with_process: {e}")
            raise

    async def discover_tools(self) -> List[Tool]:
        """
        Initializes a fresh MCP server, requests the tool list, and returns them.

        Returns:
            list: List of Tool instances.
        """
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,  # Always init with ID=1
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
            "id": 2,  # Then 'tools/list' with ID=2
            "method": "tools/list",
            "params": {},
        }

        responses = await self._run_with_process([initialize_request, list_tools_request])
        logger.debug(f"Raw tool discovery responses: {responses}")

        tools = []
        for response in responses:
            if "result" in response and "tools" in response["result"]:
                # This response includes a list of tool definitions
                for tool_info in response["result"]["tools"]:
                    tool_func = await self._create_tool_callable(tool_info.get("name"))
                    tool = Tool(
                        name=tool_info.get("name", "UnnamedTool"),
                        description=tool_info.get("description", "No description provided."),
                        func=tool_func,
                        input_schema=tool_info.get("inputSchema", {}),
                    )
                    tools.append(tool)
            elif "error" in response:
                logger.error(f"Error in tool discovery: {response['error']}")

        logger.debug(f"Discovered tools: {[tool.name for tool in tools]}")
        return tools

    async def _create_tool_callable(self, tool_name: str) -> Callable[..., Any]:
        async def dynamic_tool_func(**kwargs) -> Any:
            logger.debug(f"Creating tool callable for '{tool_name}' with arguments: {kwargs}")

            # 1) ID=1 for initialization
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "server_name": "example-client",
                    "protocolVersion": "1.0",
                    "capabilities": {},
                    "clientInfo": {"name": "tool-call-client", "version": "0.1"},
                },
            }
            logger.debug(f"Initialization request for tool '{tool_name}': {init_request}")

            # 2) ID=2 to call the tool
            call_tool_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": kwargs,
                },
            }
            logger.debug(f"Tool call request for '{tool_name}': {call_tool_request}")

            # Send both requests in a single invocation
            responses = await self._run_with_process([init_request, call_tool_request])
            logger.debug(f"Received responses for tool '{tool_name}': {responses}")

            # Initialize variable to hold tool call response
            tool_response = None

            for response in responses:
                logger.debug(f"Processing response for tool '{tool_name}': {response}")
                if "id" in response and response["id"] == 2:
                    if "result" in response:
                        result = response["result"]
                        logger.debug(f"Result found for tool '{tool_name}': {result}")

                        # Check for errors
                        if result.get("isError"):
                            error_msg = result.get("error", "Unknown error.")
                            logger.error(f"Tool '{tool_name}' returned error: {error_msg}")
                            raise RuntimeError(f"Tool '{tool_name}' error: {error_msg}")

                        # Extract content
                        content = result.get("content", [])
                        logger.debug(f"Content for tool '{tool_name}': {content}")

                        if content and isinstance(content, list) and len(content) > 0:
                            text_payload = content[0].get("text", "").strip()
                            logger.debug(f"Text payload for tool '{tool_name}': {text_payload}")

                            if text_payload == "[]":
                                logger.debug(f"Empty JSON array returned for '{tool_name}', indicating success.")
                                return "Success"

                            if text_payload.startswith("["):
                                try:
                                    parsed = json.loads(text_payload)
                                    logger.debug(f"Parsed JSON array for '{tool_name}': {parsed}")
                                    return parsed
                                except json.JSONDecodeError as e:
                                    logger.debug(f"Failed to parse JSON for '{tool_name}': {e}") # TODO false positives?

                            if text_payload:
                                logger.debug(f"Returning plain text payload for '{tool_name}': {text_payload}")
                                return text_payload

                        # Fallback if no recognized content
                        fallback_result = result.get("result")
                        logger.debug(f"Fallback result for tool '{tool_name}': {fallback_result}")
                        return fallback_result

                    elif "error" in response:
                        logger.error(f"Error in response for tool '{tool_name}': {response['error']}")
                        raise RuntimeError(f"Tool call error: {response['error']}")

            # If tool_response was not found or processed
            logger.error(f"No valid responses received for tool '{tool_name}'.")
            raise RuntimeError(f"Invalid tool response structure for '{tool_name}'.")

        # Mark the function as dynamic for the swarm
        dynamic_tool_func.dynamic = True
        return dynamic_tool_func
    
    async def call_tool(self, tool: Tool, arguments: Dict[str, Any]) -> Any:
        """
        Calls a specific tool on the MCP server.

        This is just a convenience wrapper around the dynamic_tool_func
        that was assigned to tool.func. We do not rely on the cache here;
        each invocation restarts a new process.

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
        DEPRECATED:
        For demonstration only. This method does a raw initialize+list
        but doesn't parse the results into Tool objects.

        Returns:
            list: JSON-RPC responses from server.
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
        self,
        stream: asyncio.StreamReader,
        callback: Callable[[str], None]
    ):
        """
        Utility for reading lines from a stream. Not used in the current approach.
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
        Retrieves the list of tools from the MCP server, but due to the new
        process approach, we just call `discover_tools()` each time.

        Returns:
            list: The newly discovered tools.

        Raises:
            RuntimeError: If tool discovery fails.
        """
        # If you want to keep a cache, you could store it in self._tools_cache.
        # But each new call re-initializes the process. Example:
        if self._tools_cache is not None:
            logger.debug("Returning cached tools.")
            return self._tools_cache

        logger.debug("No cached tools found. Running discover_tools().")
        tools = await self.discover_tools()
        self._tools_cache = tools
        return tools
