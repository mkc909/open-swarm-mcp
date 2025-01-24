@pytest.mark.asyncio
async def test_sqlite_tool_discovery(sqlite_client):
    """Test tool discovery with sqlite-uvx MCP server."""
    tools = await sqlite_client.list_tools()
    assert tools is not None, "No tools discovered from sqlite-uvx server."
    assert len(tools) > 0, "Expected tools from sqlite-uvx server."


@pytest.mark.asyncio
async def test_everything_tool_discovery(everything_client):
    """Test tool discovery with everything MCP server."""
    tools = await everything_client.list_tools()
    assert tools is not None, "No tools discovered from everything server."
    assert len(tools) > 0, "Expected tools from everything server."


@pytest.mark.asyncio
async def test_sqlite_tool_execution(sqlite_client):
    """Test tool execution with sqlite-uvx MCP server."""
    tools = await sqlite_client.list_tools()
    assert "list_tables" in [tool.name for tool in tools], "list_tables tool not found in sqlite-uvx server."
    response = await sqlite_client._create_tool_callable("list_tables")()
    assert response is not None, "No response from list_tables tool."
    assert isinstance(response, list), "Expected list of tables."


@pytest.mark.asyncio
async def test_everything_tool_execution(everything_client):
    """Test tool execution with everything MCP server."""
    tools = await everything_client.list_tools()
    assert "search" in [tool.name for tool in tools], "search tool not found in everything server."
    response = await everything_client._create_tool_callable("search")(pattern="*.md")
    assert response is not None, "No response from search tool."
    assert isinstance(response, list), "Expected list of matching items."
