import os
from django.conf import settings
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swarm.settings")

def test_installed_apps():
    required_apps = ['django.contrib.admin', 'rest_framework']
    for app in required_apps:
        assert app in settings.INSTALLED_APPS, f"{app} not found in INSTALLED_APPS"

def test_logging_configuration():
    loggers = settings.LOGGING.get('loggers', {})
    assert 'django' in loggers, "Django logger is not configured"
    handlers = loggers.get('django', {}).get('handlers', [])
    assert 'console' in handlers, "Console handler not found in logging configuration"
