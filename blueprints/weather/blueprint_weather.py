# blueprints/weather/blueprint_weather.py

"""
Weather Integration Blueprint

This blueprint provides weather-related information using external APIs.
"""

from open_swarm_mcp.blueprint_base import BlueprintBase
from typing import Dict, Any, Optional
from swarm import Agent, Swarm
from swarm.repl import run_demo_loop
import logging
import requests
import traceback

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class WeatherBlueprint(BlueprintBase):
    """
    Weather Integration Blueprint Implementation.

    This blueprint uses external APIs (e.g., OpenWeatherMap) to fetch current weather
    and forecast data based on user queries. It also demonstrates handling environment
    variables for API key management.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """
        Initialize the WeatherBlueprint.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary.
            **kwargs: Additional keyword arguments for blueprint initialization.
        """
        logger.debug("Initializing WeatherBlueprint.")
        super().__init__(config=config, **kwargs)
        self.client = Swarm()
        logger.info("WeatherBlueprint initialized with Swarm client.")

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the WeatherBlueprint.

        This property defines the blueprint's metadata, including its title,
        description, required MCP servers, and any environment variables.

        Returns:
            Dict[str, Any]: A dictionary containing metadata attributes.
        """
        return {
            "title": "Weather Team",
            "description": "Provides weather-related information.",
            "required_mcp_servers": [],
            "env_vars": ["WEATHER_API_KEY"]
        }

    def validate_env_vars(self) -> None:
        """
        Validate that required environment variables are set.

        Extends the base class validation to ensure 'WEATHER_API_KEY' is available.
        """
        super().validate_env_vars()
        logger.debug("Validated environment variables for WeatherBlueprint.")

    def create_agent(self) -> Agent:
        """
        Create and configure the Weather agent.

        Returns:
            Agent: A fully configured agent for weather-related tasks.
        """
        model = self.get_model()  # Retrieve model from config or override
        agent = Agent(
            name="WeatherAgent",
            model=model,
            instructions=(
                "You can provide weather-related information based on user queries.\n"
                "Available operations include:\n"
                "- Fetching current weather data for a location.\n"
                "- Providing weather forecasts.\n"
                "Please ensure all operations are based on user-provided locations."
            ),
            functions=[
                self.fetch_current_weather,
                self.fetch_weather_forecast,
            ],
            parallel_tool_calls=True,
        )
        logger.info("WeatherAgent created with weather operation functions.")
        return agent

    def get_agents(self) -> Dict[str, Agent]:
        """
        Returns a dictionary of agents.

        Returns:
            Dict[str, Agent]: Dictionary containing WeatherAgent.
        """
        logger.debug("Fetching agents for WeatherBlueprint.")
        return {"WeatherAgent": self.create_agent()}

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        logger.debug(f"Executing WeatherBlueprint with config: {config}")
        agent = self.create_agent()
        default_message = {
            "role": "user",
            "content": "What's the current weather in New York?"
        }
        messages = config.get('messages', [default_message]) if config else [default_message]

        try:
            response = self.client.run(agent=agent, messages=messages)
            logger.debug(f"Execution response: {response}")
            return {
                "status": "success",
                "messages": response.messages,
                "metadata": self.metadata,
            }
        except Exception as e:
            error_msg = f"Error during execution: {e}"
            logger.error(error_msg)
            traceback.print_exc()
            return {"status": "error", "error": error_msg}

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
        try:
            api_key = self.get_env_var("WEATHER_API_KEY")
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
            api_key = self.get_env_var("WEATHER_API_KEY")
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


# Entry point for standalone execution
if __name__ == "__main__":
    blueprint = WeatherBlueprint()
    try:
        blueprint.interactive_mode()
    except Exception as e:
        logger.error(f"Error running Weather Blueprint: {e}")
        traceback.print_exc()
