import os
import json
import logging
from unittest import mock
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import pytest

logger = logging.getLogger(__name__)

class TestChat(APITestCase):
    """Tests for verifying stateless and stateful chat behavior."""

    def setUp(self):
        """Set up test environment, credentials, and mock BlueprintBase.run_with_context."""
        self.client = APIClient()
        self.chat_url = reverse('chat_completions')
        # Ensure authentication by setting API_AUTH_TOKEN and client credentials
        os.environ['API_AUTH_TOKEN'] = 'test-token-123'
        self.client.credentials(HTTP_AUTHORIZATION='Token test-token-123')
        # Ensure no previous stateful config interferes
        os.environ.pop('STATEFUL_CHAT_ID_PATH', None)
        # Patch the method to return a realistic mocked response
        from unittest.mock import patch
        self.patcher = patch(
            "swarm.extensions.blueprint.blueprint_base.BlueprintBase.run_with_context",
            side_effect=TestChat.mock_run_with_context
        )
        self.mock_run_with_context_method = self.patcher.start()

    @staticmethod
    def mock_run_with_context(messages, context_variables):
        """
        Mocks an LLM-style response including tool calls and agent handoff.
        """
        conversation_id = "mock_conversation_123"
        return {
            "id": "swarm-chat-completion-mock",
            "object": "chat.completion",
            "created": 1738714942,
            "model": "university",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "content": None,
                        "role": "assistant",
                        "tool_calls": [
                            {"id": "mock_tool_123", "function": {"name": "get_metadata", "arguments": "{}"}, "type": "function"}
                        ],
                        "sender": "TriageAgent"
                    },
                    "finish_reason": "stop"
                },
                {
                    "index": 1,
                    "message": {
                        "role": "tool",
                        "tool_call_id": "mock_tool_123",
                        "tool_name": "get_metadata",
                        "content": "{\"workspaceInfo\": {\"workspaceId\": \"T123456\", \"workspaceName\": \"ENAB101\"}}"
                    },
                    "finish_reason": "stop"
                },
                {
                    "index": 2,
                    "message": {
                        "content": "A tiny black speck,\nBuzzing through the summer air,\nLife's brief symphony.",
                        "role": "assistant",
                        "tool_calls": None,
                        "sender": "UniversityPoet"
                    },
                    "finish_reason": "stop"
                }
            ],
            "context_variables": {"active_agent_name": "UniversityPoet"},
            "conversation_id": conversation_id,
            "response": {
                "messages": [{"content": "Mocked response", "role": "assistant"}]
            }
        }

    @pytest.mark.skip(reason="Skipping auth tests for now")
    def test_stateless_chat(self):
        """Verify stateless mode returns responses without tracking history."""
        self.assertFalse('STATEFUL_CHAT_ID_PATH' in os.environ)
        response = self.client.post(self.chat_url, data={'message': 'Hello'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("choices", response.data)
        self.assertNotIn("conversation_id", response.data)

    @pytest.mark.skip(reason="Skipping auth tests for now")
    @mock.patch('redis.Redis')
    def test_stateful_chat(self, mock_redis):
        """Verify stateful chat tracks conversation ID and stores history."""
        os.environ['STATEFUL_CHAT_ID_PATH'] = "chat_id"
        mock_redis_instance = mock_redis.return_value
        initial_payload = {"chat_id": "abc123", "message": "Hello from stateful test"}
        response = self.client.post(self.chat_url, data=initial_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("conversation_id", response.data)
        self.assertEqual(response.data["conversation_id"], "abc123")
        followup_payload = {"chat_id": "abc123", "message": "How are you stored?"}
        response2 = self.client.post(self.chat_url, data=followup_payload, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn("conversation_id", response2.data)
        self.assertEqual(response2.data["conversation_id"], "abc123")
        self.assertTrue(mock_redis_instance.get.called or mock_redis_instance.set.called)

    @pytest.mark.skip(reason="Skipping auth tests for now")
    def test_jmespath_chat_id_extraction(self):
        """Verify JMESPath-based conversation ID extraction."""
        os.environ['STATEFUL_CHAT_ID_PATH'] = "messages[?role=='assistant'] | [-1].tool_calls[-1].id"
        payload = {
            "messages": [
                {"role": "assistant", "tool_calls": [{"id": "jmespath_456"}]}
            ],
            "message": "Extract me"
        }
        response = self.client.post(self.chat_url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("conversation_id", response.data)
        self.assertEqual(response.data["conversation_id"], "jmespath_456")

    @pytest.mark.skip(reason="Skipping auth tests for now")
    @mock.patch('redis.Redis')
    def test_database_queries_optimized(self, mock_redis):
        """Ensure database queries are minimized under stateful mode."""
        os.environ['STATEFUL_CHAT_ID_PATH'] = "conv"
        mock_redis_instance = mock_redis.return_value
        payload = {"conv": "optimized123", "message": "Testing DB queries..."}
        response = self.client.post(self.chat_url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("conversation_id", response.data)
        self.assertEqual(response.data["conversation_id"], "optimized123")
        self.assertTrue(mock_redis_instance.get.called or mock_redis_instance.set.called)

    def tearDown(self):
        """Stop all patches after tests complete."""
        self.patcher.stop()
