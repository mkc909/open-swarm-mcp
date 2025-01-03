"""
Raw MCP Client for JSON-RPC
---------------------------
This client interacts with MCP servers using raw JSON-RPC. It serves as a temporary
implementation until the official MCP library is stable and feature-complete.

Features:
- Supports initializing the MCP server and listing tools.
- Allows calling specific tools with arguments.
- Configurable command, arguments, and environment variables.

TODO:
- [ ] Replace raw JSON-RPC calls with the official MCP library when stable.
"""

import asyncio
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    A class for interacting with MCP servers using raw JSON-RPC requests.

    Attributes:
        command (str): The command to run the MCP server.
        args (list): Arguments for the MCP server command.
        env (dict): Environment variables for the MCP server.
        timeout (int): Timeout for reading responses.
    """
    def __init__(self, command="npx", args=None, env=None, timeout=30):
        self.command = command
        self.args = args or []
        self.env = env or os.environ.copy()
        self.timeout = timeout
        logger.debug(f"Initialized RawMCPClient with command='{self.command}', args={self.args}, timeout={self.timeout}")

    async def _send_request(self, process, request):
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

    async def _read_responses(self, process, count):
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

    async def _run_with_process(self, requests):
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
            for request in requests:
                await self._send_request(process, request)

            responses = await self._read_responses(process, len(requests))
            logger.debug(f"Received responses: {responses}")
            return responses
        finally:
            process.terminate()
            await process.wait()
            logger.debug("Process terminated.")

    async def initialize_and_list_tools(self):
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

    async def call_tool(self, tool_name, arguments):
        """
        Calls a specific tool on the MCP server.

        Args:
            tool_name (str): Name of the tool to call.
            arguments (dict): Arguments for the tool.

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

        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        responses = await self._run_with_process([initialize_request, call_tool_request])
        return responses


# Example usage
async def test_methods(client):
    responses = await client.initialize_and_list_tools()
    logger.info(f"Initialization and List Tools Responses: {responses}")

    if responses and "result" in responses[-1]:
        logger.info("Running query on table 'courses'.")
        result = await client.call_tool("read_query", {"query": "SELECT * FROM courses LIMIT 1"})
        logger.info(f"Result from 'read_query': {result}")
    else:
        logger.warning("No tools found or invalid response.")


async def main():
    client = RawMCPClient(
        command="npx",
        args=["-y", "mcp-server-sqlite-npx", "./artificial_university.db"]
    )
    await test_methods(client)


if __name__ == "__main__":
    asyncio.run(main())
