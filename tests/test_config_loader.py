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
    LLM_PROVIDER_API_KEY_MAP,
)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Test data
SAMPLE_CONFIG = {
    'llm': {
        'provider': 'openai',
        'model': 'gpt-4',
        'temperature': 0.2,
    },
    'mcpServers': {
        'brave-search': {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-brave-search'],
            'env': {
                'BRAVE_API_KEY': 'dummy_brave_key',
            },
        },
        'sqlite': {
            'command': 'uvx',
            'args': ['mcp-server-sqlite', '--db-path', 'test.db'],
        },
    },
}

# Test: load_server_config
@patch('builtins.open', mock_open(read_data=json.dumps(SAMPLE_CONFIG)))
@patch('os.path.exists', return_value=True)
def test_load_server_config_success(mock_exists):
    '''
    Test loading a valid configuration file.
    '''
    logger.debug('Starting test_load_server_config_success')
    logger.debug(f'Mocking os.path.exists to return True for dummy_path.json')
    logger.debug(f'Mocking file content: {json.dumps(SAMPLE_CONFIG)}')

    config = load_server_config('dummy_path.json')
    logger.debug(f'Loaded config: {config}')

    assert config == SAMPLE_CONFIG, 'Loaded config does not match expected SAMPLE_CONFIG'
    logger.debug('Test passed: Config loaded successfully')

def test_load_server_config_file_not_found():
    '''
    Test loading a configuration file that does not exist.
    '''
    logger.debug('Starting test_load_server_config_file_not_found')
    logger.debug('Expecting FileNotFoundError for nonexistent_path.json')

    with pytest.raises(FileNotFoundError) as exc_info:
        load_server_config('nonexistent_path.json')
    
    assert 'Configuration file not found at nonexistent_path.json' in str(exc_info.value), 'Error message does not match expected'
    logger.debug('Test passed: FileNotFoundError raised correctly')

@patch('builtins.open', mock_open(read_data='invalid_json'))
@patch('os.path.exists', return_value=True)
def test_load_server_config_invalid_json(mock_exists):
    '''
    Test loading a configuration file with invalid JSON.
    '''
    logger.debug('Starting test_load_server_config_invalid_json')
    logger.debug(f'Mocking os.path.exists to return True for invalid_path.json')
    logger.debug('Mocking file content: invalid_json')

    with pytest.raises(json.JSONDecodeError):
        load_server_config('invalid_path.json')
    
    logger.debug('Test passed: JSONDecodeError raised correctly')

# Test: validate_api_keys
def test_validate_api_keys_success():
    '''
    Test validating API keys when all required keys are present.
    '''
    logger.debug('Starting test_validate_api_keys_success')
    config = SAMPLE_CONFIG.copy()
    logger.debug(f'Initial config: {config}')

    with patch.dict('os.environ', {'OPENAI_API_KEY': 'dummy_openai_key'}):
        logger.debug('Mocking environment variables: OPENAI_API_KEY=dummy_openai_key')
        updated_config = validate_api_keys(config)
        logger.debug(f'Updated config: {updated_config}')

        assert updated_config['llm']['api_key'] == 'dummy_openai_key', 'LLM API key not set correctly'
        assert updated_config['mcpServers']['brave-search']['env']['BRAVE_API_KEY'] == 'dummy_brave_key', 'BRAVE_API_KEY not set correctly'
        logger.debug('Test passed: API keys validated successfully')

def test_validate_api_keys_missing_llm_key():
    '''
    Test validating API keys when the LLM API key is missing.
    '''
    logger.debug('Starting test_validate_api_keys_missing_llm_key')
    config = SAMPLE_CONFIG.copy()
    logger.debug(f'Initial config: {config}')

    with patch.dict('os.environ', {}, clear=True):
        logger.debug('Mocking empty environment variables')
        with pytest.raises(ValueError) as exc_info:
            validate_api_keys(config)
        
        assert 'LLM API Key is missing' in str(exc_info.value), 'Error message does not match expected'
        logger.debug('Test passed: ValueError raised correctly for missing LLM API key')

def test_validate_api_keys_missing_server_key():
    '''
    Test validating API keys when a server API key is missing.
    '''
    logger.debug('Starting test_validate_api_keys_missing_server_key')
    config = SAMPLE_CONFIG.copy()
    config['mcpServers']['brave-search']['env']['BRAVE_API_KEY'] = ''
    logger.debug(f'Modified config: {config}')

    with patch.dict('os.environ', {'OPENAI_API_KEY': 'dummy_openai_key'}, clear=True):
        logger.debug('Mocking environment variables: OPENAI_API_KEY=dummy_openai_key')
        with pytest.raises(ValueError) as exc_info:
            validate_api_keys(config)
        
        assert 'Environment variable \'BRAVE_API_KEY\' for server \'brave-search\' is missing' in str(exc_info.value), 'Error message does not match expected'
        logger.debug('Test passed: ValueError raised correctly for missing server API key')

# Test: are_required_mcp_servers_running
def test_are_required_mcp_servers_running_all_present():
    '''
    Test checking required MCP servers when all are configured.
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

def test_are_required_mcp_servers_running_missing_servers():
    '''
    Test checking required MCP servers when some are missing.
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

def test_are_required_mcp_servers_running_empty_config():
    '''
    Test checking required MCP servers when the configuration is empty.
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