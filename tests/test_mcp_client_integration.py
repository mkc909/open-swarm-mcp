import pytest
import asyncio
import os
from swarm.extensions.mcp_client import MCPClientManager

@pytest.fixture
@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping test in CI environment due to potential environment variable interference."
)
def mcp_client_manager():
    """Fixture to provide an instance of MCPClientManager."""
    return MCPClientManager(
        command="npx",
        args=["-y", "mcp-server-sqlite-npx", "./artificial_university.db"],
        timeout=30
    )

@pytest.mark.asyncio
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
