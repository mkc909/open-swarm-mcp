# blueprints/sysadmin/blueprint_sysadmin_extended.py

"""
Sysadmin Blueprint Class for Open Swarm.

This blueprint defines Morpheus as the TriageAgent and assistant agents
Trinity, Neo, and Oracle focused on filesystem management,
running shell scripts, and Brave Search integration.
"""

import logging
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.settings import DEBUG
from swarm.types import Agent

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class SysadminBlueprint(BlueprintBase):
    """
    A blueprint defining Morpheus as the TriageAgent and assistant agents Trinity, Neo, and Oracle
    for filesystem management, running shell scripts, and Brave Search integration.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the SysadminBlueprint.

        Returns:
            Dict[str, Any]: Metadata with title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "Sysadmin  Blueprint",
            "description": (
                "Provides Morpheus as the TriageAgent and assistant agents for MCP-based system administration: "
                "filesystem management, running shell scripts, and Brave Search integration."
            ),
            "required_mcp_servers": [
                "filesystem",
                "run-shell",
                "brave-search",
            ],
            "env_vars": [
                "ALLOWED_PATH",
                "BRAVE_API_KEY",
            ],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create agents for the SysadminBlueprint, including Morpheus as the TriageAgent
        and assistant agents Trinity, Neo, and Oracle.

        Returns:
            Dict[str, Agent]: Dictionary of created agents.
        """
        import os

        # Retrieve environment variables
        allowed_paths = os.getenv("ALLOWED_PATH", "/default/path")
        brave_api_key = os.getenv("BRAVE_API_KEY", "default-brave-key")

        # Dictionary to hold all agents
        agents: Dict[str, Agent] = {}

        # Define Morpheus as the TriageAgent
        agents["Morpheus"] = Agent(
            name="Morpheus",
            instructions=(
                "You are Morpheus, the TriageAgent responsible for overseeing and delegating tasks to assistant agents. "
                "You can delegate tasks to any assistant agent but cannot perform the tasks directly."
            ),
            env_vars={},
        )

        # Define assistant agents with Matrix-themed names
        agents["Trinity"] = Agent(
            name="Trinity",
            instructions=(
                "You are Trinity, managing and interacting with the filesystem under allowed paths. "
                "You have been provided with the tools needed to do this. "
                "After executing filesystem tools on behalf of the user, you may pass back to Morpheus."
            ),
            mcp_servers=["filesystem"],
            env_vars={"ALLOWED_PATH": allowed_paths},
        )

        agents["Neo"] = Agent(
            name="Neo",
            instructions=(
                "You are Neo, executing shell scripts located at the specified script path. "
                "Ensure scripts are executed securely and return control back to Morpheus after completion."
            ),
            mcp_servers=["mcp-shell"]
        )

        agents["Oracle"] = Agent(
            name="Oracle",
            instructions=(
                "You are Oracle, performing search queries using the Brave Search MCP server. "
                "Utilize the Brave API key for authenticated search operations as directed by Morpheus."
            ),
            mcp_servers=["brave-search"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
        )

        # Define handoff functions
        def handoff_to_trinity():
            logger.debug("Morpheus is handing off to Trinity")
            return agents["Trinity"]

        def handoff_to_neo():
            logger.debug("Morpheus is handing off to Neo")
            return agents["Neo"]

        def handoff_to_oracle():
            logger.debug("Morpheus is handing off to Oracle")
            return agents["Oracle"]

        def handoff_back_to_morpheus():
            logger.debug("Assistant agent is handing off back to Morpheus")
            return agents["Morpheus"]

        # Assign handoff functions to Morpheus
        agents["Morpheus"].functions = [
            handoff_to_trinity,
            handoff_to_neo,
            handoff_to_oracle,
        ]

        # Assign handoff functions to assistant agents (only handoff back to Morpheus)
        assistant_agents = [
            "Trinity",
            "Neo",
            "Oracle",
        ]

        for agent_name in assistant_agents:
            agents[agent_name].functions = [handoff_back_to_morpheus]

        # Set the starting agent to Morpheus
        self.set_starting_agent(agents["Morpheus"])

        logger.debug(f"Agents created: {list(agents.keys())}")
        return agents


if __name__ == "__main__":
    SysadminBlueprint.main()
