from django.conf import settings
from .apps import UniversityConfig
if "blueprints.university" not in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS += ["blueprints.university"]