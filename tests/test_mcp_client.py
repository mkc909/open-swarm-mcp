import pytest
import asyncio
import os
from swarm.extensions.mcp.mcp_client import MCPClientManager
from unittest.mock import AsyncMock, MagicMock

DB_PATH = "./artificial_university.db"

@pytest.fixture(scope="module")
def cleanup_database():
    """Fixture to ensure the database file is cleaned up after tests."""
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

@pytest.fixture
@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping test in CI environment due to potential environment variable interference."
)
def mcp_client_manager():
    """Fixture to provide an instance of MCPClientManager."""
    return MCPClientManager(
        command="npx",
        args=["-y", "mcp-server-sqlite-npx", DB_PATH],
        timeout=30
    )

@pytest.mark.asyncio
@pytest.mark.usefixtures("cleanup_database")
@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping test in CI environment due to potential environment variable interference."
)
async def test_initialize_and_list_tools(mcp_client_manager):
    """Test initialization and listing tools."""
    responses = await mcp_client_manager.initialize_and_list_tools()
    assert responses is not None, "Responses should not be None"
    assert any("tools" in response.get("result", {}) for response in responses), "Tools should be listed"

@pytest.mark.asyncio
@pytest.mark.usefixtures("cleanup_database")
@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping test in CI environment due to potential environment variable interference."
)
async def test_call_tool_read_query(mcp_client_manager):
    """Test calling a tool to execute a SELECT query."""
    await mcp_client_manager.initialize_and_list_tools()
    query = "SELECT * FROM courses LIMIT 1"
    responses = await mcp_client_manager.call_tool("read_query", {"query": query})
    assert responses is not None, "Responses should not be None"
    assert any("result" in response for response in responses), "Response should contain results"

# @pytest.mark.asyncio
# async def test_read_responses_timeout(mcp_client_manager, monkeypatch):
#     """Test timeout in _read_responses."""
#     mock_process = MagicMock()
#     mock_process.stdout = AsyncMock()
#     mock_process.stdout.read = AsyncMock(side_effect=asyncio.TimeoutError)

#     with pytest.raises(asyncio.TimeoutError):
#         await mcp_client_manager._read_responses(process=mock_process, count=1)

# @pytest.mark.asyncio
# async def test_read_responses_json_error(mcp_client_manager, monkeypatch):
#     """Test JSON decoding error in _read_responses."""
#     mock_process = MagicMock()
#     mock_process.stdout = AsyncMock()
#     mock_process.stdout.read = AsyncMock(return_value=b"{invalid json}")

#     responses = await mcp_client_manager._read_responses(process=mock_process, count=1)
#     assert responses == [], "Responses should be empty on JSON decode error."

# @pytest.mark.asyncio
# async def test_call_tool_invalid_arguments(mcp_client_manager):
#     """Test calling a tool with invalid arguments."""
#     await mcp_client_manager.initialize_and_list_tools()
#     invalid_arguments = {"invalid_key": "invalid_value"}
#     responses = await mcp_client_manager.call_tool("read_query", invalid_arguments)
#     assert responses is not None, "Responses should not be None even with invalid arguments."
#     assert any("error" in response for response in responses), "Error should be present in responses."

# @pytest.mark.asyncio
# @pytest.mark.usefixtures("cleanup_database")
# async def test_create_insert_select(mcp_client_manager):
#     """Test creating a table, inserting an entry, and selecting from it."""
#     await mcp_client_manager.initialize_and_list_tools()

#     # Create table
#     create_table_query = "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"
#     create_response = await mcp_client_manager.call_tool("write_query", {"query": create_table_query})
#     assert create_response is not None, "Create table response should not be None"

#     # Insert entry
#     insert_query = "INSERT INTO test_table (name) VALUES ('test_name')"
#     insert_response = await mcp_client_manager.call_tool("write_query", {"query": insert_query})
#     assert insert_response is not None, "Insert entry response should not be None"

#     # Select entry
#     select_query = "SELECT * FROM test_table"
#     select_response = await mcp_client_manager.call_tool("read_query", {"query": select_query})
#     assert select_response is not None, "Select response should not be None"
#     assert any("result" in response for response in select_response), "Response should contain results"
#     assert select_response[0]["result"][0]["name"] == "test_name", "Selected entry should match the inserted value"
