# tests/test_rest_mode.py

import os
import json
from unittest.mock import patch, Mock
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from open_swarm_mcp.rest_mode.views import chat_completions

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
        'model': 'default',
        'messages': [
            {'role': 'user', 'content': 'hi'}
        ]
    }
    with patch('open_swarm_mcp.rest_mode.views.run_swarm_sync') as mock_run_swarm_sync:
        # Mock the Swarm.run response
        mock_run_swarm_sync.return_value = {
            'messages': [
                {'role': 'assistant', 'content': "Hello! I'm Dilbert."}
            ]
        }
        response = client.post(url, data, format='json')
        assert response.status_code == 200
        assert response.json() == {
            'messages': [
                {'role': 'assistant', 'content': "Hello! I'm Dilbert."}
            ]
        }

@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Skipping test because OPENAI_API_KEY is not set"
)
async def test_swarm_execution():
    '''
    Test the swarm_execution function to ensure it executes the Swarm correctly.
    '''
    with patch('open_swarm_mcp.rest_mode.views.run_swarm_sync') as mock_run_swarm_sync:
        # Mock the Swarm.run response
        mock_run_swarm_sync.return_value = {
            'messages': [
                {'role': 'assistant', 'content': "Hello! I'm Dilbert."}
            ]
        }

        # Mock the request object
        request = Mock()
        request.method = 'POST'
        request.body = json.dumps({
            'model': 'default',
            'messages': [{'role': 'user', 'content': 'hi'}]
        })

        # Call the view function
        response = await chat_completions(request)
        assert response.status_code == 200
        assert response.json() == {
            'messages': [
                {'role': 'assistant', 'content': "Hello! I'm Dilbert."}
            ]
        }
