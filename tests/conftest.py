import os
import warnings
import importlib
import django
from django.apps import apps
import pytest

# Suppress warnings at the beginning
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="nemoguardrails")

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swarm.settings")

# Import and reload settings
import blueprints.university.settings
importlib.reload(blueprints.university.settings)

# Setup Django
django.setup()

# Fixture to force registration of the University blueprint
@pytest.fixture(autouse=True, scope="session")
def register_university_blueprint():
    # Import the University blueprint's settings to trigger registration
    import blueprints.university.settings
    # Optionally, you can force reload if needed:
    importlib.reload(blueprints.university.settings)
    # Verify registration: Django registers the app using the "name" defined in AppConfig
    assert apps.is_installed("blueprints.university"), "University blueprint not registered"