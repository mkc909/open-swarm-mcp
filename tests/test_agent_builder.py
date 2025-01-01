import logging
import pytest
from unittest.mock import patch, Mock
from swarm.agent.agent_builder import build_agent, build_agent_with_mcp_tools, create_tool_function
from swarm import Agent
import requests

@pytest.fixture
def basic_config():
    '''
    Provides a basic configuration without MCP servers.
    '''
    return {
        'agentName': 'TestAgent',
        'instructions': 'You are a test agent.'
    }

@pytest.fixture
def mcp_config():
    '''
    Provides a configuration with MCP servers and tools.
    '''
    return {
        'agentName': 'MCPAgent',
        'instructions': 'You are an MCP-enabled agent.',
        'mcpServers': {
            'test_server': {
                'tools': [
                    {
                        'name': 'tool1',
                        'description': 'Test Tool 1',
                        'endpoint': 'http://mock-mcp-server/tool1'
                    },
                    {
                        'name': 'tool2',
                        'description': 'Test Tool 2',
                        'endpoint': 'http://mock-mcp-server/tool2'
                    }
                ]
            }
        }
    }

def test_build_agent_without_tools(basic_config):
    '''
    Test building an Agent without any MCP tools.
    '''
    agent = build_agent(basic_config)
    assert isinstance(agent, Agent)
    assert agent.name == 'TestAgent'
    assert agent.instructions == 'You are a test agent.'
    assert len(agent.functions) == 0  # No tools should be registered

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

    agent = build_agent_with_mcp_tools(mcp_config)
    assert isinstance(agent, Agent)
    assert agent.name == 'MCPAgent'
    assert agent.instructions == 'You are an MCP-enabled agent.'
    assert len(agent.functions) == 2  # Two tools should be registered
    assert agent.functions[0] == mock_tool1
    assert agent.functions[1] == mock_tool2

    # Ensure create_tool_function was called correctly
    mock_create_tool_function.assert_any_call('tool1', 'Test Tool 1', 'http://mock-mcp-server/tool1')
    mock_create_tool_function.assert_any_call('tool2', 'Test Tool 2', 'http://mock-mcp-server/tool2')
    assert mock_create_tool_function.call_count == 2

@patch('requests.post')
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
    tool_function = agent.functions[0]  # tool1

    # Execute the tool function with arbitrary parameters
    result = tool_function(param1='value1', param2='value2')

    # Assertions
    mock_post.assert_called_once_with(
        'http://mock-mcp-server/tool1',
        json={'param1': 'value1', 'param2': 'value2'},
        timeout=10
    )
    assert result == 'Success'

@patch('requests.post')
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
    tool_function = agent.functions[0]  # tool1

    # Execute the tool function
    result = tool_function(param1='value1')

    # Assertions
    mock_post.assert_called_once_with(
        'http://mock-mcp-server/tool1',
        json={'param1': 'value1'},
        timeout=10
    )
    assert result == 'MCP server responded with status 500: Internal Server Error'

@patch('requests.post')
def test_tool_function_exception(mock_post, mcp_config):
    '''
    Test execution of a tool function when an exception occurs during the request.
    '''
    # Setup the mock to raise a RequestException
    mock_post.side_effect = requests.exceptions.RequestException('Connection Error')

    # Build the agent with tools
    agent = build_agent_with_mcp_tools(mcp_config)
    tool_function = agent.functions[0]  # tool1

    # Execute the tool function
    result = tool_function(param1='value1')

    # Assertions
    mock_post.assert_called_once_with(
        'http://mock-mcp-server/tool1',
        json={'param1': 'value1'},
        timeout=10
    )
    assert result == 'HTTP request failed for tool \'tool1\': Connection Error'

def test_create_tool_function_metadata(mcp_config):
    '''
    Test that the tool function has correct metadata.
    '''
    tool_name = 'tool1'
    tool_description = 'Test Tool 1'
    mcp_endpoint = 'http://mock-mcp-server/tool1'
    tool_function = create_tool_function(tool_name, tool_description, mcp_endpoint)
    assert tool_function.__name__ == 'tool1'
    assert tool_function.__doc__ == 'Test Tool 1'

def test_build_agent_with_invalid_tool_config(mcp_config, caplog):
    '''
    Test that tools with missing configurations are skipped and warnings are logged.
    '''
    # Remove the endpoint from one of the tools
    del mcp_config['mcpServers']['test_server']['tools'][1]['endpoint']

    with caplog.at_level(logging.WARNING):
        agent = build_agent_with_mcp_tools(mcp_config)
        assert len(agent.functions) == 1  # Only one valid tool should be registered
        assert agent.functions[0].__name__ == 'tool1'

        # Check that a warning was logged for the missing endpoint
        assert 'Tool \'tool2\' in server \'test_server\' lacks an endpoint. Skipping.' in caplog.text