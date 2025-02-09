import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from swarm.core import Swarm
from swarm.extensions.config.config_loader import load_server_config
from swarm.settings import DEBUG
from swarm.types import Agent
from swarm.utils.redact import redact_sensitive_data
from dotenv import load_dotenv
import argparse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)


class OmniplexBlueprint(ABC):
    """
    Omniplex is an AI-powered orchestrator that dynamically discovers and utilizes all available MCP servers.
    
    - **Amazo**: Loads all `npx`-based MCP servers.
    - **Rogue**: Loads all `uvx`-based MCP servers.
    - **Sylar**: Loads any remaining MCP servers.
    
    Agents remain **aware** of each other’s capabilities using LLM-generated summaries.
    """

    def __init__(self, config: dict, **kwargs):
        """
        Initializes the blueprint and registers dynamically discovered agents.

        Args:
            config (dict): Configuration dictionary.
            **kwargs: Additional parameters (e.g., existing swarm instance).
        """
        logger.debug(f"Initializing Omniplex with config: {redact_sensitive_data(config)}")

        if not hasattr(self, 'metadata') or not isinstance(self.metadata, dict):
            raise AssertionError("Blueprint metadata must be defined and must be a dictionary.")

        # Load environment variables
        load_dotenv()
        logger.debug("Environment variables loaded.")

        # Store configuration
        self.config = config

        # Use existing Swarm instance if provided, otherwise create a new one
        self.swarm = kwargs.get('swarm_instance', Swarm(config=self.config))
        logger.debug("Swarm instance initialized.")

        # Register agents
        self.starting_agent = None
        self.context_variables: Dict[str, Any] = {}
        agents = self.create_agents()
        self.swarm.agents.update(agents)
        logger.debug(f"Agents registered: {list(agents.keys())}")

        # Validate required environment variables
        missing_vars = [var for var in self.metadata.get('env_vars', []) if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Discover tools asynchronously for agents
        asyncio.run(self.async_discover_agent_tools())

        # Generate agent awareness summaries
        self.update_agent_awareness()

        logger.debug("Omniplex initialization complete.")

    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadata for the Omniplex blueprint."""
        return {
            "title": "Omniplex – The Ultimate AI Tool Orchestrator",
            "description": "Dynamically loads all available MCP servers, categorizes them by execution type, and enables cross-agent awareness for optimal task delegation.",
            "required_mcp_servers": [],
            "env_vars": [],
        }

    def create_agents(self) -> Dict[str, Any]:
        """
        Dynamically creates and registers agents based on MCP server execution types.
        
        - Amazo → Handles NPX-based MCP servers.
        - Rogue → Handles UVX-based MCP servers.
        - Sylar → Handles all remaining MCP servers.
        
        Returns:
            Dict[str, Any]: A dictionary mapping agent names to Agent objects.
        """
        agents = {}
        mcp_servers = self.config.get("mcpServers", {})

        npx_servers = [name for name, cfg in mcp_servers.items() if cfg.get("command") == "npx"]
        uvx_servers = [name for name, cfg in mcp_servers.items() if cfg.get("command") == "uvx"]
        other_servers = [name for name in mcp_servers if name not in npx_servers + uvx_servers]

        agents["Amazo"] = self.create_agent("Amazo", "npx", npx_servers)
        agents["Rogue"] = self.create_agent("Rogue", "uvx", uvx_servers)
        agents["Sylar"] = self.create_agent("Sylar", "other", other_servers)

        self.set_starting_agent(agents["Amazo"])
        return agents

    def create_agent(self, name: str, category: str, mcp_servers: List[str]) -> Any:
        """
        Creates an agent with dynamically assigned MCP servers.

        Args:
            name (str): Agent name.
            category (str): Category of servers (npx, uvx, or other).
            mcp_servers (List[str]): List of MCP servers assigned to this agent.

        Returns:
            Agent: The dynamically generated agent.
        """
        return Agent(
            name=name,
            instructions=self.generate_base_instructions(name, category),
            mcp_servers=mcp_servers,
            env_vars={},
        )

    def generate_base_instructions(self, agent_name: str, category: str) -> str:
        """
        Generates base instructions for an agent, before adding cross-agent awareness.

        Args:
            agent_name (str): The name of the agent.
            category (str): The category of tools it manages.

        Returns:
            str: The base instruction set for the agent.
        """
        return (
            f"You are {agent_name}, an advanced AI tool orchestrator handling MCP servers categorized under '{category}'.\n"
            "Your role is to execute tasks using your assigned MCP tools and return responses to the user.\n"
            "You do not delegate tasks outside of your assigned toolset but may inform the user if another agent is better suited.\n"
        )

    async def async_discover_agent_tools(self) -> None:
        """Asynchronously discovers and registers tools for all agents."""
        for agent in self.swarm.agents.values():
            await self.swarm.discover_and_merge_agent_tools(agent)

    def update_agent_awareness(self) -> None:
        """
        Uses an LLM request to generate agent descriptions, making agents aware of each other's capabilities.
        """
        descriptions = {}
        for agent in self.swarm.agents.values():
            descriptions[agent.name] = self.generate_tool_summary(agent)

        for agent in self.swarm.agents.values():
            agent.instructions += "\n\nAdditional agent capabilities:\n"
            for other_agent, desc in descriptions.items():
                if other_agent != agent.name:
                    agent.instructions += f"- {other_agent}: {desc}\n"

    def generate_tool_summary(self, agent) -> str:
        """
        Uses an LLM query to summarize an agent’s toolset.

        Args:
            agent: The agent to summarize.

        Returns:
            str: A concise description of the agent's capabilities.
        """
        tools = [tool.name for tool in agent.functions if hasattr(tool, "name")]
        if not tools:
            return "No specialized tools available."

        response = self.swarm.get_chat_completion(
            agent=agent,
            history=[{"role": "user", "content": f"Summarize the following tools: {', '.join(tools)}"}],
            context_variables={},
            model_override=None,
            stream=False,
            debug=False,
        )

        return response.choices[0].message.content.strip()

    def set_starting_agent(self, agent: Any) -> None:
        """Sets the starting agent."""
        self.starting_agent = agent
        self.context_variables["active_agent_name"] = agent.name

    @classmethod
    def main(cls):
        """Main entry point for running Omniplex in CLI mode."""
        parser = argparse.ArgumentParser(description="Launch the Omniplex blueprint.")
        parser.add_argument("--config", type=str, default="./swarm_config.json", help="Path to the configuration file")
        args = parser.parse_args()

        config = load_server_config(args.config)
        blueprint = cls(config=config)
        blueprint.interactive_mode()


if __name__ == "__main__":
    OmniplexBlueprint.main()
