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

class TSRBlueprint(BlueprintBase):
    """TaskRiser - A team of Taskmaster hosts wielding uvx servers."""
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "TaskRiser",
            "description": "Agents named after Taskmaster hosts, using uvx servers for transcripts and computations.",
            "required_mcp_servers": ["youtube-transcript", "wolframalpha-llm-mcp"],
            "env_vars": ["WOLFRAM_LLM_APP_ID"]
        }

    def placeholder(self, text: str) -> str:
        """Placeholder function until uvx is fixed."""
        logger.info(f"Placeholder for {text}")
        return f"Awaiting uvx fix: {text}"

    def handoff_to_tom(self) -> Agent:
        return self.swarm.agents["Tom"]

    def handoff_to_louis(self) -> Agent:
        return self.swarm.agents["Louis"]

    def handoff_to_lasse(self) -> Agent:
        return self.swarm.agents["Lasse"]

    def handoff_to_greg(self) -> Agent:
        return self.swarm.agents["Greg"]

    def create_agents(self) -> Dict[str, Agent]:
        agents = {}
        agents["Greg"] = Agent(
            name="Greg",
            instructions="You’re Greg (UK Taskmaster). Delegate tasks to Tom, Louis, or Lasse.",
            functions=[self.handoff_to_tom, self.handoff_to_louis, self.handoff_to_lasse]
        )
        agents["Tom"] = Agent(
            name="Tom",
            instructions="You’re Tom (AU Taskmaster). Use youtube-transcript when uvx works.",
            functions=[self.placeholder, self.handoff_to_greg],
            mcp_servers=["youtube-transcript"]
        )
        agents["Louis"] = Agent(
            name="Louis",
            instructions="You’re Louis (CA Taskmaster). Use wolframalpha-llm-mcp when uvx works.",
            functions=[self.placeholder, self.handoff_to_greg],
            mcp_servers=["wolframalpha-llm-mcp"],
            env_vars={"WOLFRAM_LLM_APP_ID": os.getenv("WOLFRAM_LLM_APP_ID", "")}
        )
        agents["Lasse"] = Agent(
            name="Lasse",
            instructions="You’re Lasse (DK Taskmaster). Assist with transcripts or computations.",
            functions=[self.placeholder, self.handoff_to_greg],
            mcp_servers=["youtube-transcript", "wolframalpha-llm-mcp"]
        )
        self.set_starting_agent(agents["Greg"])
        logger.info("Agents created: Greg, Tom, Louis, Lasse.")
        return agents

if __name__ == "__main__":
    TSRBlueprint.main()
