import os
import logging
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import TokenAuthentication  # type: ignore
from rest_framework.exceptions import AuthenticationFailed  # type: ignore

logger = logging.getLogger(__name__)

class EnvAuthenticatedUser(AnonymousUser):
    """ Custom user class that is always authenticated. """
    @property
    def is_authenticated(self) -> bool:  # type: ignore[override]
        return True  # Ensure Django recognizes this user as authenticated

class EnvOrTokenAuthentication(TokenAuthentication):
    """
    Custom authentication that allows:
    1. If API_AUTH_TOKEN is set, it enforces token authentication.
    2. Else if ENABLE_API_AUTH is False/Unset, authentication is bypassed.
    3. Otherwise, falls back to Django's TokenAuthentication.
    """
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        env_token = os.getenv("API_AUTH_TOKEN", None)
        enable_auth = os.getenv("ENABLE_API_AUTH", "false").lower() in ("true", "1", "t")

        # If API authentication is disabled, allow unrestricted access
        if not enable_auth:
            logger.info("Authentication is disabled (ENABLE_API_AUTH not set or False). Allowing all users.")
            return (EnvAuthenticatedUser(), None)

        # If API_AUTH_TOKEN is set, enforce token validation
        if env_token:
            if not auth_header:
                raise AuthenticationFailed("Authentication credentials were not provided.")
            if not auth_header.startswith("Bearer "):
                raise AuthenticationFailed("Invalid token format.")

            token = auth_header.split("Bearer ")[-1].strip()

            if token == env_token:
                logger.info("Authenticated using API_AUTH_TOKEN.")
                return (EnvAuthenticatedUser(), None)  # Allow access
            else:
                raise AuthenticationFailed("Invalid token.")

        # If API authentication is disabled, allow unrestricted access
        if not enable_auth:
            logger.info("Authentication is disabled (ENABLE_API_AUTH not set or False). Allowing all users.")
            return (EnvAuthenticatedUser(), None)

        # Fallback to Django's TokenAuthentication
        return super().authenticate(request)

    def authenticate_header(self, request):
        return "Bearer"
