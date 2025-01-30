# blueprints/personal_assistant/blueprint_personal_assistant.py

"""
Personal Assistant Blueprint

This blueprint defines a Personal Assistant agent that can:
1. Retrieve real-time weather updates.
2. Search relevant documentation using the `rag-docs` MCP server.

The PersonalAssistantAgent delegates tasks to:
- `WeatherAgent` for weather-related queries.
- `DocumentationAgent` for retrieving contextual knowledge.

Each assistant agent returns control back to the PersonalAssistantAgent.
"""

import os
import logging
from typing import Dict, Any
from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class PersonalAssistantBlueprint(BlueprintBase):
    """
    Personal Assistant Blueprint Implementation.

    This blueprint provides a general-purpose assistant that can answer questions using:
    - `rag-docs` for retrieving relevant documentation.
    - `Weather API` for fetching real-time weather updates.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the Personal Assistant Blueprint.

        Returns:
            Dict[str, Any]: Metadata with title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "Personal Assistant",
            "description": "Provides weather updates and retrieves contextual knowledge from documentation.",
            "required_mcp_servers": ["rag-docs"],
            "env_vars": [
                "WEATHER_API_KEY",
                "OPENAI_API_KEY",
                "QDRANT_URL",
                "QDRANT_API_KEY",
            ],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create agents for the Personal Assistant Blueprint.

        Returns:
            Dict[str, Agent]: Dictionary of created agents.
        """

        # Retrieve environment variables
        weather_api_key = os.getenv("WEATHER_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        # Dictionary to hold all agents
        agents: Dict[str, Agent] = {}

        # Define the Personal Assistant Agent
        agents["PersonalAssistantAgent"] = Agent(
            name="PersonalAssistantAgent",
            instructions=(
                "You are a personal assistant capable of retrieving real-time weather updates "
                "and answering knowledge-based questions using documentation search. "
                "Use the WeatherAgent for weather queries and the DocumentationAgent for knowledge retrieval."
            ),
            env_vars={},
        )

        # Define the Weather Agent
        agents["WeatherAgent"] = Agent(
            name="WeatherAgent",
            instructions=(
                "You provide weather-related information using OpenWeatherMap API. "
                "You can fetch current weather conditions and forecasts based on user queries."
                "Handback to assistant after providing weather information to user."
            ),
            mcp_servers=[],
            env_vars={"WEATHER_API_KEY": weather_api_key},
        )

        # Define the Documentation Agent (Uses `rag-docs` MCP server)
        agents["DocumentationAgent"] = Agent(
            name="DocumentationAgent",
            instructions=(
                "You retrieve relevant documentation using the `rag-docs` MCP server. "
                "Search documentation based on user queries and return relevant excerpts."
                "Handback to assistant after providing documentation information to user."
            ),
            mcp_servers=["rag-docs"],
            env_vars={
                "OPENAI_API_KEY": openai_api_key,
                "QDRANT_URL": qdrant_url,
                "QDRANT_API_KEY": qdrant_api_key,
            },
        )

        # Define handoff functions
        def handoff_to_documentation():
            logger.debug("PersonalAssistantAgent is handing off to DocumentationAgent")
            return agents["DocumentationAgent"]

        def handoff_to_weather():
            logger.debug("PersonalAssistantAgent is handing off to WeatherAgent")
            return agents["WeatherAgent"]

        def handoff_back_to_assistant():
            logger.debug("Assistant agent is handing off back to PersonalAssistantAgent")
            return agents["PersonalAssistantAgent"]

        # Assign handoff functions to PersonalAssistantAgent
        agents["PersonalAssistantAgent"].functions = [
            handoff_to_documentation,
            handoff_to_weather,
        ]

        # Assistant agents return control to PersonalAssistantAgent
        agents["DocumentationAgent"].functions = [handoff_back_to_assistant]
        agents["WeatherAgent"].functions = [handoff_back_to_assistant]

        # Set the starting agent
        self.set_starting_agent(agents["PersonalAssistantAgent"])

        logger.debug(f"Agents created: {list(agents.keys())}")
        return agents


if __name__ == "__main__":
    PersonalAssistantBlueprint.main()
