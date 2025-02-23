import os
import logging
import requests
import json
import traceback
from typing import Dict, Any, List

from swarm.types import Agent
from swarm.extensions.blueprint import BlueprintBase

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class DigitalButlerSquadBlueprint(BlueprintBase):
    """
    A multi-agent system of digital butlers providing privacy-focused assistance.
    Agents: Jeeves (memory/delegation), Mycroft (external data), Cortana (analysis),
    Gutenberg (WordPress). Configurable via /v1/agent/instructions/.
    """
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "Digital Butler Squad",
            "description": (
                "A team of privacy-focused digital assistants handling memory, external queries, "
                "analysis, and WordPress management, configurable via Django DB and REST API."
            ),
            "required_mcp_servers": [
                "memory", "duckduckgo-search", "mcp-server-reddit", "rag-docs",
                "server-wp-mcp", "wolframalpha-llm-mcp", "mcp-npx-fetch", "mcp-doc-forge"
            ],
            "env_vars": [
                "WEATHER_API_KEY", "OPENAI_API_KEY", "QDRANT_URL", "QDRANT_API_KEY",
                "SERPAPI_API_KEY", "WP_SITES_PATH", "WOLFRAM_LLM_APP_ID"
            ],
            "django_modules": {
                "models": "blueprints.digital_butler_squad.models",
                "views": "blueprints.digital_butler_squad.views",
                "urls": "blueprints.digital_butler_squad.urls",
                "serializers": "blueprints.digital_butler_squad.serializers"
            },
            "url_prefix": "v1/agent/"  # Shared with dilbot_universe
        }

    def __init__(self, config: dict, **kwargs):
        config.setdefault("llm", {"default": {"dummy": "value"}})
        super().__init__(config=config, **kwargs)
        self._ensure_sample_data()

    def _ensure_sample_data(self) -> None:
        from blueprints.digital_butler_squad.models import AgentInstruction
        if AgentInstruction.objects.count() == 0:
            logger.info("No agent instructions found. Loading sample data...")
            sample_instructions = [
                {
                    "agent_name": "Jeeves",
                    "instruction_text": (
                        "You are Jeeves, the central assistant:\n"
                        "1. Start with 'Remembering...' and load user memory.\n"
                        "2. Delegate tasks: Mycroft (external), Cortana (analysis), Gutenberg (WordPress).\n"
                        "3. Update memory and return control to yourself after delegation."
                    ),
                    "model": "default",
                    "env_vars": json.dumps({"DEBUG": "true"}),
                    "mcp_servers": json.dumps(["memory"])
                },
                {
                    "agent_name": "Mycroft",
                    "instruction_text": (
                        "You are Mycroft, handling external data:\n"
                        "1. Fetch web searches, Reddit posts, weather, or Wolfram Alpha answers.\n"
                        "2. Summarize results clearly.\n"
                        "3. Return control to Jeeves."
                    ),
                    "model": "gpt-4o-mini",
                    "env_vars": json.dumps({
                        "WEATHER_API_KEY": os.getenv("WEATHER_API_KEY", ""),
                        "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY", "")
                    }),
                    "mcp_servers": json.dumps([
                        "duckduckgo-search", "mcp-server-reddit", "wolframalpha-llm-mcp",
                        "mcp-npx-fetch"
                    ])
                },
                {
                    "agent_name": "Cortana",
                    "instruction_text": (
                        "You are Cortana, analyzing data:\n"
                        "1. Summarize large texts and retrieve documents via rag-docs.\n"
                        "2. Validate sources and clarify findings.\n"
                        "3. Return control to Jeeves."
                    ),
                    "model": "default",
                    "env_vars": json.dumps({"QDRANT_URL": os.getenv("QDRANT_URL", "")}),
                    "mcp_servers": json.dumps(["rag-docs", "mcp-doc-forge"])
                },
                {
                    "agent_name": "Gutenberg",
                    "instruction_text": (
                        "You are Gutenberg, managing WordPress:\n"
                        "1. Create/edit/schedule WordPress content with SEO.\n"
                        "2. Ensure quality and confirm updates.\n"
                        "3. Return control to Jeeves."
                    ),
                    "model": "default",
                    "env_vars": json.dumps({"WP_SITES_PATH": os.getenv("WP_SITES_PATH", "")}),
                    "mcp_servers": json.dumps(["server-wp-mcp"])
                }
            ]
            for data in sample_instructions:
                AgentInstruction.objects.create(**data)
            logger.info("Sample agent instructions loaded successfully.")
        else:
            logger.info("Agent instructions already exist. Skipping sample data loading.")

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        from blueprints.digital_butler_squad.models import AgentInstruction
        try:
            instruction = AgentInstruction.objects.get(agent_name=agent_name)
            return {
                "instructions": instruction.instruction_text,
                "model": instruction.model,
                "env_vars": json.loads(instruction.env_vars) if instruction.env_vars else {},
                "mcp_servers": json.loads(instruction.mcp_servers) if instruction.mcp_servers else []
            }
        except AgentInstruction.DoesNotExist:
            logger.warning(f"No config found for agent '{agent_name}'. Using defaults.")
            return {
                "instructions": f"You are {agent_name}, a helpful assistant.",
                "model": "default",
                "env_vars": {},
                "mcp_servers": []
            }

    # Static Functions (for Mycroft)
    def fetch_current_weather(self, location: str) -> str:
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            logger.debug(f"Requesting current weather data from URL: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                weather_description = data["weather"][0]["description"]
                temperature = data["main"]["temp"]
                return f"Current weather in {location}: {weather_description}, {temperature}°C."
            return f"Failed to fetch weather data: {response.status_code} - {response.text}"
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            traceback.print_exc()
            return "Error fetching current weather."

    def fetch_weather_forecast(self, location: str) -> str:
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
            logger.debug(f"Requesting weather forecast data from URL: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
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

    # Handoff Functions
    def handoff_to_mycroft(self) -> Agent:
        return self.swarm.agents["Mycroft"]

    def handoff_to_cortana(self) -> Agent:
        return self.swarm.agents["Cortana"]

    def handoff_to_gutenberg(self) -> Agent:
        return self.swarm.agents["Gutenberg"]

    def handoff_back_to_jeeves(self) -> Agent:
        return self.swarm.agents["Jeeves"]

    def create_agents(self) -> Dict[str, Agent]:
        # Helper to create an agent with DB config
        def create_agent(name: str, functions: List) -> Agent:
            config = self.get_agent_config(name)
            return Agent(
                name=name,
                instructions=lambda ctx: config["instructions"],
                functions=functions,
                model=config["model"],
                env_vars=config["env_vars"],
                mcp_servers=config["mcp_servers"]
            )

        agents = {}

        # Jeeves (Starting Agent)
        agents["Jeeves"] = create_agent(
            "Jeeves",
            [self.handoff_to_mycroft, self.handoff_to_cortana, self.handoff_to_gutenberg]
        )

        # Mycroft (External Data)
        agents["Mycroft"] = create_agent(
            "Mycroft",
            [self.fetch_current_weather, self.fetch_weather_forecast, self.handoff_back_to_jeeves]
        )

        # Cortana (Analysis)
        agents["Cortana"] = create_agent(
            "Cortana",
            [self.handoff_back_to_jeeves]
        )

        # Gutenberg (WordPress)
        agents["Gutenberg"] = create_agent(
            "Gutenberg",
            [self.handoff_back_to_jeeves]
        )

        self.set_starting_agent(agents["Jeeves"])
        logger.info("Agents created: Jeeves, Mycroft, Cortana, Gutenberg.")
        return agents

if __name__ == "__main__":
    DigitalButlerSquadBlueprint.main()
