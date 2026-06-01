from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
import os
from swarm.auth import EnvOrTokenAuthentication
from blueprints.dilbot_universe.models import AgentInstruction
from blueprints.dilbot_universe.serializers import AgentInstructionSerializer

class AgentInstructionViewSet(ModelViewSet):
    """
    Viewset for CRUD operations on AgentInstruction model in the Dilbot Universe.
    """
    authentication_classes = [EnvOrTokenAuthentication]
    permission_classes = [AllowAny]
    queryset = AgentInstruction.objects.all()
    serializer_class = AgentInstructionSerializer

    def get_permissions(self):
        enable_auth = os.getenv("ENABLE_API_AUTH", "false").lower() in ("true", "1", "t")
        if enable_auth:
            from rest_framework.permissions import IsAuthenticated
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_authentication(self, request):
        super().perform_authentication(request)
        if not request.user or not request.user.is_authenticated:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed("Invalid token.")

__all__ = ["AgentInstructionViewSet"]
