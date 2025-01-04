# tests/test_agent_builder.py

import requests
import pytest
from unittest.mock import patch, Mock
from swarm.agent.agent_builder import build_agent_with_mcp_tools
from swarm.types import Agent, Tool
import logging

@pytest.fixture
def mcp_config():
    """
    Provides a sample MCP configuration for testing.
    """
    return {
        'agentName': 'MCPAgent',
        'instructions': 'You are an MCP-enabled agent.',
        'mcpServers': {
            'test_server': {
                'tools': [
                    {'description': 'Test Tool 1', 'endpoint': 'http://mock-mcp-server/tool1', 'name': 'tool1'},
                    {'description': 'Test Tool 2', 'endpoint': 'http://mock-mcp-server/tool2', 'name': 'tool2'}
                ]
            }
        }
    }

@patch('swarm.agent.agent_builder.create_tool_function')
def test_build_agent_with_tools(mock_create_tool_function, mcp_config):
    '''
    Test building an Agent with MCP tools.
    '''
    # Define mock tool functions that accept **kwargs
    def mock_tool1(**kwargs):
        return 'Mock Tool 1 Success'
    def mock_tool2(**kwargs):
        return 'Mock Tool 2 Success'

    # Set the side_effect to return these functions
    mock_create_tool_function.side_effect = [mock_tool1, mock_tool2]

    # Build the agent with MCP tools
    agent = build_agent_with_mcp_tools(mcp_config)

    # Assertions to ensure the agent is built correctly
    assert isinstance(agent, Agent), "Built object should be an instance of Agent."
    assert agent.name == 'MCPAgent', "Agent name mismatch."
    assert agent.instructions == 'You are an MCP-enabled agent.', "Agent instructions mismatch."
    assert len(agent.functions) == 2, "Agent should have two tools registered."

    # Check each tool
    tool1 = next((tool for tool in agent.functions if tool.name == 'tool1'), None)
    tool2 = next((tool for tool in agent.functions if tool.name == 'tool2'), None)

    assert tool1 is not None, "'tool1' should be registered."
    assert tool2 is not None, "'tool2' should be registered."

    # Verify tool descriptions
    assert tool1.description == 'Test Tool 1', "Tool1 description mismatch."
    assert tool2.description == 'Test Tool 2', "Tool2 description mismatch."

    # Verify that the tool functions are callable
    assert callable(tool1.func), "Tool1.func should be callable."
    assert callable(tool2.func), "Tool2.func should be callable."

    # Test the tool functions
    assert tool1.func() == 'Mock Tool 1 Success', "Tool1.func did not return expected result."
    assert tool2.func() == 'Mock Tool 2 Success', "Tool2.func did not return expected result."

@patch('swarm.agent.agent_builder.requests.post')
def test_tool_function_execution_success(mock_post, mcp_config):
    '''
    Test successful execution of a tool function.
    '''
    # Setup the mock response for a successful tool execution
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'result': 'Success'}
    mock_post.return_value = mock_response

    # Build the agent with tools
    agent = build_agent_with_mcp_tools(mcp_config)

    # Find 'tool1' and execute it
    tool1 = next((tool for tool in agent.functions if tool.name == 'tool1'), None)
    assert tool1 is not None, "'tool1' should be registered."

    result = tool1.func(query="SELECT * FROM courses LIMIT 1")
    assert result == 'Success', "Tool1.func should return 'Success'."

    # Verify that the POST request was called correctly
    mock_post.assert_called_with('http://mock-mcp-server/tool1', json={'query': "SELECT * FROM courses LIMIT 1"}, timeout=10)

@patch('swarm.agent.agent_builder.requests.post')
def test_tool_function_execution_failure(mock_post, mcp_config):
    '''
    Test execution of a tool function when MCP server responds with an error.
    '''
    # Setup the mock response for a failed tool execution
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = 'Internal Server Error'
    mock_post.return_value = mock_response

    # Build the agent with tools
    agent = build_agent_with_mcp_tools(mcp_config)

    # Find 'tool2' and execute it
    tool2 = next((tool for tool in agent.functions if tool.name == 'tool2'), None)
    assert tool2 is not None, "'tool2' should be registered."

    result = tool2.func(query="SELECT * FROM courses LIMIT 1")
    expected_error = 'MCP server responded with status 500: Internal Server Error'
    assert result == expected_error, "Tool2.func should return the error message."

    # Verify that the POST request was called correctly
    mock_post.assert_called_with('http://mock-mcp-server/tool2', json={'query': "SELECT * FROM courses LIMIT 1"}, timeout=10)

@patch('swarm.agent.agent_builder.requests.post')
def test_tool_function_exception(mock_post, mcp_config):
    '''
    Test execution of a tool function when an exception occurs during the request.
    '''
    # Setup the mock to raise a RequestException
    mock_post.side_effect = requests.exceptions.RequestException('Connection Error')

    # Build the agent with tools
    agent = build_agent_with_mcp_tools(mcp_config)

    # Find 'tool1' and execute it
    tool1 = next((tool for tool in agent.functions if tool.name == 'tool1'), None)
    assert tool1 is not None, "'tool1' should be registered."

    result = tool1.func(query="SELECT * FROM courses LIMIT 1")
    expected_error = "HTTP request failed for tool 'tool1': Connection Error"
    assert result == expected_error, "Tool1.func should return the HTTP error message."

    # Verify that the POST request was called correctly
    mock_post.assert_called_with('http://mock-mcp-server/tool1', json={'query': "SELECT * FROM courses LIMIT 1"}, timeout=10)

def test_build_agent_with_invalid_tool_config(mcp_config, caplog):
    '''
    Test that tools with missing configurations are skipped and warnings are logged.
    '''
    # Remove the endpoint from one of the tools
    del mcp_config['mcpServers']['test_server']['tools'][1]['endpoint']

    with caplog.at_level(logging.WARNING):
        agent = build_agent_with_mcp_tools(mcp_config)

    # Check that only one tool is registered
    assert len(agent.functions) == 1, "Only one tool should be registered due to missing endpoint."

    # Verify that the correct warning was logged
    assert "Tool 'tool2' in server 'test_server' lacks an endpoint. Skipping." in caplog.text
