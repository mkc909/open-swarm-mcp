import os
import json
from django.test import TestCase, Client

class BlueprintFilterTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_list_models_without_filter(self):
        # Ensure the environment variable is not set
        if "SWARM_BLUEPRINTS" in os.environ:
            del os.environ["SWARM_BLUEPRINTS"]
        response = self.client.get("/v1/models")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn("data", data)
        # Without filter, there should be at least one blueprint.
        self.assertTrue(len(data["data"]) >= 1)

    def test_list_models_with_filter(self):
        os.environ["SWARM_BLUEPRINTS"] = "echo"
        response = self.client.get("/v1/models")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn("data", data)
        # With filter applied, each returned model id should be "echo"
        for model in data["data"]:
            self.assertEqual(model["id"], "echo")
        del os.environ["SWARM_BLUEPRINTS"]