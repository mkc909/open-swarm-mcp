import os
import pytest
from swarm.extensions.mcp.mcp_client import MCPClientManager

@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping test in CI environment due to unknown issue executing npx."
)
@pytest.mark.asyncio
async def test_discover_tools():
    """Test the discover_tools method with real subprocess."""
    client = MCPClientManager(
        command="npx",
        args=["-y", "mcp-server-sqlite-npx", "./artificial_university.db"]
    )
    tools = await client.discover_tools()
    assert len(tools) > 0, "Expected tools to be discovered."
    assert any(tool.name == "read_query" for tool in tools), "Expected 'read_query' tool."


@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping test in CI environment due to unknown issue executing npx."
)
@pytest.mark.asyncio
async def test_call_tool():
    """Test calling a tool with real subprocess."""
    client = MCPClientManager(
        command="npx",
        args=["-y", "mcp-server-sqlite-npx", "./artificial_university.db"]
    )
    tools = await client.discover_tools()
    read_query_tool = next((tool for tool in tools if tool.name == "read_query"), None)
    assert read_query_tool, "Expected 'read_query' tool to be discovered."

    # Call the tool with a valid query
    result = await client.call_tool(read_query_tool, {"query": "SELECT * FROM courses LIMIT 1"})
    assert result, "Expected a result from the tool call."


# @pytest.mark.asyncio
# async def test_run_with_process():
#     """Test the _run_with_process method with real subprocess."""
#     client = MCPClientManager(
#         command="npx",
#         args=["-y", "mcp-server-sqlite-npx", "./artificial_university.db"]
#     )
#     requests = [{"id": 1, "method": "initialize"}]
#     responses = await client._run_with_process(requests)
#     assert len(responses) > 0, "Expected responses from the MCP server."
#     assert responses[0]["id"] == 1, "Expected response ID to match the request ID."
