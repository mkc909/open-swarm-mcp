'''
Tests for src/open_swarm_mcp/config/config_loader.py
'''

import pytest
import os
import json
import logging
from unittest.mock import patch, mock_open
from open_swarm_mcp.config.config_loader import (
    load_server_config,
    validate_api_keys,
    are_required_mcp_servers_running,
    get_llm_provider  # Included if needed for further tests
)

# Configure logger for the test module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

# Sample configuration matching 'mcp_server_config.json'
SAMPLE_CONFIG = {
    'llm_providers': {
        'default': {
            'provider': 'openai',
            'model': 'gpt-4',
            'base_url': 'https://api.openai.com/v1',
            'api_key': '${OPENAI_API_KEY}',
            'temperature': 0.2,
        },
        'grok': {
            'provider': 'openai',
            'model': 'grok-2-1212',
            'base_url': 'https://api.x.ai/v1',
            'api_key': '${XAI_API_KEY}',
            'temperature': 0.0,
        },
        'ollama': {
            'provider': 'ollama',
            'model': 'ollama-model',
            'base_url': 'http://localhost:11434/',
            'api_key': '',
            'temperature': 0.0,
        },
        'mock': {
            'provider': 'mock',
            'model': 'mock-model',
            'base_url': 'http://mock-llm.com/api',
            'api_key': '',
            'temperature': 0.0,
        }
    },
    'mcpServers': {
        'brave-search': {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-brave-search'],
            'env': {
                'BRAVE_API_KEY': '${BRAVE_API_KEY}'
            }
        },
        'sqlite': {
            'command': 'uvx',
            'args': ['mcp-server-sqlite', '--db-path', 'test.db'],
            'env': {}
        },
        'filesystem': {
            'command': 'bash',
            'args': [
                "-c",
                "command -v mcp-filesystem-server >/dev/null 2>&1 || go install github.com/mark3labs/mcp-filesystem-server@latest && ~/go/bin/mcp-filesystem-server $(echo $ALLOWED_PATHS | tr ',' ' ')"
            ],
            'env': {
                'ALLOWED_PATHS': '${ALLOWED_PATHS}'
            }
        }
    },
}

# Test: load_server_config_success
@patch('builtins.open', mock_open(read_data=json.dumps(SAMPLE_CONFIG)))
@patch('os.path.exists', return_value=True)
@patch.dict(os.environ, {
    'OPENAI_API_KEY': 'dummy_openai_key',
    'XAI_API_KEY': 'dummy_xai_key',
    'BRAVE_API_KEY': 'dummy_brave_key',
    'ALLOWED_PATHS': '/path/to/allowed1,/path/to/allowed2'
}, clear=True)
def test_load_server_config_success(mock_exists):
    '''
    Test loading a valid configuration file with all required environment variables set.
    Ensures that placeholders are correctly resolved.
    '''
    logger.debug('Starting test_load_server_config_success')
    logger.debug(f'Mocking os.path.exists to return True for dummy_path.json')
    logger.debug(f'Mocking file content: {json.dumps(SAMPLE_CONFIG)}')

    try:
        config = load_server_config('dummy_path.json')
        logger.debug(f'Loaded config: {config}')

        # Expected config with placeholders resolved
        expected_config = {
            'llm_providers': {
                'default': {
                    'provider': 'openai',
                    'model': 'gpt-4',
                    'base_url': 'https://api.openai.com/v1',
                    'api_key': 'dummy_openai_key',
                    'temperature': 0.2,
                },
                'grok': {
                    'provider': 'openai',
                    'model': 'grok-2-1212',
                    'base_url': 'https://api.x.ai/v1',
                    'api_key': 'dummy_xai_key',
                    'temperature': 0.0,
                },
                'ollama': {
                    'provider': 'ollama',
                    'model': 'ollama-model',
                    'base_url': 'http://localhost:11434/',
                    'api_key': '',
                    'temperature': 0.0,
                },
                'mock': {
                    'provider': 'mock',
                    'model': 'mock-model',
                    'base_url': 'http://mock-llm.com/api',
                    'api_key': '',
                    'temperature': 0.0,
                }
            },
            'mcpServers': {
                'brave-search': {
                    'command': 'npx',
                    'args': ['-y', '@modelcontextprotocol/server-brave-search'],
                    'env': {
                        'BRAVE_API_KEY': 'dummy_brave_key'
                    }
                },
                'sqlite': {
                    'command': 'uvx',
                    'args': ['mcp-server-sqlite', '--db-path', 'test.db'],
                    'env': {}
                },
                'filesystem': {
                    'command': 'bash',
                    'args': [
                        "-c",
                        "command -v mcp-filesystem-server >/dev/null 2>&1 || go install github.com/mark3labs/mcp-filesystem-server@latest && ~/go/bin/mcp-filesystem-server $(echo $ALLOWED_PATHS | tr ',' ' ')"
                    ],
                    'env': {
                        'ALLOWED_PATHS': '/path/to/allowed1,/path/to/allowed2'
                    }
                }
            },
        }

        assert config == expected_config, 'Loaded config does not match expected_config'
        logger.debug('Test passed: Config loaded and placeholders resolved successfully')
    except Exception as e:
        logger.error(f'Test failed with exception: {e}', exc_info=True)
        pytest.fail(f'Test failed with exception: {e}')

