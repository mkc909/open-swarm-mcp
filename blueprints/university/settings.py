import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class UniversityBlueprintConfig(AppConfig):
    name = "blueprints.university"
    label = "blueprints_university"
    verbose_name = "University Blueprint"

default_app_config = "blueprints.university.UniversityBlueprintConfig"

def update_installed_apps(settings):
    logger.debug("University settings update: Before update, INSTALLED_APPS = %s", settings.get("INSTALLED_APPS"))
    blueprint_app = "blueprints.university"
    if blueprint_app not in settings.get("INSTALLED_APPS", []):
        logger.debug("University settings update: Adding %s to INSTALLED_APPS", blueprint_app)
        settings["INSTALLED_APPS"].append(blueprint_app)
    else:
        logger.debug("University settings update: %s already in INSTALLED_APPS", blueprint_app)
# Removed automatic INSALLED_APPS update to delay it until after INSTALLED_APPS is defined in main settings.