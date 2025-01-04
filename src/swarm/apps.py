from django.apps import AppConfig

class RestModeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'swarm.extensions.blueprint.modes.rest_mode'
