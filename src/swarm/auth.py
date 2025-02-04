import os
import logging
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

class EnvAuthenticatedUser(AnonymousUser):
    """ Custom user class that is always authenticated. """
    @property
    def is_authenticated(self):
        return True  # Ensure Django recognizes this user

class EnvOrTokenAuthentication(TokenAuthentication):
    """
    Custom authentication that allows:
    1. Environment variable API key (`API_AUTH_TOKEN`)
    2. Standard Django TokenAuthentication
    """
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        # logger.info(f"Received Auth Header: {auth_header}")

        if not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Invalid token format.")

        token = auth_header.split("Bearer ")[-1].strip()

        # Log both received and expected tokens
        env_token = os.getenv("API_AUTH_TOKEN", None)
        # logger.info(f"Received Token: {token}")
        # logger.info(f"Expected Env Token: {env_token}")

        if env_token and token == env_token:
            logger.info("Authenticated as anonymous user with API_AUTH_TOKEN")
            return (EnvAuthenticatedUser(), None)  # Allow access

        return super().authenticate(request)
