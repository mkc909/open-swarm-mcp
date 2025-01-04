import os
import django
from django.test import TestCase
from django.urls import reverse

# Ensure settings are set up
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swarm.settings")
django.setup()

class ViewsTest(TestCase):
    """
    Tests for the views in the Open Swarm MCP application.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up test data shared across all test methods in this class.
        """
        # Example: Creating necessary database objects for testing
        pass

    def test_models_view(self):
        """
        Test the list_models endpoint.
        """
        url = reverse('list_models')
        response = self.client.get(url)

        # Assert the response status is 200
        self.assertEqual(response.status_code, 200)

        # Assert the response contains the expected keys
        response_data = response.json()
        self.assertIn("object", response_data)
        self.assertEqual(response_data["object"], "list")
        self.assertIn("data", response_data)
        self.assertIsInstance(response_data["data"], list)
