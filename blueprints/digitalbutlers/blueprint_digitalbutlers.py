"""
DigitalButlers: Private Search and Home Automation Blueprint

A butler-themed team merging private web search and home automation:
- Jeeves (Coordinator)
- Mycroft (Web Search)
- Gutenberg (Home Automation)
"""

import os
import logging
from typing import Dict, Any

from swarm.types import Agent
from swarm.extensions.blueprint import BlueprintBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class DigitalButlersBlueprint(BlueprintBase):
    """Blueprint for private search and home automation with butler agents."""
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "DigitalButlers",
            "description": "Provides private web search and home automation.",
            "required_mcp_servers": ["memory", "duckduckgo-search", "home-assistant"],
            "env_vars": ["SERPAPI_API_KEY", "HASS_URL", "HASS_API_KEY"]
        }

    def create_agents(self) -> Dict[str, Agent]:
        serpapi_key = os.getenv("SERPAPI_API_KEY", "")
        hass_url = os.getenv("HASS_URL", "")
        hass_api_key = os.getenv("HASS_API_KEY", "")
        if not all([serpapi_key, hass_url, hass_api_key]):
            raise EnvironmentError("Missing required env vars: SERPAPI_API_KEY, HASS_URL, HASS_API_KEY")

        agents = {}

        def handoff_to_mycroft() -> Agent:
            return agents["Mycroft"]
        def handoff_to_gutenberg() -> Agent:
            return agents["Gutenberg"]
        def handoff_back_to_jeeves() -> Agent:
            return agents["Jeeves"]

        agents["Jeeves"] = Agent(
            name="Jeeves",
            instructions="You are Jeeves, the coordinator. Delegate to Mycroft for web search, Gutenberg for home automation.",
            mcp_servers=["memory"],
            functions=[handoff_to_mycroft, handoff_to_gutenberg]
        )
        agents["Mycroft"] = Agent(
            name="Mycroft",
            instructions="You are Mycroft, the web sleuth. Fetch private web data via duckduckgo-search and return to Jeeves.",
            mcp_servers=["duckduckgo-search"],
            env_vars={"SERPAPI_API_KEY": serpapi_key},
            functions=[handoff_back_to_jeeves]
        )
        agents["Gutenberg"] = Agent(
            name="Gutenberg",
            instructions="You are Gutenberg, the home scribe. Manage home devices via home-assistant and return to Jeeves.",
            mcp_servers=["home-assistant"],
            env_vars={"HASS_URL": hass_url, "HASS_API_KEY": hass_api_key},
            functions=[handoff_back_to_jeeves]
        )

        self.set_starting_agent(agents["Jeeves"])
        logger.info("Agents created: Jeeves, Mycroft, Gutenberg.")
        return agents

if __name__ == "__main__":
    DigitalButlersBlueprint.main()
