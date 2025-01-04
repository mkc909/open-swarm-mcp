# blueprints/echo/blueprint_echo.py

"""
EchoBlueprint Class for Open Swarm.

This blueprint defines a single agent that echoes user inputs.
It leverages the BlueprintBase to handle all configuration and MCP session management.
"""

import logging
from typing import Dict, Any, Callable

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent  # Removed AgentFunctionDefinition import

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Prevent adding multiple handlers if they already exist
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class EchoBlueprint(BlueprintBase):
    """
    A blueprint that defines a single agent which echoes user inputs.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the EchoBlueprint.

        Returns:
            Dict[str, Any]: Dictionary containing title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "Echo Integration Blueprint",
            "description": "A basic blueprint that defines an agent capable of echoing user inputs.",
            "required_mcp_servers": [],  # No MCP servers required
            "env_vars": [],              # No environment variables required
        }

    def create_agents(self) -> None:
        """
        Create agents for this blueprint by defining their instructions
        and associated functions.
        """
        logger.debug("Creating agents for EchoBlueprint.")

        # Define the echo function
        def echo_function(content: str) -> str:
            """
            Echoes the user input.

            Args:
                content (str): The user's input.

            Returns:
                str: The echoed content.
            """
            logger.info(f"Echoing content: {content}")
            return content

        # Create Echo Agent
        echo_agent = Agent(
            name="EchoAgent",
            instructions=(
                "You are the EchoAgent. Your sole purpose is to echo back any input provided by the user."
            ),
            mcp_servers=[],  # No MCP servers required
            env_vars={},     # No environment variables required
            functions=[echo_function],
            parallel_tool_calls=False  # Set based on your framework's requirements
        )

        # Assign the agent to an instance variable for later use
        self.echo_agent = echo_agent
        logger.info("EchoAgent has been created.")


if __name__ == "__main__":
    import argparse

    # Parse command-line arguments for streaming mode
    parser = argparse.ArgumentParser(description="Run EchoBlueprint REPL.")
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming mode for responses."
    )
    args = parser.parse_args()

    # Instantiate the blueprint
    blueprint = EchoBlueprint()

    # Run the blueprint's interactive REPL loop with the EchoAgent
    blueprint.interactive_mode(starting_agent=blueprint.echo_agent, stream=args.stream)
