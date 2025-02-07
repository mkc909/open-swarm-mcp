import os
import logging
import requests
import traceback
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent

# --------------------------------------------------------------------------
# Configure the global logger for debugging and informational messages.
# --------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class PrivateDigitalAssistantsBlueprint(BlueprintBase):
    """
    ------------------------------------------------------------------------------
    Name: Private Digital Assistants Blueprint
    ------------------------------------------------------------------------------

    This blueprint provides a comprehensive multi-agent system for personal use,
    designed to keep your data private while offering various digital assistant
    features:

    1) **Jeeves** (Starting Agent):
       - Stores and retrieves long-term memory about the user.
       - Delegates any external or specialized tasks to the appropriate agent.
       - Always returns to itself after the delegated task completes.

    2) **Mycroft** (External Data & Weather):
       - Handles external queries such as web searches (via DuckDuckGo) and Reddit discussions.
       - Contains dedicated functions to fetch current weather data and short-term forecasts.
       - After finishing a query or data retrieval, passes control back to Jeeves.

    3) **Cortana** (Analysis & Document Retrieval):
       - Performs deeper analysis, summarization, and doc retrieval (via `rag-docs`).
       - Ideal for tasks requiring advanced processing or summarizing large text corpora.
       - Returns results to Jeeves once the requested operation is complete.

    4) **Gutenberg** (WordPress Management):
       - Manages WordPress site content using the `claudeus-wp-mcp`.
       - Can create, edit, schedule posts, and handle site updates or maintenance.
       - Returns control to Jeeves after completing requested tasks.

    ------------------------------------------------------------------------------
    Use Cases & Flow:
    - A user interacts with Jeeves, who first retrieves relevant context from memory.
    - Jeeves then delegates tasks to Mycroft, Cortana, or Gutenberg as needed.
    - Each specialized agent performs its function using the relevant MCP server(s).
    - Control is returned to Jeeves for final user-facing responses or further instructions.

    ------------------------------------------------------------------------------
    Security & Environment:
    - Requires environment variables (API keys, file paths) to function correctly.
    - If any required variable is missing, it raises an error.
    - Weather data is sourced from OpenWeatherMap. WordPress tasks from `claudeus-wp-mcp`.
    - The user can maintain privacy by controlling which environment vars are set.

    ------------------------------------------------------------------------------
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Returns metadata about this blueprint:
          - title
          - description
          - required MCP servers
          - environment variables

        This data helps the Swarm framework and other systems understand what
        this blueprint needs to function, including external services and
        environment configurations.
        """
        return {
            "title": "Private Digital Assistants",
            "description": (
                "A multi-agent system providing memory-driven delegation, weather updates, "
                "web search, Reddit retrieval, document analysis, and WordPress publishing "
                "while maintaining user privacy."
            ),
            # The following MCP servers are required by the four agents:
            "required_mcp_servers": [
                "memory",            # For Jeeves to store/retrieve user data
                "duckduckgo-search", # For Mycroft to handle web queries
                "mcp-server-reddit", # For Mycroft to fetch Reddit discussions
                "claudeus-wp-mcp",   # For Gutenberg to manage WordPress
                "rag-docs",          # For Cortana to retrieve & analyze docs
            ],
            # These environment variables must be configured for the system to operate.
            "env_vars": [
                "WEATHER_API_KEY",
                "OPENAI_API_KEY",
                "QDRANT_URL",
                "QDRANT_API_KEY",
                "SERPAPI_API_KEY",
                "WP_SITES_PATH",
            ],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Creates and registers four agents:
          1) Jeeves   (Starting Agent: memory & delegation)
          2) Mycroft  (External data & weather)
          3) Cortana  (Analysis & document retrieval)
          4) Gutenberg (WordPress site management)

        Returns:
            A dictionary of agents keyed by their respective names.
        """
        # ----------------------------------------------------------------------
        # Retrieve environment variables needed to function.
        # ----------------------------------------------------------------------
        weather_api_key = os.getenv("WEATHER_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        wp_sites_path = os.getenv("WP_SITES_PATH")

        # ----------------------------------------------------------------------
        # Verify that required environment variables are available.
        # ----------------------------------------------------------------------
        required_vars = [
            "WEATHER_API_KEY",
            "OPENAI_API_KEY",
            "QDRANT_URL",
            "QDRANT_API_KEY",
            "SERPAPI_API_KEY",
            "WP_SITES_PATH",
        ]
        missing_env_vars = [var for var in required_vars if not locals()[var.lower()]]
        if missing_env_vars:
            raise EnvironmentError(
                f"Missing environment variables: {', '.join(missing_env_vars)}"
            )

        agents: Dict[str, Agent] = {}

        # ======================================================================
        # Jeeves (Starting Agent: Memory & Delegation)
        # ======================================================================
        agents["Jeeves"] = Agent(
            name="Jeeves",
            instructions=(
                "You are Jeeves, the personal assistant responsible for managing long-term memory "
                "and delegating tasks to specialized agents (Mycroft, Cortana, Gutenberg).\n\n"

                "Follow these steps for every interaction:\n"
                "1) User Identification:\n"
                "   - Assume you are interacting with 'default_user'.\n"
                "   - If not identified, proactively confirm their identity.\n\n"

                "2) Memory Retrieval:\n"
                "   - Always begin a conversation by saying only 'Remembering...'\n"
                "   - Retrieve all relevant data from your memory graph.\n\n"

                "3) Memory Usage:\n"
                "   - Pay attention to user details:\n"
                "     a) Identity (e.g. age, gender, location)\n"
                "     b) Behaviors (e.g. interests, habits)\n"
                "     c) Preferences (style, language)\n"
                "     d) Goals (targets, aspirations)\n"
                "     e) Relationships (up to 3 degrees)\n\n"

                "4) Memory Update:\n"
                "   - When new info is learned, update memory accordingly.\n"
                "   - Create or link entities (orgs, people, events) & store observations.\n\n"

                "Delegation:\n"
                "   - Mycroft handles external queries (web, weather, Reddit)\n"
                "   - Cortana handles advanced analysis, summarization, and doc retrieval\n"
                "   - Gutenberg manages WordPress content\n"
                "   - Always return control to yourself after delegation.\n"
            ),
            mcp_servers=["memory"],
            env_vars={},
        )

        # ======================================================================
        # Mycroft (External Data & Weather)
        # ======================================================================
        agents["Mycroft"] = Agent(
            name="Mycroft",
            instructions=(
                "You are Mycroft, responsible for external knowledge retrieval. "
                "You handle web searches (DuckDuckGo), weather data (OpenWeatherMap), "
                "and Reddit queries. After completing each task, return control to Jeeves."
            ),
            functions=[
                self.fetch_current_weather,
                self.fetch_weather_forecast
            ],
            mcp_servers=["duckduckgo-search", "mcp-server-reddit"],
            parallel_tool_calls=True,
            env_vars={
                "OPENAI_API_KEY": openai_api_key,
                "QDRANT_URL": qdrant_url,
                "QDRANT_API_KEY": qdrant_api_key,
                "SERPAPI_API_KEY": serpapi_api_key,
            },
        )

        # ======================================================================
        # Cortana (Analysis & Document Retrieval)
        # ======================================================================
        agents["Cortana"] = Agent(
            name="Cortana",
            instructions=(
                "You are Cortana, responsible for advanced data analysis, summarization, "
                "and retrieving contextual knowledge from various doc sources using 'rag-docs'.\n\n"
                "After completing your analysis, always return control to Jeeves."
            ),
            mcp_servers=["rag-docs"],
            env_vars={},
        )

        # ======================================================================
        # Gutenberg (WordPress Management)
        # ======================================================================
        agents["Gutenberg"] = Agent(
            name="Gutenberg",
            instructions=(
                "You are Gutenberg, responsible for managing WordPress sites and content via 'claudeus-wp-mcp'.\n"
                "Handle tasks such as creating, editing, and publishing posts, as well as general WP maintenance.\n"
                "After completing your tasks, return control to Jeeves."
            ),
            mcp_servers=["claudeus-wp-mcp"],
            env_vars={
                "WP_SITES_PATH": wp_sites_path
            },
        )

        # ----------------------------------------------------------------------
        # Handoff Functions
        # ----------------------------------------------------------------------
        def handoff_to_mycroft():
            """Delegate tasks requiring external data (web, weather, Reddit) to Mycroft."""
            return agents["Mycroft"]

        def handoff_to_cortana():
            """Delegate advanced analysis and doc retrieval tasks to Cortana."""
            return agents["Cortana"]

        def handoff_to_gutenberg():
            """Delegate WordPress management tasks to Gutenberg."""
            return agents["Gutenberg"]

        def handoff_back_to_jeeves():
            """Return control from Mycroft, Cortana, or Gutenberg back to Jeeves."""
            return agents["Jeeves"]

        # Assign handoff methods to each agent
        agents["Jeeves"].functions = [
            handoff_to_mycroft,
            handoff_to_cortana,
            handoff_to_gutenberg
        ]
        agents["Mycroft"].functions += [handoff_back_to_jeeves]
        agents["Cortana"].functions = [handoff_back_to_jeeves]
        agents["Gutenberg"].functions = [handoff_back_to_jeeves]

        # ----------------------------------------------------------------------
        # Set Jeeves as the starting agent (entry point for user requests)
        # ----------------------------------------------------------------------
        self.set_starting_agent(agents["Jeeves"])

        logger.info("Agents created: Jeeves, Mycroft, Cortana, and Gutenberg.")
        logger.debug(f"Agents registered: {list(agents.keys())}")
        return agents

    # ==========================================================================
    # Weather-Related Utility Functions (Used by Mycroft)
    # ==========================================================================
    def fetch_current_weather(self, location: str) -> str:
        """
        Fetches current weather data for the specified location via OpenWeatherMap.
        
        Args:
            location (str): The name of the city or location to retrieve weather for.
        
        Returns:
            A string describing the current weather condition and temperature in Celsius.
        
        Raises:
            An error message if fetching data fails for any reason.
        """
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            logger.debug(f"Requesting current weather data from URL: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                weather_description = data["weather"][0]["description"]
                temperature = data["main"]["temp"]
                return (
                    f"The current weather in {location} is "
                    f"{weather_description} with a temperature of {temperature}°C."
                )
            return f"Failed to fetch weather data: {response.status_code} - {response.text}"
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            traceback.print_exc()
            return "Error fetching current weather."

    def fetch_weather_forecast(self, location: str) -> str:
        """
        Fetches a brief weather forecast for the specified location via OpenWeatherMap.
        
        Args:
            location (str): The name of the city or location to retrieve forecast for.
        
        Returns:
            A multi-line string with up to five upcoming forecast entries, including
            the timestamp, weather description, and temperature in Celsius.
        
        Raises:
            An error message if fetching data fails for any reason.
        """
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
            logger.debug(f"Requesting weather forecast data from URL: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Limit forecast entries to the first five (each spaced ~3hrs apart)
                forecast_list = data["list"][:5]
                forecast_info = [f"Weather forecast for {location}:\n"]
                for forecast in forecast_list:
                    dt_txt = forecast["dt_txt"]
                    weather_desc = forecast["weather"][0]["description"]
                    temp = forecast["main"]["temp"]
                    forecast_info.append(f"{dt_txt}: {weather_desc}, {temp}°C")
                return "\n".join(forecast_info)
            return f"Failed to fetch weather forecast: {response.status_code} - {response.text}"
        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            traceback.print_exc()
            return "Error fetching weather forecast."


# ------------------------------------------------------------------------------
# If invoked directly, run this blueprint's main method to start the system.
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    PrivateDigitalAssistantsBlueprint.main()
