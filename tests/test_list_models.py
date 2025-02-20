import json
import os
from django.test import TestCase, Client
from django.urls import reverse
import swarm.extensions.blueprint as bp
from swarm import views

class BlueprintFilterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        os.environ["SWARM_BLUEPRINTS"] = ""
        
        # Store original values
        self.original_discover = bp.discover_blueprints
        self.original_config = views.config
        self.original_blueprints_metadata = views.blueprints_metadata
        
        # Mock discover_blueprints
        bp.discover_blueprints = lambda paths: {
            "echo": {"title": "Echo Blueprint", "description": "Echoes input"},
            "test_bp": {"title": "Test Blueprint", "description": "Test BP"}
        }
        
        # Mock config and blueprints_metadata
        global config, blueprints_metadata
        views.config = {
            "llm": {
                "mock_llm": {"provider": "test", "model": "mock", "passthrough": True},
                "other_llm": {"provider": "test", "model": "other", "passthrough": False}
            },
            "blueprints": {
                "echo": {"path": "/mock/path/echo", "api": True},
                "test_bp": {"path": "/mock/path/test_bp"}
            }
        }
        views.blueprints_metadata = bp.discover_blueprints(["/mock/path"])

    def tearDown(self):
        bp.discover_blueprints = self.original_discover
        views.config = self.original_config
        views.blueprints_metadata = self.original_blueprints_metadata
        if "SWARM_BLUEPRINTS" in os.environ:
            del os.environ["SWARM_BLUEPRINTS"]

    def test_list_models_with_filter(self):
        os.environ["SWARM_BLUEPRINTS"] = "echo"
        url = reverse('list_models')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        
        blueprint_ids = {model["id"] for model in data["data"] if model["object"] == "model"}
        llm_ids = {model["id"] for model in data["data"] if model["object"] == "llm"}
        
        self.assertEqual(blueprint_ids, {"echo"})
        self.assertEqual(llm_ids, {"mock_llm"})

if __name__ == "__main__":
    import unittest
    unittest.main()