# Test: load_server_config_file_not_found
@patch('os.path.exists', return_value=False)
def test_load_server_config_file_not_found(mock_exists):
    '''
    Test loading a configuration file that does not exist.
    Expects a FileNotFoundError.
    '''
    logger.debug('Starting test_load_server_config_file_not_found')
    logger.debug('Mocking os.path.exists to return False for nonexistent_path.json')

    with pytest.raises(FileNotFoundError) as exc_info:
        load_server_config('nonexistent_path.json')
    
    assert 'Configuration file not found at nonexistent_path.json' in str(exc_info.value), 'Error message does not match expected'
    logger.debug('Test passed: FileNotFoundError raised correctly for missing configuration file')

# Test: load_server_config_invalid_json
@patch('builtins.open', mock_open(read_data='invalid_json'))
@patch('os.path.exists', return_value=True)
def test_load_server_config_invalid_json(mock_exists):
    '''
    Test loading a configuration file with invalid JSON content.
    Expects a JSONDecodeError.
    '''
    logger.debug('Starting test_load_server_config_invalid_json')
    logger.debug('Mocking os.path.exists to return True for invalid_path.json')
    logger.debug('Mocking file content: invalid_json')

    with pytest.raises(json.JSONDecodeError):
        load_server_config('invalid_path.json')
    
    logger.debug('Test passed: JSONDecodeError raised correctly for invalid JSON content')

# Test: validate_api_keys_success
@patch.dict(os.environ, {
    'OPENAI_API_KEY': 'dummy_openai_key',
    'XAI_API_KEY': 'dummy_xai_key',
    'BRAVE_API_KEY': 'dummy_brave_key',
    'ALLOWED_PATHS': '/path/to/allowed1,/path/to/allowed2'
}, clear=True)
def test_validate_api_keys_success():
    '''
    Test validating API keys when all required keys are present.
    Ensures that no ValueError is raised and keys are correctly set.
    '''
    logger.debug('Starting test_validate_api_keys_success')
    config = {
        'llm_providers': {
            'default': {
                'provider': 'openai',
                'model': 'gpt-4',
                'base_url': 'https://api.openai.com/v1',
                'api_key': 'dummy_openai_key',
                'temperature': 0.2,
            },
            'grok': {
                'provider': 'openai',
                'model': 'grok-2-1212',
                'base_url': 'https://api.x.ai/v1',
                'api_key': 'dummy_xai_key',
                'temperature': 0.0,
            },
            'ollama': {
                'provider': 'ollama',
                'model': 'ollama-model',
                'base_url': 'http://localhost:11434/',
                'api_key': '',
                'temperature': 0.0,
            },
            'mock': {
                'provider': 'mock',
                'model': 'mock-model',
                'base_url': 'http://mock-llm.com/api',
                'api_key': '',
                'temperature': 0.0,
            }
        },
        'mcpServers': {
            'brave-search': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-brave-search'],
                'env': {
                    'BRAVE_API_KEY': 'dummy_brave_key'
                }
            },
            'sqlite': {
                'command': 'uvx',
                'args': ['mcp-server-sqlite', '--db-path', 'test.db'],
                'env': {}
            },
            'filesystem': {
                'command': 'bash',
                'args': [
                    "-c",
                    "command -v mcp-filesystem-server >/dev/null 2>&1 || go install github.com/mark3labs/mcp-filesystem-server@latest && ~/go/bin/mcp-filesystem-server $(echo $ALLOWED_PATHS | tr ',' ' ')"
                ],
                'env': {
                    'ALLOWED_PATHS': '/path/to/allowed1,/path/to/allowed2'
                }
            }
        },
    }
    logger.debug(f'Initial config: {config}')

    try:
        updated_config = validate_api_keys(config, 'default')  # Selecting 'default' LLM profile
        logger.debug(f'Updated config after validation: {updated_config}')

        assert updated_config['llm_providers']['default']['api_key'] == 'dummy_openai_key', 'LLM API key not set correctly'
        assert updated_config['mcpServers']['brave-search']['env']['BRAVE_API_KEY'] == 'dummy_brave_key', 'BRAVE_API_KEY not set correctly'
        logger.debug('Test passed: API keys validated successfully with all required keys present')
    except Exception as e:
        logger.error(f'Test failed with exception: {e}', exc_info=True)
        pytest.fail(f'Test failed with exception: {e}')

