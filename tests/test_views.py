import os
import json
import django
from django.test import TestCase
from django.urls import reverse
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swarm.settings")
django.setup()

@pytest.mark.skipif(os.getenv("CI", "").lower() in ["true", "1"], reason="Skipping ViewsTest in CI environment.")
class ViewsTest(TestCase):
    def setUp(self):
        if 'API_AUTH_TOKEN' not in os.environ:
            os.environ['API_AUTH_TOKEN'] = 'test-token-123'

    def test_models_view(self):
        url = reverse('list_models')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, f"Expected status 200, got {response.status_code}")
        response_data = response.json()
        self.assertIn("object", response_data, "Response missing 'object' field.")
        self.assertEqual(response_data["object"], "list", "Response 'object' field is not 'list'.")
        self.assertIn("data", response_data, "Response missing 'data' field.")
        self.assertIsInstance(response_data["data"], list, "Response 'data' field is not a list.")

    def test_chat_completions_view_authorized(self):
        url = reverse('chat_completions')
        payload = {
            "model": "echo",
            "messages": [{"role": "user", "content": "hello", "sender": "User"}]
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f'Bearer {os.environ["API_AUTH_TOKEN"]}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("choices", response.json())

    def test_chat_completions_view_unauthorized(self):
        url = reverse('chat_completions')
        payload = {
            "model": "echo",
            "messages": [{"role": "user", "content": "hello", "sender": "User"}]
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication credentials were not provided.")

    def test_serve_swarm_config_view(self):
        url = reverse('serve_swarm_config')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIsInstance(response_data, dict)
        self.assertIn("llm", response_data)

    def tearDown(self):
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(username='testuser')
            user.delete()
        except User.DoesNotExist:
            pass