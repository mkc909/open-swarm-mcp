# blueprints/sysadmin/blueprint_sysadmin.py

"""
Sysadmin Blueprint Class for Open Swarm (MCP).

This blueprint defines a SysAdmin agent and a team of assistant agents that perform
specific system administration tasks. The SysAdmin can delegate tasks to any assistant
agent, and assistant agents can only hand off tasks back to the SysAdmin.
"""

import logging
from typing import Dict, Any, Callable

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
    A blueprint defining a SysAdmin agent and assistant agents for various MCP server integrations.
    The SysAdmin can delegate tasks to assistant agents, and assistant agents can only return
    control back to the SysAdmin.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the SysadminBlueprint.

        Returns:
            Dict[str, Any]: Metadata with title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "Sysadmin Blueprint",
            "description": (
                "Provides a SysAdmin agent and assistant agents for MCP-based system administration: "
                "filesystem management, searching, SQLite database operations, MCP installation, "
                "in-memory tasks, and sequential-thinking workflows."
            ),
            "required_mcp_servers": [
                "filesystem",
                "brave-search",
                "sqlite",
                "mcp-installer",
                "memory",
                "sequential-thinking",
            ],
            "env_vars": [
                "ALLOWED_PATH",
                "BRAVE_API_KEY",
                "SQLITE_DB_PATH",
            ],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create agents for the SysadminBlueprint, including the SysAdmin and assistant agents.

        Returns:
            Dict[str, Agent]: Dictionary of created agents.
        """
        import os

        # Retrieve environment variables
        allowed_paths = os.getenv("ALLOWED_PATH", "/default/path")
        brave_api_key = os.getenv("BRAVE_API_KEY", "default-brave-key")
        sqlite_db_path = os.getenv("SQLITE_DB_PATH", "/tmp/sqlite.db")

        # Dictionary to hold all agents
        agents: Dict[str, Agent] = {}

        # Define the SysAdmin agent
        agents["SysAdminAgent"] = Agent(
            name="SysAdminAgent",
            instructions=(
                "You are the SysAdmin responsible for overseeing and delegating tasks to assistant agents. "
                "You can delegate tasks to any assistant agent but cannot perform the tasks directly."
            ),
            env_vars={},
        )

        # Define assistant agents
        agents["FilesystemAgent"] = Agent(
            name="FilesystemAgent",
            instructions=(
                "You manage and interact with the filesystem under allowed paths. "
                "You have been provided with the tools need to do this."
                "After executing filesystem tools on behalf of the user, you may pass back to Sysadmin."
            ),
            mcp_servers=["filesystem"],
            env_vars={"ALLOWED_PATH": allowed_paths},
        )

        agents["BraveSearchAgent"] = Agent(
            name="BraveSearchAgent",
            instructions=(
                "You perform search queries using the Brave Search MCP server. "
                "Leverage the Brave API key for authenticated search operations as instructed by the SysAdmin."
            ),
            mcp_servers=["brave-search"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
        )

        agents["SQLiteAgent"] = Agent(
            name="SQLiteAgent",
            instructions=(
                "You interact with a SQLite database via the SQLite MCP server. "
                "Use the provided database path to manage data as directed by the SysAdmin."
            ),
            mcp_servers=["sqlite"],
            env_vars={"SQLITE_DB_PATH": sqlite_db_path},
        )

        agents["McpInstallerAgent"] = Agent(
            name="McpInstallerAgent",
            instructions=(
                "You handle MCP installation and configuration tasks, "
                "coordinating the setup of various MCP servers as needed under the direction of the SysAdmin."
            ),
            mcp_servers=["mcp-installer"],
            env_vars={},
        )

        agents["MemoryAgent"] = Agent(
            name="MemoryAgent",
            instructions=(
                "You perform in-memory data operations using the memory MCP server, "
                "allowing short-term or ephemeral data storage within workflows as requested by the SysAdmin."
            ),
            mcp_servers=["memory"],
            env_vars={},
        )

        agents["SequentialThinkingAgent"] = Agent(
            name="SequentialThinkingAgent",
            instructions=(
                "You provide sequential-thinking capabilities, helping plan and structure "
                "multi-step or branching tasks in a logical order as assigned by the SysAdmin."
            ),
            mcp_servers=["sequential-thinking"],
            env_vars={},
        )

        # Define handoff functions
        # SysAdmin can handoff to any assistant agent
        def handoff_to_filesystem():
            logger.debug("SysAdmin is handing off to FilesystemAgent")
            return agents["FilesystemAgent"]

        def handoff_to_brave_search():
            logger.debug("SysAdmin is handing off to BraveSearchAgent")
            return agents["BraveSearchAgent"]

        def handoff_to_sqlite():
            logger.debug("SysAdmin is handing off to SQLiteAgent")
            return agents["SQLiteAgent"]

        def handoff_to_mcp_installer():
            logger.debug("SysAdmin is handing off to McpInstallerAgent")
            return agents["McpInstallerAgent"]

        def handoff_to_memory():
            logger.debug("SysAdmin is handing off to MemoryAgent")
            return agents["MemoryAgent"]

        def handoff_to_sequential_thinking():
            logger.debug("SysAdmin is handing off to SequentialThinkingAgent")
            return agents["SequentialThinkingAgent"]

        # Assistant agents can only handoff back to SysAdmin
        def handoff_back_to_sysadmin():
            logger.debug("Assistant agent is handing off back to SysAdminAgent")
            return agents["SysAdminAgent"]

        # Assign handoff functions to the SysAdmin agent
        agents["SysAdminAgent"].functions = [
            handoff_to_filesystem,
            handoff_to_brave_search,
            handoff_to_sqlite,
            handoff_to_mcp_installer,
            handoff_to_memory,
            handoff_to_sequential_thinking,
        ]

        # Assign handoff functions to assistant agents (only handoff back to SysAdmin)
        assistant_agents = [
            "FilesystemAgent",
            "BraveSearchAgent",
            "SQLiteAgent",
            "McpInstallerAgent",
            "MemoryAgent",
            "SequentialThinkingAgent",
        ]

        for agent_name in assistant_agents:
            agents[agent_name].functions = [handoff_back_to_sysadmin]

        # Set the starting agent to SysAdminAgent
        self.set_starting_agent(agents["SysAdminAgent"])

        logger.debug(f"Agents created: {list(agents.keys())}")
        return agents


if __name__ == "__main__":
    SysadminBlueprint.main()
