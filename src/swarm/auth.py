import os
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class EnvOrTokenAuthentication(TokenAuthentication):
    """
    Custom authentication that allows:
    1. Environment variable API key (`API_AUTH_TOKEN`)
    2. Standard Django TokenAuthentication
    """
    def authenticate(self, request):
        # Check if a Bearer token was provided
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Invalid token format.")

        token = auth_header.split("Bearer ")[-1].strip()

        # Check if the token matches the env-based API token
        env_token = os.getenv("API_AUTH_TOKEN", None)
        if env_token and token == env_token:
            return (None, None)

        # If not an env token, fall back to Django's TokenAuthentication
        return super().authenticate(request)
