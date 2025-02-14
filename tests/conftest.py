import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swarm.settings")
import blueprints.university.settings
import importlib
import django
from django.apps import apps
import pytest
importlib.reload(blueprints.university.settings)
django.setup()

# Existing fixtures and configuration can remain here

# Fixture to force registration of the University blueprint
@pytest.fixture(autouse=True, scope="session")
def register_university_blueprint():
    # Import the University blueprint's settings to trigger registration
    import blueprints.university.settings
    # Optionally, you can force reload if needed:
    importlib.reload(blueprints.university.settings)
    # Verify registration: Django registers the app using the "name" defined in AppConfig
    assert apps.is_installed("blueprints.university"), "University blueprint not registered"
