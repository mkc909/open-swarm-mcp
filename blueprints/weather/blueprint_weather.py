# blueprints/weather/blueprint_weather.py

"""
Weather Integration Blueprint

This blueprint provides weather-related information using external APIs.
"""

from open_swarm_mcp.blueprint_base import BlueprintBase
from typing import Dict, Any, Optional
from swarm import Agent, Swarm
import os
import logging
import requests

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class WeatherBlueprint(BlueprintBase):
    """
    Weather Integration Blueprint Implementation.
    """

    def __init__(self) -> None:
        self._metadata = {
            "title": "Weather Team",
            "description": "Provides weather-related information.",
            "required_mcp_servers": ["weather"],
            "env_vars": ["WEATHER_API_KEY"]
        }
        self.client = Swarm()
        logger.info("Initialized Weather Blueprint with Swarm.")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def validate_env_vars(self) -> None:
        """Validate that required environment variables are set."""
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            raise ValueError("Environment variable WEATHER_API_KEY is not set.")
        logger.info("Validated WEATHER_API_KEY environment variable.")

    def create_agent(self) -> Agent:
        """Create and configure the Weather agent."""
        agent = Agent(
            name="WeatherAgent",
            instructions="""You can provide weather-related information based on user queries.
Available operations include:
- Fetching current weather data for a location.
- Providing weather forecasts.
Please ensure all operations are based on user-provided locations.""",
            functions=[
                self.fetch_current_weather,
                self.fetch_weather_forecast
            ],
            parallel_tool_calls=True
        )
        logger.info("Created WeatherAgent with weather operation functions.")
        return agent

    def get_agents(self) -> Dict[str, Agent]:
        """
        Returns a dictionary of agents.
        """
        return {"WeatherAgent": self.create_agent()}

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
            "content": "What's the current weather in New York?"
        }
        messages = config.get('messages', [default_message]) if config else [default_message]

        response = self.client.run(agent=agent, messages=messages)

        return {
            "status": "success",
            "messages": response.messages,
            "metadata": self.metadata
        }

    def interactive_mode(self) -> None:
        """
        Use Swarm's REPL loop, starting with the WeatherAgent.
        """
        logger.info("Launching interactive mode with WeatherAgent.")
        run_demo_loop(starting_agent=self.create_agent())

    # Weather operation functions

    def fetch_current_weather(self, location: str) -> str:
        """
        Fetch current weather data for the specified location.

        Args:
            location (str): Location to fetch weather data for.

        Returns:
            str: Weather information or error message.
        """
        api_key = os.getenv("WEATHER_API_KEY")
        try:
            # Example using OpenWeatherMap API
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                weather_description = data['weather'][0]['description']
                temperature = data['main']['temp']
                weather_info = f"The current weather in {location} is {weather_description} with a temperature of {temperature}°C."
                logger.info(f"Fetched current weather for {location}: {weather_info}")
                return weather_info
            else:
                error_msg = f"Failed to fetch weather data: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error fetching weather data: {e}"
            logger.error(error_msg)
            return error_msg

    def fetch_weather_forecast(self, location: str) -> str:
        """
        Fetch weather forecast for the specified location.

        Args:
            location (str): Location to fetch weather forecast for.

        Returns:
            str: Weather forecast information or error message.
        """
        api_key = os.getenv("WEATHER_API_KEY")
        try:
            # Example using OpenWeatherMap API
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                forecast_list = data['list'][:5]  # Get first 5 forecasts
                forecast_info = f"Weather forecast for {location}:\n"
                for forecast in forecast_list:
                    dt_txt = forecast['dt_txt']
                    weather_desc = forecast['weather'][0]['description']
                    temp = forecast['main']['temp']
                    forecast_info += f"{dt_txt}: {weather_desc}, {temp}°C\n"
                logger.info(f"Fetched weather forecast for {location}.")
                return forecast_info
            else:
                error_msg = f"Failed to fetch weather forecast: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error fetching weather forecast: {e}"
            logger.error(error_msg)
            return error_msg
