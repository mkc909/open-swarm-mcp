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

class ChaosCrewBlueprint(BlueprintBase):
    """Manages WordPress content with a streamlined multi-agent system."""
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "ChaosCrew",
            "description": "Manages WordPress content using DB-driven configs and memory.",
            "required_mcp_servers": ["memory", "server-wp-mcp"],
            "cli_name": "famties",
            "env_vars": ["WP_SITES_PATH"]
        }

    def handoff_to_brian(self) -> Agent:
        """Hands off to BrianGrifton for WordPress tasks."""
        return self.swarm.agents["BrianGrifton"]

    def create_agents(self) -> Dict[str, Agent]:
        agents = {}
        agents["PeterGrifton"] = Agent(
            name="PeterGrifton",
            instructions="You are PeterGrifton, the coordinator. Delegate WordPress tasks to BrianGrifton.",
            functions=[self.handoff_to_brian],
            mcp_servers=["memory"]
        )
        agents["BrianGrifton"] = Agent(
            name="BrianGrifton",
            instructions="You are BrianGrifton, managing WordPress content (creation, editing, SEO) via server-wp-mcp.",
            mcp_servers=["server-wp-mcp"],
            env_vars={"WP_SITES_PATH": os.getenv("WP_SITES_PATH", "")}
        )
        self.set_starting_agent(agents["PeterGrifton"])
        logger.info("Agents created: PeterGrifton, BrianGrifton.")
        return agents

if __name__ == "__main__":
    ChaosCrewBlueprint.main()
