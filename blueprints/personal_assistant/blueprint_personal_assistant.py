# blueprints/personal_assistant/blueprint_personal_assistant.py

"""
Personal Assistant Blueprint

This blueprint defines a Personal Assistant agent that can:
1. Retrieve real-time weather updates.
2. Search relevant documentation using the `rag-docs` MCP server.
3. Perform web searches using the `brave-search` MCP server.

The PersonalAssistantAgent delegates tasks to:
- `WeatherAgent` for weather-related queries.
- `DocumentationAgent` for retrieving contextual knowledge.
- `BraveSearchAgent` for web search tasks.

Each assistant agent returns control back to the PersonalAssistantAgent.
"""

import os
import logging
import requests
import traceback
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
    - `Brave Search` for performing web searches.
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
            "description": (
                "Provides weather updates, retrieves contextual knowledge from documentation, "
                "and performs web searches using Brave Search."
            ),
            "required_mcp_servers": ["rag-docs", "brave-search"],
            "env_vars": [
                "WEATHER_API_KEY",
                "OPENAI_API_KEY",
                "QDRANT_URL",
                "QDRANT_API_KEY",
                "BRAVE_API_KEY",  # Added Brave API Key
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
        brave_api_key = os.getenv("BRAVE_API_KEY")  # Retrieve Brave API Key

        # Validate environment variables
        missing_env_vars = []
        if not weather_api_key:
            missing_env_vars.append("WEATHER_API_KEY")
        if not openai_api_key:
            missing_env_vars.append("OPENAI_API_KEY")
        if not qdrant_url:
            missing_env_vars.append("QDRANT_URL")
        if not qdrant_api_key:
            missing_env_vars.append("QDRANT_API_KEY")
        if not brave_api_key:
            missing_env_vars.append("BRAVE_API_KEY")
        if missing_env_vars:
            raise EnvironmentError(
                f"Missing environment variables: {', '.join(missing_env_vars)}"
            )

        # Dictionary to hold all agents
        agents: Dict[str, Agent] = {}

        # Define the Personal Assistant Agent
        agents["PersonalAssistantAgent"] = Agent(
            name="PersonalAssistantAgent",
            instructions=(
                "You are a personal assistant capable of retrieving real-time weather updates, "
                "answering knowledge-based questions using documentation search, and performing web searches. "
                "Use the WeatherAgent for weather queries, the DocumentationAgent for knowledge retrieval, "
                "and the BraveSearchAgent for web searches."
            ),
            env_vars={},
        )

        # Define the Weather Agent
        agents["WeatherAgent"] = Agent(
            name="WeatherAgent",
            instructions=(
                "You provide weather-related information using the OpenWeatherMap API. "
                "You can fetch current weather conditions and forecasts based on user queries. "
                "Only after providing the information, you may return control to the PersonalAssistantAgent."
            ),
            functions=[
                self.fetch_current_weather,
                self.fetch_weather_forecast,
            ],
            parallel_tool_calls=True
        )

        # Define the Documentation Agent (Uses `rag-docs` MCP server)
        agents["DocumentationAgent"] = Agent(
            name="DocumentationAgent",
            instructions=(
                "You retrieve relevant documentation using the `rag-docs` MCP server. "
                "Search documentation based on user queries and return relevant excerpts. "
                "After providing the information, return control to the PersonalAssistantAgent."
            ),
            mcp_servers=["rag-docs"],
            env_vars={
                "OPENAI_API_KEY": openai_api_key,
                "QDRANT_URL": qdrant_url,
                "QDRANT_API_KEY": qdrant_api_key,
            },
        )

        # Define the Brave Search Agent
        agents["BraveSearchAgent"] = Agent(
            name="BraveSearchAgent",
            instructions=(
                "You are a web search assistant using Brave Search. "
                "Provide accurate and relevant web search results based on user queries. "
                "After providing the search results, return control to the PersonalAssistantAgent."
            ),
            mcp_servers=["brave-search"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
        )

        # Define handoff functions
        def handoff_to_documentation():
            logger.debug("PersonalAssistantAgent is handing off to DocumentationAgent")
            return agents["DocumentationAgent"]

        def handoff_to_weather():
            logger.debug("PersonalAssistantAgent is handing off to WeatherAgent")
            return agents["WeatherAgent"]

        def handoff_to_brave_search():
            logger.debug("PersonalAssistantAgent is handing off to BraveSearchAgent")
            return agents["BraveSearchAgent"]

        def handoff_back_to_assistant():
            logger.debug("Assistant agent is handing off back to PersonalAssistantAgent")
            return agents["PersonalAssistantAgent"]

        # Assign handoff functions to PersonalAssistantAgent
        agents["PersonalAssistantAgent"].functions = [
            handoff_to_documentation,
            handoff_to_weather,
            handoff_to_brave_search,  # Added handoff to BraveSearchAgent
        ]

        # Assistant agents return control to PersonalAssistantAgent
        agents["DocumentationAgent"].functions = [handoff_back_to_assistant]
        agents["WeatherAgent"].functions += [handoff_back_to_assistant]
        agents["BraveSearchAgent"].functions = [handoff_back_to_assistant]  # Ensure it returns control

        # Set the starting agent
        self.set_starting_agent(agents["PersonalAssistantAgent"])

        logger.info("PersonalAssistantAgent, WeatherAgent, DocumentationAgent, and BraveSearchAgent have been created.")
        logger.debug(f"Agents created: {list(agents.keys())}")
        return agents


    def fetch_current_weather(self, location: str) -> str:
        """
        Fetch current weather data for the specified location.

        Args:
            location (str): Location to fetch weather data for.

        Returns:
            str: Weather information or error message.
        """
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            logger.debug(f"Requesting current weather data from: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                weather_description = data['weather'][0]['description']
                temperature = data['main']['temp']
                weather_info = f"The current weather in {location} is {weather_description} with a temperature of {temperature}°C."
                logger.info(f"Weather data fetched: {weather_info}")
                return weather_info
            else:
                error_msg = f"Failed to fetch weather data: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error fetching current weather: {e}"
            logger.error(error_msg)
            traceback.print_exc()
            return error_msg

    def fetch_weather_forecast(self, location: str) -> str:
        """
        Fetch weather forecast for the specified location.

        Args:
            location (str): Location to fetch weather forecast for.

        Returns:
            str: Weather forecast information or error message.
        """
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
            logger.debug(f"Requesting weather forecast data from: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                forecast_list = data['list'][:5]
                forecast_info = f"Weather forecast for {location}:\n"
                for forecast in forecast_list:
                    dt_txt = forecast['dt_txt']
                    weather_desc = forecast['weather'][0]['description']
                    temp = forecast['main']['temp']
                    forecast_info += f"{dt_txt}: {weather_desc}, {temp}°C\n"
                logger.info(f"Weather forecast fetched: {forecast_info}")
                return forecast_info
            else:
                error_msg = f"Failed to fetch weather forecast: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error fetching weather forecast: {e}"
            logger.error(error_msg)
            traceback.print_exc()
            return error_msg

if __name__ == "__main__":
    PersonalAssistantBlueprint.main()
