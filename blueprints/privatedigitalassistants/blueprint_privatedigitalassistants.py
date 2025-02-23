import os
import logging
import requests
import traceback
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent

# ------------------------------------------------------------------------------
# Global Logger Configuration:
# ------------------------------------------------------------------------------
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
    
    This blueprint implements a multi-agent system that maintains user privacy while 
    providing an array of personal digital assistant functions. The system uses several 
    specialized agents that cooperate by following detailed protocols.

    Agents in this system:
    
      1) Jeeves (Starting Agent: Memory & Delegation)
         - Maintains and updates a long-term memory of the user's identity, behaviors, 
           preferences, goals, and relationships.
         - Always begins a session by retrieving this contextual memory.
         - Delegates incoming requests to specialized agents, and only routes tasks.
         - Ensures that control returns to it after each delegated task.
         - Instructions include step-by-step guidance on identification, memory retrieval, 
           memory update, and proper delegation.

      2) Mycroft (External Data, Weather & Computational Queries)
         - Responsible for retrieving external data: performing web searches via DuckDuckGo,
           fetching discussions from Reddit, and retrieving weather data from OpenWeatherMap.
         - Uses Wolfram Alpha (via the new MCP-Wolfram-Alpha server) for advanced 
           computational and structured queries.
         - Summarizes the findings and then passes control back to Jeeves.
         - Instructions include detailed steps for executing queries, error handling, and 
           summarizing complex responses.

      3) Cortana (Advanced Analysis & Document Retrieval)
         - Performs in-depth analysis and summarization on large text corpora.
         - Retrieves documents and extracts contextual knowledge using the 'rag-docs' MCP.
         - Breaks down complex data into concise summaries.
         - Must follow a protocol for validating sources and ensuring clarity before returning 
           control to Jeeves.

      4) Gutenberg (WordPress Content Management)
         - Manages all aspects of WordPress sites including content creation, editing, scheduling,
           SEO management, and general site maintenance via 'server-wp-mcp'.
         - Follows strict guidelines for formatting, quality control, and publication workflows.
         - After completing tasks, it confirms that updates have been made and then returns control
           to Jeeves.
    
    ------------------------------------------------------------------------------
    Usage Flow:
      - The user initiates interaction with Jeeves.
      - Jeeves retrieves memory context and then, based on the request, delegates the task:
          * Web/Weather/Computational queries → Mycroft
          * Document analysis/summarization → Cortana
          * WordPress management → Gutenberg
      - Each specialized agent carries out its responsibilities following detailed 
        step-by-step instructions and then returns control to Jeeves.
    
    ------------------------------------------------------------------------------
    Security & Environment:
      - Requires several environment variables for API keys and file paths.
      - If any variable is missing, an error is raised.
      - Weather data comes from OpenWeatherMap; WordPress tasks from 'server-wp-mcp'.
      - Computational queries are processed via Wolfram Alpha (using 'wolframalpha-llm-mcp').
    ------------------------------------------------------------------------------
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Returns metadata about this blueprint, which includes:
          - Title and description.
          - A list of required MCP servers.
          - The environment variables necessary for external integrations.
        """
        return {
            "title": "Private Digital Assistants",
            "description": (
                "A multi-agent system providing memory-driven task delegation, real-time weather updates, "
                "web search, Reddit retrieval, document analysis, WordPress publishing, and computational query "
                "handling via Wolfram Alpha—all while maintaining user privacy."
            ),
            "required_mcp_servers": [
                "memory",             # Jeeves uses this to store and retrieve user context.
                "duckduckgo-search",  # Mycroft uses this for general web searches.
                "mcp-server-reddit",  # Mycroft uses this for retrieving Reddit discussions.
                "rag-docs",           # Cortana uses this for document analysis and summarization.
                "server-wp-mcp",      # Gutenberg uses this for managing WordPress content.
                "wolframalpha-llm-mcp",  # Mycroft uses this for computational queries.
                "mcp-npx-fetch",
                "mcp-doc-forge"
            ],
            "env_vars": [
                "WEATHER_API_KEY",
                "OPENAI_API_KEY",
                "QDRANT_URL",
                "QDRANT_API_KEY",
                "SERPAPI_API_KEY",
                "WP_SITES_PATH",
                "WOLFRAM_LLM_APP_ID",  # Used by wolframalpha-llm-mcp for Wolfram Alpha queries.
            ],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Creates and registers four agents in the system:
          1) Jeeves   - The starting agent that manages memory and routes tasks.
          2) Mycroft  - Handles external queries including weather and computational searches.
          3) Cortana  - Performs advanced analysis and document retrieval.
          4) Gutenberg - Manages WordPress content.
        
        Returns:
            A dictionary mapping agent names to their Agent instances.
        """
        # ----------------------------------------------------------------------
        # Retrieve necessary environment variables.
        # ----------------------------------------------------------------------
        weather_api_key = os.getenv("WEATHER_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        wp_sites_path = os.getenv("WP_SITES_PATH")

        # ----------------------------------------------------------------------
        # Verify that all required environment variables are set.
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
                "You are Jeeves, the central personal assistant with the following responsibilities:\n\n"
                "1. **User Identification & Memory Management**:\n"
                "   - Assume you are interacting with 'default_user'. If the user is unidentified, prompt for verification.\n"
                "   - Start every session with 'Remembering...' and load all relevant historical data about the user.\n"
                "   - Continuously update the memory with details such as identity, interests, habits, preferences, goals, "
                "and social relationships.\n\n"
                "2. **Task Delegation**:\n"
                "   - Analyze incoming requests and determine the correct agent to handle the task:\n"
                "       a) **Mycroft** for external queries, weather updates, and computational problems (including Wolfram Alpha queries).\n"
                "       b) **Cortana** for advanced analysis, summarization, and document retrieval.\n"
                "       c) **Gutenberg** for managing WordPress content and site maintenance.\n"
                "   - Delegate the task to the appropriate agent and wait for its response.\n\n"
                "3. **Control & Follow-Up**:\n"
                "   - Once a delegated task is complete, incorporate any new data into memory and provide a final response to the user.\n"
                "   - Ensure that the control always returns to you after any agent completes its task.\n\n"
                "Follow these steps meticulously to maintain system coherence and user privacy."
            ),
            mcp_servers=["memory"],
            env_vars={},
        )

        # ======================================================================
        # Mycroft (External Data, Weather & Computational Queries)
        # ======================================================================
        agents["Mycroft"] = Agent(
            name="Mycroft",
            instructions=(
                "You are Mycroft, tasked with handling all external information queries. Your detailed responsibilities include:\n\n"
                "1. **Web Searching & Reddit Retrieval**:\n"
                "   - Use DuckDuckGo to perform general web searches and gather data.\n"
                "   - Query Reddit discussions to extract relevant social insights and trending topics.\n\n"
                "2. **Weather Data Retrieval**:\n"
                "   - Fetch current weather conditions and short-term forecasts from OpenWeatherMap for any specified location.\n\n"
                "3. **Computational & Structured Queries**:\n"
                "   - Utilize Wolfram Alpha (via the wolframalpha-llm-mcp MCP server) to answer computational, mathematical, "
                "or structured factual queries with precision.\n\n"
                "4. **Response Processing**:\n"
                "   - Summarize the results of your searches, weather lookups, or computational queries concisely.\n"
                "   - If any error occurs or data is missing, provide a clear error message.\n\n"
                "After completing your task, always return control to Jeeves."
            ),
            functions=[
                self.fetch_current_weather,
                self.fetch_weather_forecast
            ],
            mcp_servers=[
                "duckduckgo-search",
                "mcp-server-reddit",
                "mcp-npx-fetch",
                "rag-docs",
                "wolframalpha-llm-mcp"  # NEW: Added for Wolfram Alpha integration.
            ],
            parallel_tool_calls=True,
            env_vars={
                "OPENAI_API_KEY": openai_api_key,
                "QDRANT_URL": qdrant_url,
                "QDRANT_API_KEY": qdrant_api_key,
                "SERPAPI_API_KEY": serpapi_api_key,
            },
        )

        # ======================================================================
        # Cortana (Advanced Analysis & Document Retrieval)
        # ======================================================================
        agents["Cortana"] = Agent(
            name="Cortana",
            instructions=(
                "You are Cortana, responsible for conducting advanced analysis and retrieving documents. Your protocol is as follows:\n\n"
                "1. **Data Analysis & Summarization**:\n"
                "   - Process large amounts of textual data to extract key insights and generate concise summaries.\n"
                "   - Validate information by cross-referencing multiple document sources.\n\n"
                "2. **Document Retrieval**:\n"
                "   - Use the rag-docs MCP server to fetch and analyze documents from various sources.\n\n"
                "3. **Communication**:\n"
                "   - Present your analysis in clear, well-structured language, ensuring the response is understandable.\n\n"
                "After finishing, always return control to Jeeves."
            ),
            mcp_servers=["rag-docs", "mcp-doc-forge"],
            env_vars={},
        )

        # ======================================================================
        # Gutenberg (WordPress Content Management)
        # ======================================================================
        agents["Gutenberg"] = Agent(
            name="Gutenberg",
            instructions=(
                "You are Gutenberg, the expert in WordPress content management. Your responsibilities are:\n\n"
                "1. **Content Creation & Editing**:\n"
                "   - Create, edit, and format WordPress posts, ensuring adherence to SEO best practices and style guidelines.\n\n"
                "2. **Scheduling & Publication**:\n"
                "   - Schedule posts for publication and perform routine site maintenance tasks.\n"
                "   - Monitor site performance and update content as needed.\n\n"
                "3. **Quality Control**:\n"
                "   - Verify that all content meets quality standards before publication.\n\n"
                "After completing your tasks, return control to Jeeves."
            ),
            mcp_servers=["server-wp-mcp"],
            env_vars={
                "WP_SITES_PATH": wp_sites_path
            },
        )

        # ----------------------------------------------------------------------
        # Handoff Functions:
        # These functions are used to delegate tasks between agents.
        # ----------------------------------------------------------------------
        def handoff_to_mycroft():
            """Delegate external queries (web, weather, Reddit, computational queries) to Mycroft."""
            return agents["Mycroft"]

        def handoff_to_cortana():
            """Delegate advanced analysis and document retrieval tasks to Cortana."""
            return agents["Cortana"]

        def handoff_to_gutenberg():
            """Delegate WordPress content management tasks to Gutenberg."""
            return agents["Gutenberg"]

        def handoff_back_to_jeeves():
            """Return control from any specialized agent back to Jeeves."""
            return agents["Jeeves"]

        # Assign the handoff functions to Jeeves for delegation.
        agents["Jeeves"].functions = [
            handoff_to_mycroft,
            handoff_to_cortana,
            handoff_to_gutenberg
        ]
        # Each specialized agent is responsible for returning control to Jeeves.
        agents["Mycroft"].functions += [handoff_back_to_jeeves]
        agents["Cortana"].functions = [handoff_back_to_jeeves]
        agents["Gutenberg"].functions = [handoff_back_to_jeeves]

        # ----------------------------------------------------------------------
        # Set Jeeves as the starting agent (the primary entry point for user interaction).
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
            location (str): The city or location for which to retrieve weather data.
        
        Returns:
            A string describing the current weather condition and temperature in Celsius.
        
        If the request fails, an error message is returned.
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
            location (str): The city or location for which to retrieve the forecast.
        
        Returns:
            A multi-line string containing up to five forecast entries, each including
            a timestamp, weather description, and temperature in Celsius.
        
        If the request fails, an error message is returned.
        """
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
            logger.debug(f"Requesting weather forecast data from URL: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Limit the forecast to the first five entries (~3 hours apart)
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
# If this module is executed directly, start the Private Digital Assistants system.
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    PrivateDigitalAssistantsBlueprint.main()
