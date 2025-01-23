"""
Integration tests for MCP tool execution using the 'everything' server.
"""

import pytest
import asyncio
import logging
from swarm.extensions.mcp.mcp_client import MCPClient
from swarm.types import Tool

# Configure logging for the tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# "everything" server configuration
EVERYTHING_SERVER_CONFIG = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-everything"],
    "env": {},
    "timeout": 30,
}

@pytest.fixture
def mcp_client():
    """
    Initializes MCPClient configured for the 'everything' server.

    Yields:
        MCPClient: An instance of MCPClient configured for testing.
    """
    client = MCPClient(server_config=EVERYTHING_SERVER_CONFIG, timeout=30)
    yield client


@pytest.mark.asyncio
async def test_discover_tools(mcp_client):
    """
    Test that MCPClient can discover tools from the 'everything' server.

    Args:
        mcp_client (MCPClient): Instance of MCPClient.
    """
    tools = await mcp_client.list_tools()

    # Ensure at least one tool is discovered
    assert len(tools) > 0, "Expected at least one tool from the 'everything' server."

    # Verify the tools have expected properties
    expected_tool_names = {"echo", "add", "longRunningOperation", "printEnv", "sampleLLM", "getTinyImage"}
    discovered_tool_names = {tool.name for tool in tools}

    for tool_name in expected_tool_names:
        assert tool_name in discovered_tool_names, f"Expected tool '{tool_name}' not found."

    logger.info(f"Discovered tools: {discovered_tool_names}")


@pytest.mark.asyncio
async def test_call_tool_echo(mcp_client):
    """
    Test calling the 'echo' tool.

    Args:
        mcp_client (MCPClient): Instance of MCPClient.
    """
    tools = await mcp_client.list_tools()
    echo_tool = next((tool for tool in tools if tool.name == "echo"), None)
    assert echo_tool is not None, "'echo' tool not found."

    # Call the tool
    arguments = {"message": "Hello, MCP!"}
    result = await mcp_client.execute_tool(echo_tool, arguments)

    # Extract the text content from the response
    text_content = result.content[0].text
    assert text_content == "Echo: Hello, MCP!", f"Unexpected result from 'echo' tool: {text_content}"


@pytest.mark.asyncio
async def test_call_tool_add(mcp_client):
    """
    Test calling the 'add' tool.

    Args:
        mcp_client (MCPClient): Instance of MCPClient.
    """
    tools = await mcp_client.list_tools()
    add_tool = next((tool for tool in tools if tool.name == "add"), None)
    assert add_tool is not None, "'add' tool not found."

    # Call the tool
    arguments = {"a": 5, "b": 7}
    result = await mcp_client.execute_tool(add_tool, arguments)

    # Extract the text content from the response
    text_content = result.content[0].text
    assert text_content == "The sum of 5 and 7 is 12.", f"Unexpected result from 'add' tool: {text_content}"


# @pytest.mark.asyncio
# async def test_tool_caching(mcp_client):
#     """
#     Test that tools are cached after discovery to prevent redundant MCP server processes.

#     Args:
#         mcp_client (MCPClient): Instance of MCPClient.
#     """
#     # Discover tools once
#     tools_first_call = await mcp_client.list_tools()

#     # Verify caching by calling list_tools again (should return the same tools)
#     tools_second_call = await mcp_client.list_tools()
#     assert tools_first_call == tools_second_call, "Tools should be cached between calls."

#     # Verify that the same objects are returned
#     assert all(t1.name == t2.name for t1, t2 in zip(tools_first_call, tools_second_call)), "Cached tools should have identical names."
