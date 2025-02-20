import os
import uuid
os.environ["UNIT_TESTING"] = "true"
os.environ["SQLITE_DB_PATH"] = f"/mnt/models/open-swarm/test_db_{uuid.uuid4().hex}.sqlite3"
import pytest
from django.conf import settings
from django.apps import apps
from blueprints.university.blueprint_university import UniversitySupportBlueprint

import pytest
@pytest.mark.django_db
def test_university_blueprint_loaded():
    """
    Test that the University blueprint settings are loaded.
    If SWARM_BLUEPRINTS is not set or includes 'university', then the university
    blueprint should be loaded and its app registered.
    """
    from django.apps import apps
    app_labels = [app.label for app in apps.get_app_configs()]
    assert "blueprints_university" in app_labels, "University blueprint app not loaded"

def test_university_blueprint_metadata():
    """
    Test that the University blueprint metadata contains the expected django_modules
    with full module paths.
    """
    blueprint = UniversitySupportBlueprint(config={})
    metadata = blueprint.metadata
    django_modules = metadata.get("django_modules", {})
    required_keys = ["models", "views", "urls", "serializers"]
    for key in required_keys:
        assert key in django_modules, f"Missing '{key}' in django_modules"
        module_path = django_modules[key]
        # Expect module_path to start with 'blueprints.university.'
        assert module_path.startswith("blueprints.university."), f"{key} does not use full path"