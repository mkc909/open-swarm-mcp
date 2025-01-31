# blueprints/sysadmin/blueprint_sysadmin.py

"""
Sysadmin Blueprint for Open Swarm.

This blueprint sets up a system administration framework with:
  - Morpheus as the central coordinator (TriageAgent).
  - Trinity handling filesystem operations.
  - Neo executing shell scripts.
  - Oracle performing search queries.
"""

import logging
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.settings import DEBUG
from swarm.types import Agent

# Configure logging for debugging and informational messages.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class SysadminBlueprint(BlueprintBase):
    """
    Blueprint for system administration tasks.

    This blueprint configures:
      - Morpheus as the central coordinator who delegates tasks.
      - Trinity for managing filesystem operations.
      - Neo for executing shell scripts.
      - Oracle for processing search queries.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Returns blueprint metadata including title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "Sysadmin Blueprint",
            "description": (
                "Deploys Morpheus as the central coordinator and assistant agents for MCP-based system administration, "
                "covering filesystem management, shell script execution, and search query processing."
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
        Creates and registers agents for the blueprint.

        Returns:
            A dictionary of agents, keyed by agent names.
        """
        import os

        # Retrieve environment variables.
        allowed_paths = os.getenv("ALLOWED_PATH", "/default/path")
        brave_api_key = os.getenv("BRAVE_API_KEY", "default-brave-key")

        # Container for agents.
        agents: Dict[str, Agent] = {}

        # Define Morpheus as the central coordinator (TriageAgent).
        # His instructions clearly state which tasks should be routed to which assistant.
        agents["Morpheus"] = Agent(
            name="Morpheus",
            instructions=(
                "You are Morpheus, the central coordinator responsible for delegating tasks. "
                "Route filesystem operations to Trinity, shell script tasks to Neo, and search queries to Oracle. "
                "Do not execute tasks yourself."
            ),
            env_vars={},
        )

        # Define Trinity for filesystem operations.
        agents["Trinity"] = Agent(
            name="Trinity",
            instructions=(
                "You are Trinity, responsible for managing filesystem operations within allowed paths. "
                "Complete file management tasks and then return control to Morpheus."
            ),
            mcp_servers=["filesystem"],
            env_vars={"ALLOWED_PATH": allowed_paths},
        )

        # Define Neo for executing shell scripts.
        agents["Neo"] = Agent(
            name="Neo",
            instructions=(
                "You are Neo, tasked with executing shell scripts securely. "
                "Process and complete script execution tasks, then return control to Morpheus."
            ),
            mcp_servers=["mcp-shell"],
        )

        # Define Oracle for processing search queries.
        agents["Oracle"] = Agent(
            name="Oracle",
            instructions=(
                "You are Oracle, responsible for executing search queries using the Brave Search MCP server. "
                "Utilize the API key to process queries and return results to Morpheus."
            ),
            mcp_servers=["brave-search"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
        )

        # Explicit handoff functions with 25-word docstrings.

        def handoff_to_trinity():
            """
            Delegates task execution from Morpheus to Trinity. This function enables Trinity to securely perform filesystem operations, then returns control to Morpheus upon task completion.
            """
            return agents["Trinity"]

        def handoff_to_neo():
            """
            Delegates task execution from Morpheus to Neo. This function enables Neo to securely execute shell scripts, then promptly returns control to Morpheus after successful completion.
            """
            return agents["Neo"]

        def handoff_to_oracle():
            """
            Delegates task execution from Morpheus to Oracle. This function enables Oracle to process search queries using Brave Search, then returns control to Morpheus upon query completion.
            """
            return agents["Oracle"]

        def handoff_back_to_morpheus():
            """
            Delegates task execution from an assistant agent back to Morpheus. This function ensures that after task completion, control reliably returns to Morpheus for further delegation.
            """
            return agents["Morpheus"]

        # Assign delegation functions to Morpheus.
        agents["Morpheus"].functions = [
            handoff_to_trinity,
            handoff_to_neo,
            handoff_to_oracle,
        ]

        # Configure each assistant agent to return control back to Morpheus.
        for agent_name in ["Trinity", "Neo", "Oracle"]:
            agents[agent_name].functions = [handoff_back_to_morpheus]

        # Set Morpheus as the starting agent.
        self.set_starting_agent(agents["Morpheus"])

        logger.debug(f"Agents registered: {list(agents.keys())}")
        return agents


if __name__ == "__main__":
    SysadminBlueprint.main()
