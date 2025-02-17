import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swarm.settings")
os.environ.setdefault("ENABLE_API_AUTH", "false")
import uuid
import pytest
from django.conf import settings
from django.core.management import call_command
from django.test.utils import override_settings

# Set up a unique test database for each test suite run.
os.environ["UNIT_TESTING"] = "true"
os.environ["SQLITE_DB_PATH"] = f"./swarm-django-{uuid.uuid4().hex}.db"
os.environ["DJANGO_DATABASE"] = "sqlite"

@pytest.fixture(autouse=True, scope="session")
def migrate_db(django_db_setup, django_db_blocker):
    # Reorder INSTALLED_APPS so that 'swarm' comes first.
    new_apps = sorted(settings.INSTALLED_APPS, key=lambda app: 0 if app == "swarm" else 1)
    # with django_db_blocker.unblock():
            # call_command("migrate", interactive=False)
            # call_command("migrate", "swarm", interactive=False)
            # call_command("migrate", "blueprints_university", interactive=False)