# # Test: validate_api_keys_missing_llm_key
# @patch.dict(os.environ, {
#     'XAI_API_KEY': 'dummy_xai_key',
#     'BRAVE_API_KEY': 'dummy_brave_key',
#     'ALLOWED_PATHS': '/path/to/allowed1,/path/to/allowed2'
# }, clear=True)  # Missing 'OPENAI_API_KEY'
# def test_validate_api_keys_missing_llm_key():
#     '''
#     Test validating API keys when the LLM API key is missing.
#     Expects a ValueError indicating the missing API key.
#     '''
#     logger.debug('Starting test_validate_api_keys_missing_llm_key')
#     config = {
#         'llm_providers': {
#             'default': {
#                 'provider': 'openai',
#                 'model': 'gpt-4',
#                 'base_url': 'https://api.openai.com/v1',
#                 'api_key': '${OPENAI_API_KEY}',  # Placeholder
#                 'temperature': 0.2,
#             },
#             'grok': {
#                 'provider': 'openai',
#                 'model': 'grok-2-1212',
#                 'base_url': 'https://api.x.ai/v1',
#                 'api_key': 'dummy_xai_key',
#                 'temperature': 0.0,
#             },
#             'ollama': {
#                 'provider': 'ollama',
#                 'model': 'ollama-model',
#                 'base_url': 'http://localhost:11434/',
#                 'api_key': '',
#                 'temperature': 0.0,
#             },
#             'mock': {
#                 'provider': 'mock',
#                 'model': 'mock-model',
#                 'base_url': 'http://mock-llm.com/api',
#                 'api_key': '',
#                 'temperature': 0.0,
#             }
#         },
#         'mcpServers': {
#             'brave-search': {
#                 'command': 'npx',
#                 'args': ['-y', '@modelcontextprotocol/server-brave-search'],
#                 'env': {
#                     'BRAVE_API_KEY': 'dummy_brave_key'
#                 }
#             },
#             'sqlite': {
#                 'command': 'uvx',
#                 'args': ['mcp-server-sqlite', '--db-path', 'test.db'],
#                 'env': {}
#             },
#             'filesystem': {
#                 'command': 'bash',
#                 'args': [
#                     "-c",
#                     "command -v mcp-filesystem-server >/dev/null 2>&1 || go install github.com/mark3labs/mcp-filesystem-server@latest && ~/go/bin/mcp-filesystem-server $(echo $ALLOWED_PATHS | tr ',' ' ')"
#                 ],
#                 'env': {
#                     'ALLOWED_PATHS': '/path/to/allowed1,/path/to/allowed2'
#                 }
#             }
#         },
#     }
#     logger.debug(f'Initial config: {config}')

#     try:
#         with pytest.raises(ValueError) as exc_info:
#             validate_api_keys(config, 'default')  # Selecting 'default' LLM profile with missing API key
        
#         expected_error_msg = "API key for provider 'openai' in LLM profile 'default' is missing."
#         assert expected_error_msg in str(exc_info.value), 'Error message does not match expected'
#         logger.debug('Test passed: ValueError raised correctly for missing LLM API key')
#     except Exception as e:
#         logger.error(f'Test failed with exception: {e}', exc_info=True)
#         pytest.fail(f'Test failed with exception: {e}')

