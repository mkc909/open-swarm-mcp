"""
Integration tests for MCP tool execution using the 'everything' and 'sqlite-uvx' servers.
"""

import pytest
import asyncio
import logging
import os
from swarm.extensions.mcp.mcp_client import MCPClient
from swarm.types import Tool

# Configure logging for the tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Server configurations
EVERYTHING_SERVER_CONFIG = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-everything"],
    "env": {},
    "timeout": 30,
}

SQLITE_UVX_SERVER_CONFIG = {
    "command": "uvx",
    "args": ["mcp-server-sqlite", "--db-path", "/tmp/test.db"],
    "env": {},
    "timeout": 30,
}

@pytest.fixture
def mcp_client_everything():
    """
    Initializes MCPClient configured for the 'everything' server.

    Yields:
        MCPClient: An instance of MCPClient configured for testing.
    """
    client = MCPClient(server_config=EVERYTHING_SERVER_CONFIG, timeout=30)
    yield client


@pytest.fixture
def mcp_client_sqlite():
    """
    Initializes MCPClient configured for the 'sqlite-uvx' server.

    Yields:
        MCPClient: An instance of MCPClient configured for SQLite server testing.
    """
    client = MCPClient(server_config=SQLITE_UVX_SERVER_CONFIG, timeout=30)
    yield client


@pytest.mark.asyncio
async def test_discover_tools_everything(mcp_client_everything):
    """
    Test that MCPClient can discover tools from the 'everything' server.

    Args:
        mcp_client_everything (MCPClient): Instance of MCPClient.
    """
    tools = await mcp_client_everything.list_tools()

    # Ensure at least one tool is discovered
    assert len(tools) > 0, "Expected at least one tool from the 'everything' server."

    # Verify the tools have expected properties
    expected_tool_names = {"echo", "add", "longRunningOperation", "printEnv", "sampleLLM", "getTinyImage"}
    discovered_tool_names = {tool.name for tool in tools}

    for tool_name in expected_tool_names:
        assert tool_name in discovered_tool_names, f"Expected tool '{tool_name}' not found."

    logger.info(f"Discovered tools: {discovered_tool_names}")


@pytest.mark.asyncio
async def test_call_tool_echo(mcp_client_everything):
    """
    Test calling the 'echo' tool.

    Args:
        mcp_client_everything (MCPClient): Instance of MCPClient.
    """
    tools = await mcp_client_everything.list_tools()
    echo_tool = next((tool for tool in tools if tool.name == "echo"), None)
    assert echo_tool is not None, "'echo' tool not found."

    # Call the tool
    arguments = {"message": "Hello, MCP!"}
    result = await mcp_client_everything.execute_tool(echo_tool, arguments)

    # Extract the text content from the response
    text_content = result.content[0].text
    assert text_content == "Echo: Hello, MCP!", f"Unexpected result from 'echo' tool: {text_content}"

@pytest.mark.asyncio
async def test_sqlite_operations(mcp_client_sqlite):
    """
    Test creating, querying, and cleaning up a database using the SQLite UVX server.

    Args:
        mcp_client_sqlite (MCPClient): Instance of MCPClient.
    """
    tools = await mcp_client_sqlite.list_tools()
    create_table_tool = next((tool for tool in tools if tool.name == "write_query"), None)
    read_query_tool = next((tool for tool in tools if tool.name == "read_query"), None)
    assert create_table_tool is not None, "'write_query' tool not found."
    assert read_query_tool is not None, "'read_query' tool not found."

    # Step 1: Create a table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS test_table (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        value INTEGER NOT NULL
    );
    """
    await mcp_client_sqlite.execute_tool(create_table_tool, {"query": create_table_query})

    # Step 2: Insert a record
    insert_query = "INSERT INTO test_table (id, name, value) VALUES (1, 'Test Record', 123);"
    await mcp_client_sqlite.execute_tool(create_table_tool, {"query": insert_query})

    # Step 3: Query the record
    select_query = "SELECT * FROM test_table WHERE id = 1;"
    result = await mcp_client_sqlite.execute_tool(read_query_tool, {"query": select_query})

    # Extract the actual result from the tool response
    assert hasattr(result, "content"), "Tool response is missing 'content'."
    text_content = result.content[0].text  # Assuming first text block contains the query result

    # Convert the stringified JSON into a Python object for comparison
    query_result = eval(text_content)  # Avoid eval if possible; replace with json.loads if input format is JSON
    expected_result = [{"id": 1, "name": "Test Record", "value": 123}]
    assert query_result == expected_result, f"Unexpected query result: {query_result}"

    # Step 4: Cleanup the database
    os.remove("/tmp/test.db")
    assert not os.path.exists("/tmp/test.db"), "Database file was not deleted."

