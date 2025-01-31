# blueprints/personal_assistant/blueprint_personal_assistant.py

"""
Personal Assistant Blueprint

This blueprint defines a Personal Assistant agent that can:
  1. Retrieve real-time weather updates.
  2. Search relevant documentation using the `rag-docs` MCP server.
  3. Perform web searches using the `duckduckgo-search` MCP server.

Lisa delegates tasks to:
  - Marge for weather-related queries.
  - Maggie for retrieving contextual documentation.
  - Bart for performing web searches.

Each assistant agent returns control back to Lisa.
"""

import os
import logging
import requests
import traceback
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent

# Configure logger.
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

    This blueprint provides a general-purpose assistant (Lisa) that can answer questions using:
      - `rag-docs` for documentation search.
      - `Weather API` for real-time weather updates.
      - `DuckDuckGo Search` for web search tasks.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Returns metadata for the Personal Assistant Blueprint.

        Returns:
            Dict[str, Any]: Title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "Personal Assistant",
            "description": (
                "Provides weather updates, retrieves contextual knowledge from documentation, "
                "and performs web searches using DuckDuckGo Search."
            ),
            "required_mcp_servers": ["rag-docs", "duckduckgo-search"],
            "env_vars": [
                "WEATHER_API_KEY",
                "OPENAI_API_KEY",
                "QDRANT_URL",
                "QDRANT_API_KEY",
                "SERPAPI_API_KEY",
            ],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Creates and registers agents for the Personal Assistant Blueprint.

        Returns:
            Dict[str, Agent]: Dictionary of created agents.
        """

        # Retrieve environment variables.
        weather_api_key = os.getenv("WEATHER_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")  # DuckDuckGo API key

        # Validate environment variables.
        missing_env_vars = []
        if not weather_api_key:
            missing_env_vars.append("WEATHER_API_KEY")
        if not openai_api_key:
            missing_env_vars.append("OPENAI_API_KEY")
        if not qdrant_url:
            missing_env_vars.append("QDRANT_URL")
        if not qdrant_api_key:
            missing_env_vars.append("QDRANT_API_KEY")
        if not serpapi_api_key:
            missing_env_vars.append("SERPAPI_API_KEY")
        if missing_env_vars:
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing_env_vars)}")

        # Dictionary to hold all agents.
        agents: Dict[str, Agent] = {}

        # Define Lisa as the central Personal Assistant.
        agents["Lisa"] = Agent(
            name="Lisa",
            instructions=(
                "You are Lisa, a personal assistant capable of retrieving real-time weather updates, "
                "searching documentation via rag-docs, and performing web searches using DuckDuckGo. "
                "Delegate weather queries to Marge, documentation queries to Maggie, and web searches to Bart."
            ),
            env_vars={},
        )

        # Define Marge for weather-related queries.
        agents["Marge"] = Agent(
            name="Marge",
            instructions=(
                "You are Marge, responsible for fetching weather updates using the OpenWeatherMap API. "
                "Retrieve current conditions and forecasts, then return control to Lisa."
            ),
            functions=[self.fetch_current_weather, self.fetch_weather_forecast],
            parallel_tool_calls=True,
        )

        # Define Maggie for retrieving documentation (using rag-docs).
        agents["Maggie"] = Agent(
            name="Maggie",
            instructions=(
                "You are Maggie, tasked with searching and retrieving relevant documentation via the rag-docs MCP server. "
                "Return documentation excerpts to Lisa after processing queries."
            ),
            mcp_servers=["rag-docs"],
            env_vars={
                "OPENAI_API_KEY": openai_api_key,
                "QDRANT_URL": qdrant_url,
                "QDRANT_API_KEY": qdrant_api_key,
            },
        )

        # Define Bart for performing web searches (using DuckDuckGo Search).
        agents["Bart"] = Agent(
            name="Bart",
            instructions=(
                "You are Bart, a web search agent utilizing DuckDuckGo Search. "
                "Process web queries accurately and return results to Lisa promptly."
            ),
            mcp_servers=["duckduckgo-search"],
            env_vars={"SERPAPI_API_KEY": serpapi_api_key},
        )

        # Explicit handoff functions with 25-word docstrings.

        def handoff_to_maggie():
            """
            Delegates task execution from Lisa to Maggie. This function enables Maggie to retrieve documentation via rag-docs accurately and then returns control to Lisa promptly.
            """
            return agents["Maggie"]

        def handoff_to_marge():
            """
            Delegates task execution from Lisa to Marge. This function directs weather queries to Marge, ensuring timely, accurate updates and then returns control promptly to Lisa.
            """
            return agents["Marge"]

        def handoff_to_bart():
            """
            Delegates task execution from Lisa to Bart. This function directs web search queries to Bart using DuckDuckGo, ensuring results and then returns control to Lisa.
            """
            return agents["Bart"]

        def handoff_back_to_lisa():
            """
            Delegates task execution from an assistant agent back to Lisa. This function ensures that after completing tasks, control is returned to Lisa for further processing.
            """
            return agents["Lisa"]

        # Assign handoff functions to Lisa.
        agents["Lisa"].functions = [
            handoff_to_maggie,
            handoff_to_marge,
            handoff_to_bart,
        ]

        # Each assistant agent returns control back to Lisa.
        agents["Maggie"].functions = [handoff_back_to_lisa]
        # For Marge, add the handoff function to the existing tool calls.
        agents["Marge"].functions += [handoff_back_to_lisa]
        agents["Bart"].functions = [handoff_back_to_lisa]

        # Set Lisa as the starting agent.
        self.set_starting_agent(agents["Lisa"])

        logger.info("Lisa, Marge, Maggie, and Bart have been created as agents.")
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
