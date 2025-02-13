import json
import os
from django.test import TestCase, Client, override_settings
from django.urls import reverse
import swarm.extensions.blueprint as bp

class BlueprintFilterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        os.environ["SWARM_BLUEPRINTS"] = ""
        # Monkey-patch discover_blueprints to return a fixed dictionary.
        self.original_discover = bp.discover_blueprints
        bp.discover_blueprints = lambda paths: {"echo": {"title": "Echo Blueprint"}}

    def tearDown(self):
        bp.discover_blueprints = self.original_discover
        if "SWARM_BLUEPRINTS" in os.environ:
            del os.environ["SWARM_BLUEPRINTS"]

    def test_list_models_with_filter(self):
        os.environ["SWARM_BLUEPRINTS"] = "echo"
        url = reverse('list_models')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        for model in data["data"]:
            self.assertEqual(model["id"], "echo")
        del os.environ["SWARM_BLUEPRINTS"]

if __name__ == "__main__":
    import unittest
    unittest.main()
