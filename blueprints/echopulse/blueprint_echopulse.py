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

class EPLBlueprint(BlueprintBase):
    """EchoPulse - A simple single-agent blueprint with an echo function."""
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "EchoPulse",
            "description": "A basic agent that echoes user input.",
            "required_mcp_servers": [],
            "env_vars": []
        }

    def echo(self, text: str) -> str:
        """Echoes the input text back to the user."""
        logger.info(f"Echoing: {text}")
        return f"Echo: {text}"

    def create_agents(self) -> Dict[str, Agent]:
        agent = Agent(
            name="EchoAgent",
            instructions="You’re the EchoAgent. Echo back whatever the user says.",
            functions=[self.echo]
        )
        self.set_starting_agent(agent)
        logger.info("EchoAgent created.")
        return {"EchoAgent": agent}

if __name__ == "__main__":
    EPLBlueprint.main()
