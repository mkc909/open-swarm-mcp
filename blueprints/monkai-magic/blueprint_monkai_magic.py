"""
MonkaiMagic: Cloud Operations Journey Blueprint

A *Monkai Magic*-inspired crew managing AWS, Fly.io, and Vercel with pre-authenticated CLIs:
- Tripitaka (Wise Leader/Coordinator)
- Monkey (Cloud Trickster/AWS Master)
- Pigsy (Greedy Tinker/CLI Handler)
- Sandy (River Sage/Ops Watcher)

Assumes pre-authenticated aws, flyctl, and vercel commands; optional env vars hint at defaults in instructions.
Tripitaka delegates based on role awareness, no memory tracking.
"""

import os
import logging
import subprocess
from typing import Dict, Any

from swarm.types import Agent
from swarm.extensions.blueprint import BlueprintBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

# Cloud CLI Functions
def aws_cli(command: str) -> str:
    """Executes an AWS CLI command and returns output."""
    try:
        full_cmd = f"aws {command}"
        logger.debug(f"Executing AWS CLI: {full_cmd}")
        result = subprocess.run(full_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"AWS CLI error: {e.stderr}")
        return f"Error: {e.stderr}"

def fly_cli(command: str) -> str:
    """Executes a Fly.io CLI command and returns output."""
    try:
        full_cmd = f"flyctl {command}"
        logger.debug(f"Executing Fly CLI: {full_cmd}")
        result = subprocess.run(full_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Fly CLI error: {e.stderr}")
        return f"Error: {e.stderr}"

def vercel_cli(command: str) -> str:
    """Executes a Vercel CLI command and returns output."""
    try:
        full_cmd = f"vercel {command}"
        logger.debug(f"Executing Vercel CLI: {full_cmd}")
        result = subprocess.run(full_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Vercel CLI error: {e.stderr}")
        return f"Error: {e.stderr}"

TOOLS = {
    "aws_cli": aws_cli,
    "fly_cli": fly_cli,
    "vercel_cli": vercel_cli
}

class MonkaiMagicBlueprint(BlueprintBase):
    """
    Blueprint for a cloud operations team inspired by *Monkai Magic*.

    Agents:
      - Tripitaka: Wise Leader/Coordinator, delegates without memory tracking.
      - Monkey: Cloud Trickster/AWS Master managing AWS CLI operations.
      - Pigsy: Greedy Tinker/CLI Handler for Fly.io and Vercel.
      - Sandy: River Sage/Ops Watcher with shell diagnostics.

    Assumes pre-authenticated aws, flyctl, and vercel commands; optional env vars (AWS_REGION, FLY_REGION, VERCEL_ORG_ID)
    hint at defaults in instructions.
    """
    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the MonkaiMagic blueprint.

        Returns:
            Dict[str, Any]: Dictionary of title, description, MCP servers; no required env vars.
        """
        return {
            "title": "MonkaiMagic: Cloud Operations Journey",
            "description": "A *Monkai Magic*-inspired crew managing AWS, Fly.io, and Vercel with pre-authenticated CLI tools.",
            "required_mcp_servers": ["mcp-shell"],
            "env_vars": []  # No required env vars; optional hints in instructions
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Creates 4 agents for cloud operations with *Monkai Magic* roles.

        Dynamically amends instructions with optional env var hints (AWS_REGION, FLY_REGION, VERCEL_ORG_ID).
        Tripitaka delegates based on role awareness, no memory tracking.

        Returns:
            Dict[str, Agent]: Dictionary mapping agent names to Agent instances.
        """
        # Optional env vars for hinting defaults
        aws_region = os.getenv("AWS_REGION")
        fly_region = os.getenv("FLY_REGION")
        vercel_org_id = os.getenv("VERCEL_ORG_ID")

        agents: Dict[str, Agent] = {}

        # Tripitaka: Wise Leader/Coordinator
        tripitaka_instructions = (
            "You are Tripitaka, the wise leader guiding the cloud journey:\n"
            "- Lead with calm wisdom, delegating to: Monkey (AWS mastery), Pigsy (Fly.io/Vercel tinkering), Sandy (ops watching).\n"
            "- No memory tracking—just know your crew’s roles and hand off tasks."
        )
        agents["Tripitaka"] = Agent(
            name="Tripitaka",
            instructions=tripitaka_instructions,
            mcp_servers=[],
            env_vars={}
        )

        # Monkey: Cloud Trickster/AWS Master
        monkey_instructions = (
            "You are Monkey, the cloud trickster and AWS master:\n"
            "- Wreak havoc on AWS with aws_cli tool, deploying and scaling with wild flair.\n"
            "- Assumes aws command is pre-authenticated; use it directly.\n"
            "- Return to Tripitaka or hand off to Sandy for a watchful eye."
        )
        if aws_region:
            monkey_instructions += f"\n- Hint: AWS_REGION={aws_region} is set; prefer this region unless specified otherwise."
        agents["Monkey"] = Agent(
            name="Monkey",
            instructions=monkey_instructions,
            mcp_servers=[],
            env_vars={},
            tools={"aws_cli": TOOLS["aws_cli"]}
        )

        # Pigsy: Greedy Tinker/CLI Handler
        pigsy_instructions = (
            "You are Pigsy, the greedy tinker of CLI hosting:\n"
            "- Gobble up Fly.io with fly_cli tool, Vercel with vercel_cli tool.\n"
            "- Assumes flyctl and vercel commands are pre-authenticated; use them directly.\n"
            "- Return to Tripitaka or hand off to Sandy when stuffed."
        )
        if fly_region:
            pigsy_instructions += f"\n- Hint: FLY_REGION={fly_region} is set; prefer this region for Fly.io unless overridden."
        if vercel_org_id:
            pigsy_instructions += f"\n- Hint: VERCEL_ORG_ID={vercel_org_id} is set; target this org for Vercel unless specified."
        agents["Pigsy"] = Agent(
            name="Pigsy",
            instructions=pigsy_instructions,
            mcp_servers=[],
            env_vars={},
            tools={"fly_cli": TOOLS["fly_cli"], "vercel_cli": TOOLS["vercel_cli"]}
        )

        # Sandy: River Sage/Ops Watcher
        sandy_instructions = (
            "You are Sandy, the river sage and ops watcher:\n"
            "- Use mcp-shell to monitor the flowing currents of cloud deployments from Monkey or Pigsy.\n"
            "- Return steady reports to Tripitaka."
        )
        agents["Sandy"] = Agent(
            name="Sandy",
            instructions=sandy_instructions,
            mcp_servers=["mcp-shell"],
            env_vars={}
        )

        # Handoff Functions
        def handoff_to_monkey() -> Agent:
            """Delegates to Monkey (AWS Master)."""
            return agents["Monkey"]

        def handoff_to_pigsy() -> Agent:
            """Delegates to Pigsy (CLI Handler)."""
            return agents["Pigsy"]

        def handoff_to_sandy() -> Agent:
            """Delegates to Sandy (Ops Watcher)."""
            return agents["Sandy"]

        def handoff_back_to_tripitaka() -> Agent:
            """Returns control to Tripitaka."""
            return agents["Tripitaka"]

        # Assign Functions
        agents["Tripitaka"].functions = [handoff_to_monkey, handoff_to_pigsy, handoff_to_sandy]
        agents["Monkey"].functions = [handoff_back_to_tripitaka, handoff_to_sandy]
        agents["Pigsy"].functions = [handoff_back_to_tripitaka, handoff_to_sandy]
        agents["Sandy"].functions = [handoff_back_to_tripitaka]

        self.set_starting_agent(agents["Tripitaka"])
        logger.info("MonkaiMagic Team created.")
        logger.debug(f"Agents registered: {list(agents.keys())}")
        return agents

if __name__ == "__main__":
    MonkaiMagicBlueprint.main()
