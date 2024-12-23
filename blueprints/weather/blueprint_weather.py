# blueprints/weather/blueprint_weather.py

"""
Weather Information Blueprint

This blueprint provides weather-related information using the Open Swarm MCP framework.
"""

import os
from typing import Dict, Any, Optional
from swarm import Agent
from open_swarm_mcp.blueprint_base import BlueprintBase

class WeatherBlueprint(BlueprintBase):
    """
    Weather Information Blueprint Implementation.
    """

    def __init__(self):
        super().__init__()
        self._metadata = {
            "title": "Weather Information",
            "description": "Provides current weather information based on user queries.",
            "required_mcp_servers": ["weather"],
            "env_vars": ["WEATHER_API_KEY"]
        }

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def validate_env_vars(self) -> None:
        """Validate that required environment variables are set."""
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            raise ValueError("Environment variable WEATHER_API_KEY is not set.")

    def create_agent(self) -> Agent:
        """Create and configure the weather information agent."""
        return Agent(
            name="WeatherAgent",
            instructions="""You can provide current weather information based on user queries.
Please ensure that all operations are within the allowed parameters.""",
            functions=[],
            tool_choice=None,
            parallel_tool_calls=True
        )

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        self.validate_env_vars()
        agent = self.create_agent()

        # Allow for message override from framework config
        default_message = {
            "role": "user",
            "content": "What's the weather like today in New York?"
        }
        messages = config.get('messages', [default_message]) if config else [default_message]

        response = self.client.run(agent=agent, messages=messages)

        return {
            "status": "success",
            "messages": response.messages,
            "metadata": self.metadata
        }

# Entry point for standalone execution
if __name__ == "__main__":
    blueprint = WeatherBlueprint()
    try:
        blueprint.interactive_mode()
    except Exception as e:
        print(f"Error running Weather Blueprint: {e}")
