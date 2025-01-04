import pytest
import asyncio
import os
import tempfile
import sqlite3
from unittest.mock import AsyncMock
from swarm.extensions.mcp.mcp_client import MCPClientManager
from swarm.types import Tool


@pytest.fixture
def temp_db_path():
    """
    Creates a temporary SQLite database for testing.

    Yields:
        str: Path to the temporary SQLite database.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    os.remove(db_path)


@pytest.fixture
def setup_test_database(temp_db_path):
    """
    Sets up the test database with required tables and sample data.

    Args:
        temp_db_path (str): Path to the temporary SQLite database.
    """
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            credits INTEGER NOT NULL
        )
    ''')

    # Insert sample data
    cursor.executemany('''
        INSERT INTO courses (id, name, department, credits)
        VALUES (?, ?, ?, ?)
    ''', [
        (1, "Introduction to AI", "Computer Science", 3),
        (2, "Advanced Mathematics", "Mathematics", 4),
    ])

    conn.commit()
    conn.close()


@pytest.fixture
def mcp_client_manager(temp_db_path):
    """
    Initializes MCPClientManager with the real MCP server command and args.

    Args:
        temp_db_path (str): Path to the temporary SQLite database.

    Yields:
        MCPClientManager: An instance of MCPClientManager configured for testing.
    """
    env = os.environ.copy()
    env.update({
        "npm_config_registry": "https://registry.npmjs.org",
        "SQLITE_DB_PATH": temp_db_path,
    })

    manager = MCPClientManager(
        command="npx",
        args=["-y", "mcp-server-sqlite-npx", temp_db_path],
        env=env,
        timeout=30  # Adjust as needed
    )

    yield manager
    # No teardown needed since MCPClientManager's methods terminate the subprocess


@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping MCP client tests in CI environment"
)
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_test_database")
async def test_discover_tools(mcp_client_manager):
    """
    Test that discover_tools correctly retrieves available tools.

    Args:
        mcp_client_manager (MCPClientManager): Instance of MCPClientManager.
    """
    responses = await mcp_client_manager.initialize_and_list_tools()

    # Check that two responses are received
    assert len(responses) == 2, f"Expected 2 responses, got {len(responses)}"

    # Extract the 'tools/list' response, which is the second response
    tools_response = responses[1]
    assert "result" in tools_response, "No result in tools/list response."
    assert "tools" in tools_response["result"], "No tools in tools/list response."

    tool_defs = tools_response["result"]["tools"]
    assert len(tool_defs) >= 1, "Expected at least one tool."

    # Find 'read_query' tool
    read_query_def = next((tool for tool in tool_defs if tool.get("name") == "read_query"), None)
    assert read_query_def is not None, "'read_query' tool not found."

    # Optionally, verify tool details
    assert read_query_def.get("description") == "Execute a SELECT query on the SQLite database", "Tool description mismatch."
    assert "inputSchema" in read_query_def, "No inputSchema in tool definition."


@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping MCP client tests in CI environment"
)
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_test_database")
async def test_call_tool_read_query(mcp_client_manager):
    """
    Test calling the 'read_query' tool to execute a SELECT query.

    Args:
        mcp_client_manager (MCPClientManager): Instance of MCPClientManager.
    """
    # Create a mock Tool object
    mock_tool = Tool(
        name="read_query",
        description="Execute a SELECT query on the SQLite database",
        func=AsyncMock(return_value={"result": [{"id": 1, "name": "Introduction to AI", "department": "Computer Science", "credits": 3}]}),
        input_schema={"query": "string"}
    )

    # Define the SQL query for testing
    sql_query = "SELECT * FROM courses LIMIT 1"
    arguments = {"query": sql_query}

    # Call the tool
    tool_response = await mcp_client_manager.call_tool(mock_tool, arguments)

    # Check the response
    assert tool_response["result"] == [
        {
            "id": 1,
            "name": "Introduction to AI",
            "department": "Computer Science",
            "credits": 3
        }
    ], f"Tool function output mismatch. Got: {tool_response}"
