import os
import json
from django.test import TestCase, Client
from django.urls import reverse
from swarm import views

class ViewsTest(TestCase):
    def setUp(self):
        os.environ["ENABLE_API_AUTH"] = "True"
        os.environ["API_AUTH_TOKEN"] = "dummy-token"
        self.client = Client()
        from swarm import views
        self.original_auth = views.EnvOrTokenAuthentication
        # Define a dummy authenticate function on the real EnvOrTokenAuthentication
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
        # Override the authentication and permission classes for the chat_completions view.
        views.chat_completions.authentication_classes = [EnvOrTokenAuthentication]
        views.chat_completions.permission_classes = []
        # Patch get_blueprint_instance to return a dummy blueprint for model "echo"
        self.original_get_blueprint_instance = views.get_blueprint_instance
        from swarm.extensions.blueprint.blueprint_base import BlueprintBase
        class DummyBlueprint(BlueprintBase):
            metadata = {"title": "Echo Blueprint"}
            def create_agents(self):
                return {}
            def run_with_context(self, messages, context_vars):
                return {"response": {"message": "Dummy response"}, "context_variables": context_vars}
        def dummy_get_blueprint_instance(model, context_vars):
            if model == "echo":
                return DummyBlueprint(config={'llm': {'default': {'provider': 'openai', 'model': 'default'}}})
            return self.original_get_blueprint_instance(model, context_vars)
        views.get_blueprint_instance = dummy_get_blueprint_instance
        
    def tearDown(self):
        views.EnvOrTokenAuthentication = self.original_auth

    def test_chat_completions_view_authorized(self):
        url = reverse('chat_completions')
        payload = {
            "model": "echo",
            "messages": [{"role": "user", "content": "hello", "sender": "User"}]
        }
        response = self.client.post(
            url + '/',
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer dummy-token'
        )
        self.assertEqual(response.status_code, 200)
    def test_chat_completions_view_unauthorized(self):
        url = reverse('chat_completions')
        payload = {
            "model": "echo",
            "messages": [{"role": "user", "content": "hello", "sender": "User"}]
        }
        # Temporarily remove authentication-related environment variables to simulate an unauthorized request.
        old_enable = os.environ.pop("ENABLE_API_AUTH", None)
        old_token = os.environ.pop("API_AUTH_TOKEN", None)
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        # Restore the environment variables after the request.
        if old_enable is not None:
            os.environ["ENABLE_API_AUTH"] = old_enable
        if old_token is not None:
            os.environ["API_AUTH_TOKEN"] = old_token
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
if __name__ == "__main__":
    import unittest
    unittest.main()