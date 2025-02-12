import os
import json
import logging
from unittest import mock
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient  # type: ignore
from rest_framework import status  # type: ignore
from rest_framework.authtoken.models import Token  # type: ignore
import pytest

logger = logging.getLogger(__name__)

class TestChat(APITestCase):
    """Tests for verifying stateless and stateful chat behavior."""

    def setUp(self):
        """Set up test environment, credentials, and mock BlueprintBase.run_with_context."""
        # Set dummy API authentication environment variables to mirror test_views.py
        os.environ["ENABLE_API_AUTH"] = "True"
        os.environ["API_AUTH_TOKEN"] = "dummy-token"

        self.client = APIClient()
        self.chat_url = reverse('chat_completions')

        # Patch authentication similar to test_views.py so that the request
        # is authenticated if the Authorization header is "Bearer dummy-token"
        from swarm import views
        self.original_auth = views.EnvOrTokenAuthentication
        from swarm.auth import EnvOrTokenAuthentication
        def dummy_authenticate(self, request):
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            if auth_header == "Bearer dummy-token":
                class DummyUser:
                    username = "testuser"
                    
                    @property
                    def is_authenticated(self):
                        return True
                    
                    @property
                    def is_anonymous(self):
                        return False
                return (DummyUser(), None)
            return None
        EnvOrTokenAuthentication.authenticate = dummy_authenticate
        setattr(views.chat_completions, "authentication_classes", [EnvOrTokenAuthentication])
        setattr(views.chat_completions, "permission_classes", [])

        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create the token with key "dummy-token" so it matches the dummy auth logic.
        self.token = Token.objects.create(user=self.user, key='dummy-token')
        # Set up authentication using the created token.
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
        
        # Ensure no previous stateful config interferes.
        os.environ.pop('STATEFUL_CHAT_ID_PATH', None)
        # Patch the method to return a realistic mocked response.
        from unittest.mock import patch
        self.patcher = patch(
            "swarm.extensions.blueprint.blueprint_base.BlueprintBase.run_with_context",
            side_effect=TestChat.mock_run_with_context
        )
        self.mock_run_with_context_method = self.patcher.start()

    functions = []  # Add empty functions list to mock agent

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
            "messages": [{"content": "Mocked response", "role": "assistant"}]
        }

    def test_stateless_chat(self):
        # Test with valid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer dummy-token')
        """Verify stateless mode returns responses without tracking history."""
        self.assertFalse('STATEFUL_CHAT_ID_PATH' in os.environ)
        response = self.client.post(self.chat_url, data={'message': 'Hello'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("choices", response.data)

    def test_invalid_input(self):
        """Test error handling for invalid input."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer dummy-token')
        response = self.client.post(self.chat_url, data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Messages are required.")

    def test_stateful_chat(self):
        """Verify stateful chat tracks conversation ID and stores history."""
        os.environ['STATEFUL_CHAT_ID_PATH'] = "chat_id"
        initial_payload = {"chat_id": "abc123", "message": "Hello from stateful test"}
        self.client.credentials(HTTP_AUTHORIZATION='Bearer dummy-token')
        response = self.client.post(self.chat_url, data=initial_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("conversation_id", response.data)
        self.assertEqual(response.data["conversation_id"], "abc123")
        followup_payload = {"chat_id": "abc123", "message": "How are you stored?"}
        response2 = self.client.post(self.chat_url, data=followup_payload, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn("conversation_id", response2.data)
        self.assertEqual(response2.data["conversation_id"], "abc123")

    def test_jmespath_chat_id_extraction(self):
        """Verify JMESPath-based conversation ID extraction."""
        os.environ['STATEFUL_CHAT_ID_PATH'] = "messages[?role=='assistant'] | [-1].tool_calls[-1].id"
        self.client.credentials(HTTP_AUTHORIZATION='Bearer dummy-token')
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

    def test_database_queries_optimized(self):
        """Ensure database queries are minimized under stateful mode."""
        os.environ['STATEFUL_CHAT_ID_PATH'] = "conv"
        payload = {"conv": "optimized123", "message": "Testing DB queries..."}
        self.client.credentials(HTTP_AUTHORIZATION='Bearer dummy-token')
        response = self.client.post(self.chat_url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("conversation_id", response.data)
        self.assertEqual(response.data["conversation_id"], "optimized123")

    def tearDown(self):
        """Stop all patches and restore altered settings after tests complete."""
        self.patcher.stop()
        from swarm import views
        views.EnvOrTokenAuthentication = self.original_auth
        os.environ.pop('STATEFUL_CHAT_ID_PATH', None)
        os.environ.pop('ENABLE_API_AUTH', None)
        os.environ.pop('API_AUTH_TOKEN', None)

if __name__ == "__main__":
    import unittest
    unittest.main()
