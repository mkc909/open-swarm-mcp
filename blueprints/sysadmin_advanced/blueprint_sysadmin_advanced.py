# blueprints/sysadmin/blueprint_sysadmin_advanced.py

"""
Advanced Sysadmin Blueprint for Open Swarm (MCP).

This blueprint defines Zeus as the central TriageAgent and assistant agents
(Hephaestus, Hermes, Odin, Thoth, Hecate, Mnemosyne, Chronos) handling system
administration tasks including filesystem management, shell execution, search,
database operations, deployment, memory management, and sequential planning.
"""

import logging
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.settings import DEBUG
from swarm.types import Agent

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class SysadminAdvancedBlueprint(BlueprintBase):
    """
    A blueprint defining Zeus as the TriageAgent and a pantheon of assistant agents
    (Hephaestus, Hermes, Odin, Thoth, Hecate, Mnemosyne, Chronos) for advanced system
    administration and automation.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "Advanced Sysadmin Blueprint",
            "description": (
                "Provides Zeus as the TriageAgent and a pantheon of assistant agents for MCP-based system "
                "administration, including filesystem management, shell execution, search, database operations, "
                "deployment, memory management, and sequential planning."
            ),
            "required_mcp_servers": [
                "filesystem",
                "brave-search",
                "sqlite",
                "mcp-installer",
                "memory",
                "mcp-shell",
                "sequential-thinking",
            ],
            "env_vars": [
                "ALLOWED_PATH",
                "BRAVE_API_KEY",
                "SQLITE_DB_PATH",
            ],
        }

    def create_agents(self) -> Dict[str, Agent]:
        import os

        # Retrieve environment variables
        allowed_paths = os.getenv("ALLOWED_PATH", "/default/path")
        brave_api_key = os.getenv("BRAVE_API_KEY", "default-brave-key")
        sqlite_db_path = os.getenv("SQLITE_DB_PATH", "/tmp/sqlite.db")

        agents: Dict[str, Agent] = {}

        # Define Zeus as the central TriageAgent
        agents["Zeus"] = Agent(
            name="Zeus",
            instructions=(
                "You are Zeus, the supreme coordinator overseeing and delegating tasks to assistant agents. "
                "You do not execute tasks directly but ensure smooth delegation and system order."
            ),
            env_vars={},
        )

        # Define assistant agents with mythological names
        agents["Hephaestus"] = Agent(
            name="Hephaestus",
            instructions=(
                "You are Hephaestus, responsible for managing filesystem operations, including file creation, modification, and deletion."
            ),
            mcp_servers=["filesystem"],
            env_vars={"ALLOWED_PATH": allowed_paths},
        )

        agents["Hermes"] = Agent(
            name="Hermes",
            instructions=(
                "You are Hermes, responsible for executing shell commands and scripts securely with prompt performance."
            ),
            mcp_servers=["mcp-shell"],
        )

        agents["Odin"] = Agent(
            name="Odin",
            instructions=(
                "You are Odin, tasked with performing search queries using the Brave Search MCP server, returning accurate results."
            ),
            mcp_servers=["brave-search"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
        )

        agents["Thoth"] = Agent(
            name="Thoth",
            instructions=(
                "You are Thoth, responsible for managing structured data and database operations using SQLite."
            ),
            mcp_servers=["sqlite"],
            env_vars={"SQLITE_DB_PATH": sqlite_db_path},
        )

        agents["Hecate"] = Agent(
            name="Hecate",
            instructions=(
                "You are Hecate, handling system deployment and configuration tasks, ensuring that installations occur reliably."
            ),
            mcp_servers=["mcp-installer"],
        )

        agents["Mnemosyne"] = Agent(
            name="Mnemosyne",
            instructions=(
                "You are Mnemosyne, managing memory operations for both temporary and persistent data storage."
            ),
            mcp_servers=["memory"],
        )

        agents["Chronos"] = Agent(
            name="Chronos",
            instructions=(
                "You are Chronos, responsible for sequential planning and organizing multi-step processes in a time-efficient manner."
            ),
            mcp_servers=["sequential-thinking"],
        )

        # Define explicit handoff functions with 25-word docstrings.
        def handoff_to_hephaestus():
            """This function delegates task execution to Hephaestus, the agent responsible for filesystem operations, ensuring that file management commands are handled securely and efficiently without error."""
            return agents["Hephaestus"]

        def handoff_to_hermes():
            """This function delegates task execution to Hermes, the agent responsible for processing shell commands, ensuring that script execution occurs securely and promptly without interruption indeed."""
            return agents["Hermes"]

        def handoff_to_odin():
            """This function delegates task execution to Odin, the agent responsible for performing search queries, ensuring that search requests are processed efficiently and results returned promptly."""
            return agents["Odin"]

        def handoff_to_thoth():
            """This function delegates task execution to Thoth, the agent responsible for managing database operations using SQLite, ensuring that data is organized, stored, and retrieval flawless."""
            return agents["Thoth"]

        def handoff_to_hecate():
            """This function delegates task execution to Hecate, the agent responsible for system deployment and configuration, ensuring that installations and setups are performed efficiently without complications."""
            return agents["Hecate"]

        def handoff_to_mnemosyne():
            """This function delegates task execution to Mnemosyne, the agent responsible for memory management, ensuring that temporary and persistent data is stored and retrieved with context."""
            return agents["Mnemosyne"]

        def handoff_to_chronos():
            """This function delegates task execution to Chronos, the agent responsible for sequential planning, ensuring that multi-step processes are organized, scheduled, and executed in time-efficient manner."""
            return agents["Chronos"]

        def handoff_back_to_zeus():
            """This function delegates task execution back to Zeus, the supreme coordinator, ensuring that tasks are returned to the central agent for further delegation and oversight."""
            return agents["Zeus"]

        # Assign handoff functions to Zeus (central coordinator)
        zeus_handoffs = [
            handoff_to_hephaestus,
            handoff_to_hermes,
            handoff_to_odin,
            handoff_to_thoth,
            handoff_to_hecate,
            handoff_to_mnemosyne,
            handoff_to_chronos,
        ]
        agents["Zeus"].functions = zeus_handoffs

        # Each assistant agent only hands off back to Zeus.
        assistant_names = ["Hephaestus", "Hermes", "Odin", "Thoth", "Hecate", "Mnemosyne", "Chronos"]
        for name in assistant_names:
            agents[name].functions = [handoff_back_to_zeus]

        # Set the starting agent to Zeus.
        self.set_starting_agent(agents["Zeus"])
        logger.debug(f"Agents created: {list(agents.keys())}")
        return agents


if __name__ == "__main__":
    SysadminAdvancedBlueprint.main()
