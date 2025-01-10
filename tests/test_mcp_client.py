# tests/test_mcp_client.py

"""
Integration tests for MCP tool execution from the blueprint filesystem.
"""

import pytest
import asyncio
import os
import tempfile
import sqlite3
import logging
from unittest.mock import AsyncMock
from swarm.extensions.mcp.mcp_client import MCPClient
from swarm.types import Tool, Agent

# Configure logging for the tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
    logger.debug(f"Setting up test database at {temp_db_path}")
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Create tables
    logger.debug("Creating 'courses' table.")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            credits INTEGER NOT NULL
        )
    ''')

    # Insert sample data
    logger.debug("Inserting sample data into 'courses' table.")
    cursor.executemany('''
        INSERT INTO courses (id, name, department, credits)
        VALUES (?, ?, ?, ?)
    ''', [
        (1, "Introduction to AI", "Computer Science", 3),
        (2, "Advanced Mathematics", "Mathematics", 4),
    ])

    conn.commit()
    conn.close()
    logger.debug("Test database setup complete.")


@pytest.fixture
def mcp_client_manager(temp_db_path, setup_test_database):
    """
    Initializes MCPClient with the MCP server command and args.

    Args:
        temp_db_path (str): Path to the temporary SQLite database.

    Yields:
        MCPClient: An instance of MCPClient configured for testing.
    """
    env = os.environ.copy()
    env.update({
        "npm_config_registry": "https://registry.npmjs.org",
        # "SQLITE_DB_PATH": temp_db_path,  # Uncomment if needed by the MCP server
    })

    manager = MCPClient(
        command="npx",
        args=["-y", "mcp-server-sqlite-npx", temp_db_path],
        env=env,
        timeout=30  # Adjust as needed
    )

    logger.debug(f"MCPClient manager initialized with env: {env}")
    yield manager
    # No teardown needed since MCPClient's methods terminate the subprocess


@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping MCP client tests in CI environment due to unknown issue executing npx."
)
@pytest.mark.asyncio
async def test_discover_tools(mcp_client_manager):
    """
    Test that discover_tools correctly retrieves available tools.

    Args:
        mcp_client_manager (MCPClient): Instance of MCPClient.
    """
    tools = await mcp_client_manager.get_tools("FilesystemAgent")

    # Check that at least one tool is discovered
    assert len(tools) >= 1, f"Expected at least 1 tool, got {len(tools)}"

    # Find 'read_query' tool
    read_query_tool = next((tool for tool in tools if tool.name == "read_query"), None)
    assert read_query_tool is not None, "'read_query' tool not found."

    # Verify tool details
    assert read_query_tool.description == "Execute a SELECT query on the SQLite database", "Tool description mismatch."

    # Properly define 'schema' from the tool's input_schema
    schema = read_query_tool.input_schema
    assert "query" in schema.get("properties", {}), "Missing 'query' property in schema"


@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping MCP client tests in CI environment due to unknown issue executing npx."
)
@pytest.mark.asyncio
async def test_call_tool_read_query(mcp_client_manager):
    """
    Test calling the 'read_query' tool to execute a SELECT query.

    Args:
        mcp_client_manager (MCPClient): Instance of MCPClient.
    """
    # Discover tools
    tools = await mcp_client_manager.get_tools("FilesystemAgent")
    read_query_tool = next((tool for tool in tools if tool.name == "read_query"), None)
    assert read_query_tool is not None, "'read_query' tool not found."

    # Define the SQL query for testing
    sql_query = "SELECT * FROM courses LIMIT 1"
    arguments = {"query": sql_query}

    # Call the tool
    tool_response = await mcp_client_manager.call_tool(read_query_tool, arguments)

    # Check the response
    expected_result = [
        {
            "id": 1,
            "name": "Introduction to AI",
            "department": "Computer Science",
            "credits": 3
        }
    ]
    assert tool_response == expected_result, f"Tool function output mismatch. Got: {tool_response}"


@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping MCP client tests in CI environment due to unknown issue executing npx."
)
@pytest.mark.asyncio
async def test_call_tool_write_query(mcp_client_manager, temp_db_path):
    """
    Test calling the 'write_query' tool to execute an INSERT statement.

    Args:
        mcp_client_manager (MCPClient): Instance of MCPClient.
        temp_db_path (str): Path to the temporary SQLite database.
    """
    # Discover tools
    tools = await mcp_client_manager.get_tools("FilesystemAgent")
    write_query_tool = next((tool for tool in tools if tool.name == "write_query"), None)
    assert write_query_tool is not None, "'write_query' tool not found."

    # Define the SQL INSERT query for testing
    sql_insert = "INSERT INTO courses (id, name, department, credits) VALUES (3, 'Data Structures', 'Computer Science', 4)"
    arguments = {"query": sql_insert}

    # Call the tool
    tool_response = await mcp_client_manager.call_tool(write_query_tool, arguments)

    # Check the response
    assert tool_response == "Success", f"Tool function output mismatch. Got: {tool_response}"

    # Verify that the data was inserted into the database
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE id = 3")
    result = cursor.fetchone()
    conn.close()

    assert result is not None, "No data inserted into the database."
    assert result == (3, "Data Structures", "Computer Science", 4), f"Inserted data does not match. Got: {result}"


@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping MCP client tests in CI environment due to unknown issue executing npx."
)
@pytest.mark.asyncio
async def test_call_tool_write_query_invalid(mcp_client_manager, temp_db_path):
    """
    Test calling the 'write_query' tool with an invalid SQL statement.

    Args:
        mcp_client_manager (MCPClient): Instance of MCPClient.
        temp_db_path (str): Path to the temporary SQLite database.
    """
    # Discover tools
    tools = await mcp_client_manager.get_tools("FilesystemAgent")
    write_query_tool = next((tool for tool in tools if tool.name == "write_query"), None)
    assert write_query_tool is not None, "'write_query' tool not found."

    # Define an invalid SQL INSERT query for testing (typo in INSERT)
    invalid_sql_insert = "INSER INTO courses (id, name, department, credits) VALUES (4, 'Algorithms', 'Computer Science', 4)"
    arguments = {"query": invalid_sql_insert}

    # Call the tool and expect an exception due to invalid SQL syntax
    with pytest.raises(RuntimeError) as exc_info:
        await mcp_client_manager.call_tool(write_query_tool, arguments)

    # assert "syntax error" in str(exc_info.value).lower(), "Expected a syntax error in the tool response."


@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping MCP client tests in CI environment due to unknown issue executing npx."
)
@pytest.mark.asyncio
async def test_tool_caching(mcp_client_manager):
    """
    Test that tools are cached after the first discovery to prevent redundant MCP server processes.

    Args:
        mcp_client_manager (MCPClient): Instance of MCPClient.
    """
    # Mock the discover_tools method to track its calls
    original_discover_tools = mcp_client_manager.discover_tools
    mcp_client_manager.discover_tools = AsyncMock(side_effect=original_discover_tools)

    # First call to get_tools (should trigger discovery)
    tools_first_call = await mcp_client_manager.get_tools("FilesystemAgent")
    assert mcp_client_manager.discover_tools.call_count == 1, "discover_tools should be called once."

    # Second call to get_tools (should use cache)
    tools_second_call = await mcp_client_manager.get_tools("FilesystemAgent")
    assert mcp_client_manager.discover_tools.call_count == 1, "discover_tools should not be called again due to caching."

    # Verify that both calls return the same tools
    assert tools_first_call == tools_second_call, "Cached tools do not match the initially discovered tools."
