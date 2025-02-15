from django.conf import settings
from blueprints.university.apps import UniversityConfig
if "blueprints.university" not in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS += ["blueprints.university"]