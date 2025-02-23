from rest_framework import serializers
from blueprints.mission_improbable.models import AgentInstruction

class AgentInstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentInstruction
        fields = ['id', 'agent_name', 'instruction_text', 'model', 'env_vars', 'mcp_servers', 'nemo_guardrails_config', 'created_at', 'updated_at']
