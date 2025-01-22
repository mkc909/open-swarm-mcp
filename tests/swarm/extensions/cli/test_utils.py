import pytest
from unittest.mock import patch
from src.swarm.extensions.cli.utils import (
    find_project_root,
    display_message,
    prompt_user,
    validate_input,
    log_and_exit
)

def test_find_project_root(monkeypatch):
    # Mock os.path.exists to return True when checking for the marker
    monkeypatch.setattr('os.path.exists', lambda x: True)
    # Mock os.path.dirname to navigate up one directory
    monkeypatch.setattr('os.path.dirname', lambda x: '/'.join(x.split('/')[:-1]))
    
    path = '/some/path/to/project/src'
    marker = '.git'
    expected = '/some/path/to/project/src'
    
    result = find_project_root(path, marker)
    
    assert result == expected

def test_display_message(capfd, monkeypatch):
    message = "Test message"
    # Mock color_text to return the message without modification
    monkeypatch.setattr('src.swarm.extensions.cli.utils.color_text', lambda msg, color: msg)
    
    display_message(message, 'info')
    
    captured = capfd.readouterr()
    assert message in captured.out

def test_prompt_user(monkeypatch):
    user_input = 'user response'
    # Mock input to return predefined user input
    monkeypatch.setattr('builtins.input', lambda x: user_input)
    
    result = prompt_user('Enter something')
    assert result == user_input

def test_validate_input_valid():
    valid_options = ['yes', 'no']
    user_input = 'yes'
    result = validate_input(user_input, valid_options)
    assert result == user_input

def test_validate_input_invalid_with_default(monkeypatch):
    valid_options = ['yes', 'no']
    user_input = 'maybe'
    default = 'no'
    
    # Mock display_message to do nothing
    monkeypatch.setattr('src.swarm.extensions.cli.utils.display_message', lambda msg, msg_type: None)
    
    result = validate_input(user_input, valid_options, default=default)
    assert result == default

def test_validate_input_invalid_no_default(monkeypatch):
    valid_options = ['yes', 'no']
    user_input = 'maybe'
    
    # Mock display_message to do nothing
    monkeypatch.setattr('src.swarm.extensions.cli.utils.display_message', lambda msg, msg_type: None)
    
    with pytest.raises(ValueError):
        validate_input(user_input, valid_options)

def test_log_and_exit(monkeypatch):
    message = "Error occurred"
    # Mock display_message to do nothing
    monkeypatch.setattr('src.swarm.extensions.cli.utils.display_message', lambda msg, msg_type: None)
    # Mock sys.exit to raise an exception instead of exiting
    monkeypatch.setattr('src.swarm.extensions.cli.utils.sys.exit', lambda x: (_ for _ in ()).throw(SystemExit(x)))
    # Mock logger.error to do nothing
    monkeypatch.setattr('src.swarm.extensions.cli.utils.logger.error', lambda msg: None)
    
    with pytest.raises(SystemExit) as e:
        log_and_exit(message, code=1)
    
    assert e.value.code == 1