# Test: validate_api_keys_missing_server_key
@patch.dict(os.environ, {
    'OPENAI_API_KEY': 'dummy_openai_key',
    'XAI_API_KEY': 'dummy_xai_key',
    'ALLOWED_PATHS': '/path/to/allowed1,/path/to/allowed2'
}, clear=True)  # Missing 'BRAVE_API_KEY'
def test_validate_api_keys_missing_server_key():
    '''
    Test validating API keys when a server API key is missing.
    Expects a ValueError indicating the missing server API key.
    '''
    logger.debug('Starting test_validate_api_keys_missing_server_key')
    config = {
        'llm_providers': {
            'grok': {
                'provider': 'openai',
                'model': 'grok-2-1212',
                'base_url': 'https://api.x.ai/v1',
                'api_key': 'dummy_xai_key',
                'temperature': 0.0,
            }
        },
        'mcpServers': {
            'brave-search': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-brave-search'],
                'env': {
                    'BRAVE_API_KEY': ''  # Missing API key
                }
            },
            'sqlite': {
                'command': 'uvx',
                'args': ['mcp-server-sqlite', '--db-path', 'test.db'],
                'env': {}
            },
            'filesystem': {
                'command': 'bash',
                'args': [
                    "-c",
                    "command -v mcp-filesystem-server >/dev/null 2>&1 || go install github.com/mark3labs/mcp-filesystem-server@latest && ~/go/bin/mcp-filesystem-server $(echo $ALLOWED_PATHS | tr ',' ' ')"
                ],
                'env': {
                    'ALLOWED_PATHS': '/path/to/allowed1,/path/to/allowed2'
                }
            }
        },
    }
    logger.debug(f'Modified config with missing BRAVE_API_KEY: {config}')

    try:
        with pytest.raises(ValueError) as exc_info:
            validate_api_keys(config, 'grok')  # Selecting 'grok' LLM profile with missing server API key
        
        expected_error_msg = "Environment variable 'BRAVE_API_KEY' for server 'brave-search' is missing."
        assert expected_error_msg in str(exc_info.value), 'Error message does not match expected'
        logger.debug('Test passed: ValueError raised correctly for missing server API key')
    except Exception as e:
        logger.error(f'Test failed with exception: {e}', exc_info=True)
        pytest.fail(f'Test failed with exception: {e}')

# Test: are_required_mcp_servers_running_all_present
def test_are_required_mcp_servers_running_all_present():
    '''
    Test checking required MCP servers when all are configured.
    Ensures that the function returns True with no missing servers.
    '''
    logger.debug('Starting test_are_required_mcp_servers_running_all_present')
    config = SAMPLE_CONFIG.copy()
    required_servers = ['brave-search', 'sqlite']
    logger.debug(f'Required servers: {required_servers}')

    result, missing_servers = are_required_mcp_servers_running(required_servers, config)
    logger.debug(f'Result: {result}, Missing servers: {missing_servers}')

    assert result is True, 'Expected all servers to be present'
    assert missing_servers == [], 'Expected no missing servers'
    logger.debug('Test passed: All required servers are present')

# Test: are_required_mcp_servers_running_missing_servers
def test_are_required_mcp_servers_running_missing_servers():
    '''
    Test checking required MCP servers when some are missing.
    Ensures that the function returns False with the correct missing servers listed.
    '''
    logger.debug('Starting test_are_required_mcp_servers_running_missing_servers')
    config = SAMPLE_CONFIG.copy()
    required_servers = ['brave-search', 'missing-server']
    logger.debug(f'Required servers: {required_servers}')

    result, missing_servers = are_required_mcp_servers_running(required_servers, config)
    logger.debug(f'Result: {result}, Missing servers: {missing_servers}')

    assert result is False, 'Expected missing servers'
    assert missing_servers == ['missing-server'], 'Expected missing-server to be missing'
    logger.debug('Test passed: Missing servers detected correctly')

# Test: are_required_mcp_servers_running_empty_config
def test_are_required_mcp_servers_running_empty_config():
    '''
    Test checking required MCP servers when the configuration is empty.
    Ensures that the function returns False with all required servers listed as missing.
    '''
    logger.debug('Starting test_are_required_mcp_servers_running_empty_config')
    config = {}
    required_servers = ['brave-search']
    logger.debug(f'Required servers: {required_servers}')

    result, missing_servers = are_required_mcp_servers_running(required_servers, config)
    logger.debug(f'Result: {result}, Missing servers: {missing_servers}')

    assert result is False, 'Expected missing servers'
    assert missing_servers == ['brave-search'], 'Expected brave-search to be missing'
    logger.debug('Test passed: Missing servers detected correctly in empty config')
