import pytest
import asyncio
import os
from swarm.extensions.mcp.mcp_client import MCPClientManager

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
