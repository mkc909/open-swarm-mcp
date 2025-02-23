from django.db import models

class AgentInstruction(models.Model):
    """Stores instructions and configuration for Dilbot Universe agents."""
    agent_name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique name of the agent (e.g., 'Dilbot')."
    )
    instruction_text = models.TextField(
        help_text="Instructions for the agent’s 9-step SDLC routine."
    )
    model = models.CharField(
        max_length=50,
        default="default",
        help_text="LLM model for the agent (e.g., 'gpt-4o-mini')."
    )
    env_vars = models.TextField(
        blank=True,
        null=True,
        help_text="JSON string of environment variables (e.g., '{\"DEBUG\": \"true\"}')."
    )
    mcp_servers = models.TextField(
        blank=True,
        null=True,
        help_text="JSON string of MCP server names (e.g., '[\"server1\"]')."
    )
    nemo_guardrails_config = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="NeMo Guardrails config directory name (e.g., 'tracing')."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the instruction was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the instruction was last updated."
    )

    class Meta:
        app_label = "blueprints_dilbot_universe"
        db_table = "swarm_agent_instruction"
        verbose_name = "Agent Instruction"
        verbose_name_plural = "Agent Instructions"

    def __str__(self):
        return f"{self.agent_name} Instruction"
