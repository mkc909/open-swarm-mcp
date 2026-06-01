from django.apps import apps
from django.test import TestCase

class AppsTest(TestCase):
    def test_rest_mode_config(self):
        config = apps.get_app_config('rest_mode')
        self.assertEqual(config.default_auto_field, 'django.db.models.BigAutoField')
        self.assertEqual(config.name, 'swarm.extensions.blueprint.modes.rest_mode')