"""
FlowiseBlueprint Class for Open Swarm MCP.

This blueprint defines agents related to Flowise MCP server interactions.
It leverages the BlueprintBase to handle all configuration and MCP session management.
"""

import logging
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.settings import DEBUG
from swarm.types import Agent

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Prevent adding multiple handlers if they already exist
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class FlowiseBlueprint(BlueprintBase):
    """
    A blueprint that defines two agents:
      - FlowiseAgent: Interacts with the Flowise API via the 'flowise-mcp' MCP server.
      - TriageAgent: Performs triage tasks without accessing any MCP server.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the FlowiseBlueprint.

        Returns:
            Dict[str, Any]: Dictionary containing title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "Flowise Integration Blueprint",
            "description": "Enables interaction with Flowise via MCP server tools and includes a triage agent.",
            "required_mcp_servers": ["flowise-mcp"],
            "env_vars": ["FLOWISE_API_KEY", "FLOWISE_API_ENDPOINT"],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create agents for the FlowiseBlueprint.

        Returns:
            Dict[str, Agent]: Dictionary containing all created agents.
        """
        import os

        # Retrieve environment variables
        flowise_api_key = os.getenv("FLOWISE_API_KEY")
        flowise_api_endpoint = os.getenv("FLOWISE_API_ENDPOINT", "http://localhost:3000")

        if not flowise_api_key:
            raise EnvironmentError("Environment variable 'FLOWISE_API_KEY' is not set.")

        # Define agents dictionary
        agents = {}

        # Define transfer function with explicit reference to `agents`
        def transfer_to_flowise() -> Agent:
            """
            Transfer control from TriageAgent to FlowiseAgent.
            """
            logger.debug("Transferring control from TriageAgent to FlowiseAgent.")
            return agents["FlowiseAgent"]

        # Create Flowise Agent
        flowise_agent = Agent(
            name="FlowiseAgent",
            instructions=(
                "You are the FlowiseAgent. Interact with the Flowise API via the 'flowise-mcp' MCP server. "
                "Use available functions like 'list_chatflows' or 'create_prediction' to perform operations."
            ),
            mcp_servers=["flowise-mcp"],
            env_vars={
                "FLOWISE_API_KEY": flowise_api_key,
                "FLOWISE_API_ENDPOINT": flowise_api_endpoint,
            },
            functions=[],  # Functions are provided by the MCP server
            parallel_tool_calls=False,  # Set based on your framework's requirements
        )

        # Create Triage Agent
        triage_agent = Agent(
            name="TriageAgent",
            instructions=(
                "You are the TriageAgent, responsible for categorizing and managing tasks. "
                "You do not have access to any external MCP servers."
            ),
            mcp_servers=[],
            env_vars={},
            functions=[transfer_to_flowise],  # Pass the closure function
            parallel_tool_calls=False,
        )

        # Populate agents dictionary
        agents["FlowiseAgent"] = flowise_agent
        agents["TriageAgent"] = triage_agent

        logger.debug("FlowiseAgent and TriageAgent have been created.")
        self.set_starting_agent(triage_agent)  # Set TriageAgent as the starting agent
        return agents


if __name__ == "__main__":
    FlowiseBlueprint.main()

