import os
import logging
import requests
import json
import traceback
from typing import Dict, Any, List

from swarm.types import Agent
from swarm.extensions.blueprint import BlueprintBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class CHCBlueprint(BlueprintBase):
    """ChaosCrew - A multi-agent team with static weather functions and DB/REST."""
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "ChaosCrew",
            "description": "A Grifton family team managing chaotic tasks with DB-driven configs.",
            "required_mcp_servers": [
                "memory", "duckduckgo-search", "mcp-server-reddit", "rag-docs",
                "server-wp-mcp", "wolframalpha-llm-mcp", "mcp-npx-fetch", "mcp-doc-forge"
            ],
            "env_vars": [
                "WEATHER_API_KEY", "OPENAI_API_KEY", "QDRANT_URL", "QDRANT_API_KEY",
                "SERPAPI_API_KEY", "WP_SITES_PATH", "WOLFRAM_LLM_APP_ID"
            ],
            "django_modules": {
                "models": "blueprints.chc.models",
                "views": "blueprints.chc.views",
                "urls": "blueprints.chc.urls",
                "serializers": "blueprints.chc.serializers"
            },
            "url_prefix": "v1/agent/"
        }

    def __init__(self, config: dict, **kwargs):
        config.setdefault("llm", {"default": {"dummy": "value"}})
        super().__init__(config=config, **kwargs)
        self._ensure_sample_data()

    def _ensure_sample_data(self) -> None:
        from blueprints.chc.models import AgentInstruction
        if AgentInstruction.objects.count() == 0:
            logger.info("No agent instructions found. Loading sample data...")
            sample_instructions = [
                {
                    "agent_name": "PeterGrifton",
                    "instruction_text": (
                        "You’re Peter Grifton, chaos coordinator:\n"
                        "1. Start with 'Heh, let’s see what I remember...' and load memory.\n"
                        "2. Delegate: LoisGrifton (external), StewieGrifton (analysis), BrianGrifton (WordPress).\n"
                        "3. Log updates and keep control."
                    ),
                    "model": "default",
                    "env_vars": json.dumps({"DEBUG": "true"}),
                    "mcp_servers": json.dumps(["memory"])
                },
                {
                    "agent_name": "LoisGrifton",
                    "instruction_text": (
                        "You’re Lois Grifton, sensible chaos tamer:\n"
                        "1. Fetch web, Reddit, weather, or Wolfram data.\n"
                        "2. Sum it up quick.\n"
                        "3. Return to PeterGrifton."
                    ),
                    "model": "gpt-4o-mini",
                    "env_vars": json.dumps({
                        "WEATHER_API_KEY": os.getenv("WEATHER_API_KEY", ""),
                        "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY", ""),
                        "WOLFRAM_LLM_APP_ID": os.getenv("WOLFRAM_LLM_APP_ID", "")
                    }),
                    "mcp_servers": json.dumps([
                        "duckduckgo-search", "mcp-server-reddit", "wolframalpha-llm-mcp",
                        "mcp-npx-fetch"
                    ])
                },
                {
                    "agent_name": "StewieGrifton",
                    "instruction_text": (
                        "You’re Stewie Grifton, evil genius:\n"
                        "1. Analyze texts and fetch docs with rag-docs.\n"
                        "2. Condense findings.\n"
                        "3. Return to PeterGrifton."
                    ),
                    "model": "default",
                    "env_vars": json.dumps({"QDRANT_URL": os.getenv("QDRANT_URL", "")}),
                    "mcp_servers": json.dumps(["rag-docs", "mcp-doc-forge"])
                },
                {
                    "agent_name": "BrianGrifton",
                    "instruction_text": (
                        "You’re Brian Grifton, smug scribe:\n"
                        "1. Manage WordPress content with SEO.\n"
                        "2. Confirm updates.\n"
                        "3. Return to PeterGrifton."
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
        from blueprints.chc.models import AgentInstruction
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
                "instructions": f"You are {agent_name}, a chaotic helper.",
                "model": "default",
                "env_vars": {},
                "mcp_servers": []
            }

    def fetch_current_weather(self, location: str) -> str:
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                weather_description = data["weather"][0]["description"]
                temperature = data["main"]["temp"]
                return f"Current weather in {location}: {weather_description}, {temperature}°C."
            return f"Failed to fetch weather data: {response.status_code}"
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return "Weather fetch failed."

    def handoff_to_lois(self) -> Agent:
        return self.swarm.agents["LoisGrifton"]
    def handoff_to_stewie(self) -> Agent:
        return self.swarm.agents["StewieGrifton"]
    def handoff_to_brian(self) -> Agent:
        return self.swarm.agents["BrianGrifton"]
    def handoff_to_peter(self) -> Agent:
        return self.swarm.agents["PeterGrifton"]

    def handoff_to_peter(self) -> Agent:
        return self.swarm.agents["PeterGriffin"]

    def create_agents(self) -> Dict[str, Agent]:
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
        agents["PeterGriffin"] = create_agent(
            "PeterGriffin",
            [self.handoff_to_lois, self.handoff_to_stewie, self.handoff_to_brian]
        )
        agents["LoisGriffin"] = create_agent(
            "LoisGriffin",
            [self.fetch_current_weather, self.handoff_to_peter]
        )
        agents["StewieGriffin"] = create_agent(
            "StewieGriffin",
            [self.handoff_to_peter]
        )
        agents["BrianGriffin"] = create_agent(
            "BrianGriffin",
            [self.handoff_to_peter]
        )
        self.set_starting_agent(agents["PeterGriffin"])
        logger.info("Agents created: Peter, Lois, Stewie, Brian.")
        return agents

if __name__ == "__main__":
    CHCBlueprint.main()
