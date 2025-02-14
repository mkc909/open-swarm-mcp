import os
from django.conf import settings
from django.test import TestCase, Client
from blueprints.university.blueprint_university import UniversitySupportBlueprint

class UniversityBlueprintURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set a dummy SQLite DB path to satisfy blueprint initialization.
        os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
        # Ensure ROOT_URLCONF is set to the core swarm urls.
        settings.ROOT_URLCONF = "swarm.urls"
        # Provide a dummy LLM configuration to avoid config errors.
        dummy_config = {
            "llm": {
                "default": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "dummy"
                }
            }
        }
        # Instantiate the blueprint and register its URLs.
        blueprint = UniversitySupportBlueprint(config=dummy_config)
        blueprint.register_blueprint_urls()

    def setUp(self):
        self.client = Client()

    def test_courses_endpoint(self):
        """
        Verify that the university blueprint has registered the courses endpoint.
        """
        response = self.client.get('/v1/university/courses/')
        self.assertEqual(response.status_code, 200)

    def test_students_endpoint(self):
        """
        Verify that the university blueprint has registered the students endpoint.
        """
        response = self.client.get('/v1/university/students/')
        self.assertEqual(response.status_code, 200)