import pytest
import asyncio
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
async def test_initialize_and_list_tools(mcp_client_manager):
    """Test initialization and listing tools."""
    responses = await mcp_client_manager.initialize_and_list_tools()
    assert responses is not None, "Responses should not be None"
    assert any("tools" in response.get("result", {}) for response in responses), "Tools should be listed"
