import os
import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from django.urls import reverse
from rest_framework.test import APIClient
from open_swarm_mcp.rest_mode.views import construct_openai_response, chat_completions

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.open_swarm_mcp.settings')

@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Skipping test because OPENAI_API_KEY is not set"
)
async def test_construct_openai_response():
    '''
    Test the construct_openai_response function to ensure it constructs a valid OpenAI-like response.
    '''
    # Mock the response object as a dictionary
    response = {
        "messages": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "Hello! I'm Dilbert."}
        ]
    }
    openai_model = 'gpt-3.5-turbo'
    result = construct_openai_response(response, openai_model)

    # Assertions to verify the response structure
    assert 'id' in result
    assert result['model'] == openai_model
    assert result['choices'][0]['message']['content'] == "Hello! I'm Dilbert."
    assert result['usage']['prompt_tokens'] > 0
    assert result['usage']['completion_tokens'] > 0
    assert result['usage']['total_tokens'] > 0

@pytest.mark.django_db
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Skipping test because OPENAI_API_KEY is not set"
)
def test_chat_completion_endpoint():
    '''
    Test the chat_completion endpoint to ensure it returns a valid response.
    '''
    client = APIClient()
    url = reverse('chat_completions')
    data = {
        'model': 'path_e_tech',
        'messages': [
            {'role': 'user', 'content': 'hi'}
        ]
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 200
    response_data = response.json()
    assert 'id' in response_data
    assert 'choices' in response_data
    assert len(response_data['choices']) > 0
    assert 'message' in response_data['choices'][0]

@pytest.mark.django_db
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Skipping test because OPENAI_API_KEY is not set"
)
def test_chat_completion_invalid_input():
    '''
    Test the chat_completion endpoint with invalid input (empty messages).
    '''
    client = APIClient()
    url = reverse('chat_completions')
    data = {
        'model': 'path_e_tech',
        'messages': []  # Empty messages
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['error'] == 'Messages are required'

@pytest.mark.asyncio
@patch('open_swarm_mcp.rest_mode.views.run_swarm_sync')
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Skipping test because OPENAI_API_KEY is not set"
)
async def test_swarm_execution(mock_run_swarm_sync):
    '''
    Test the swarm_execution function to ensure it executes the Swarm correctly.
    '''
    # Mock the helper function
    mock_run_swarm_sync.return_value = {'messages': [{'role': 'assistant', 'content': 'Hello!'}]}
    
    # Mock the request object
    request = MagicMock()
    request.method = 'POST'
    request.body = json.dumps({
        'model': 'path_e_tech',
        'messages': [{'role': 'user', 'content': 'hi'}]
    })
    
    # Call the view function
    result = await chat_completions(request)
    assert result.status_code == 200