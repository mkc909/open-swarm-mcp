import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

def update_installed_apps(settings):
    logger.debug("University settings update: Before update, INSTALLED_APPS = %s", settings.get("INSTALLED_APPS"))
    blueprint_app = "blueprints.university"
    if blueprint_app not in settings.get("INSTALLED_APPS", []):
        logger.debug("University settings update: Adding %s to INSTALLED_APPS", blueprint_app)
        settings["INSTALLED_APPS"].append(blueprint_app)
    else:
        logger.debug("University settings update: %s already in INSTALLED_APPS", blueprint_app)
    
try:
    update_installed_apps(globals())
    logger.debug("University update succeeded.")
except Exception as e:
    logger.error("University update failed: %s", e)
