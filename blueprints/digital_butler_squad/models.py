from django.db import models

class AgentInstruction(models.Model):
    """Stores instructions and configuration for Digital Butler Squad agents."""
    agent_name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique name of the agent (e.g., 'Jeeves')."
    )
    instruction_text = models.TextField(
        help_text="Instructions for the agent’s behavior."
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
        help_text="JSON string of MCP server names (e.g., '[\"memory\"]')."
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
        app_label = "blueprints_digital_butler_squad"
        db_table = "swarm_agent_instruction_digital_butler"
        verbose_name = "Agent Instruction"
        verbose_name_plural = "Agent Instructions"

    def __str__(self):
        return f"{self.agent_name} Instruction"
