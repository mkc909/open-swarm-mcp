from django.apps import AppConfig

class UniversityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blueprints.university"  # Directory name
    label = "blueprints_university"  # App label with underscore
