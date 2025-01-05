import os
import json
import django
from django.test import TestCase
from django.urls import reverse
import pytest

# Ensure settings are set up
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swarm.settings")
django.setup()

@pytest.mark.skipif(
    os.getenv("CI", "").lower() in ["true", "1"],
    reason="Skipping all tests in ViewsTest due to missing OPENAI_API_KEY in CI environment."
)
class ViewsTest(TestCase):
    """
    Tests for the views in the Open Swarm MCP application.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up test data shared across all test methods in this class.
        """
        # Example setup if any database objects or preconditions are required
        pass

    def test_models_view(self):
        """
        Test the list_models endpoint.
        """
        url = reverse('list_models')
        response = self.client.get(url)

        # Assert the response status is 200
        self.assertEqual(response.status_code, 200, f"Expected status 200, got {response.status_code}")

        # Assert the response contains the expected keys
        response_data = response.json()
        self.assertIn("object", response_data, "Response missing 'object' field.")
        self.assertEqual(response_data["object"], "list", "Response 'object' field is not 'list'.")
        self.assertIn("data", response_data, "Response missing 'data' field.")
        self.assertIsInstance(response_data["data"], list, "Response 'data' field is not a list.")

        # Assert individual model objects in the list
        for model in response_data["data"]:
            self.assertIn("id", model, "Model missing 'id' field.")
            self.assertIn("title", model, "Model missing 'title' field.")
            self.assertIn("description", model, "Model missing 'description' field.")

    def test_chat_completions_view(self):
        """
        Test the chat_completions endpoint.
        """
        url = reverse('chat_completions')

        # Simulate a valid request payload
        payload = {
            "model": "echo",  # Blueprint identifier
            "messages": [{"role": "user", "content": "hello", "sender": "User"}]
        }

        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")

        # Assert the response status is 200
        self.assertEqual(response.status_code, 200, f"Expected status 200, got {response.status_code}")

        # Assert the response contains expected keys
        response_data = response.json()
        self.assertIn("id", response_data, "Response missing 'id' field.")
        self.assertIn("object", response_data, "Response missing 'object' field.")
        self.assertIn("model", response_data, "Response missing 'model' field.")
        self.assertIn("choices", response_data, "Response missing 'choices' field.")

        # Assert the choices field contains a valid response
        self.assertIsInstance(response_data["choices"], list, "Response 'choices' is not a list.")
        self.assertGreater(len(response_data["choices"]), 0, "Response 'choices' is empty.")
        choice = response_data["choices"][0]
        self.assertIn("message", choice, "Choice missing 'message' field.")
        self.assertIn("content", choice["message"], "Choice message missing 'content' field.")
