import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

def update_installed_apps(settings):
    logger.debug("DilbotUniverse settings update: Before update, INSTALLED_APPS = %s", settings.get("INSTALLED_APPS"))
    blueprint_app = "blueprints.dilbot_universe"
    if blueprint_app not in settings.get("INSTALLED_APPS", []):
        logger.debug("Adding %s to INSTALLED_APPS", blueprint_app)
        settings["INSTALLED_APPS"].append(blueprint_app)
    else:
        logger.debug("%s already in INSTALLED_APPS", blueprint_app)

try:
    update_installed_apps(globals())
    logger.debug("DilbotUniverse update succeeded.")
except Exception as e:
    logger.error("DilbotUniverse update failed: %s", e)

CORS_ALLOW_ALL_ORIGINS = True
