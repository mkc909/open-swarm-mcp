# src/swarm/extensions/blueprint/modes/cli_mode/main.py

import asyncio
from swarm import Agent, Swarm
from swarm.extensions.blueprint.modes.cli_mode.utils import (
    display_message,
    prompt_user,
    log_and_exit
)
from swarm.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

async def run_cli_mode(agent: Agent, colorama_available: bool = False) -> None:
    """
    Execute CLI mode for Open Swarm MCP.

    CLI mode enables users to interact with a Swarm agent via a command-line interface.
    Users can input queries, and the agent will respond with generated outputs.

    Args:
        agent (Agent): An instance of the Swarm agent to handle user queries.
        colorama_available (bool): Flag indicating whether colorized output is supported.
    """
    # Guard clause: Ensure the agent is provided
    if not agent:
        log_and_exit("No agent provided for CLI mode. Exiting.", code=1)

    # Inform the user about CLI mode startup
    display_message("Starting CLI mode. Enter your queries (type 'exit' or 'quit' to quit).", "info")
    logger.debug(f"CLI mode initialized with agent: {agent}")

    try:
        while True:
            # Prompt the user for input
            query = prompt_user("Enter your query").strip()
            logger.debug(f"User input received: {query}")

            # Exit conditions
            if query.lower() in ["exit", "quit"]:
                display_message("Exiting CLI mode.", "info")
                logger.info("User exited CLI mode.")
                break

            # Skip empty inputs
            if not query:
                logger.debug("Empty input received. Skipping.")
                continue

            # Process the query through the agent
            try:
                response = Swarm().run(
                    agent=agent,
                    messages=[{"role": "user", "content": query}],
                    stream=False,
                )
                result = next(
                    (message.get("content") for message in response.messages if message["role"] == "assistant"),
                    "No response."
                )
                logger.debug(f"Agent response: {result}")
                print(f"Response: {result}")

            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                display_message(f"Error processing your query: {e}", "error")
                continue

    except KeyboardInterrupt:
        # Handle user interruption gracefully
        display_message("\nCLI mode interrupted by user (Ctrl+C). Exiting.", "warning")
        logger.info("CLI mode interrupted by user (Ctrl+C).")
    except Exception as e:
        # Log and report unexpected errors
        logger.error(f"Unexpected error in CLI mode: {e}")
        display_message(f"Unexpected error in CLI mode: {e}", "error")
    finally:
        # Cleanup and shutdown
        logger.info("CLI mode terminated.")
        display_message("CLI mode terminated.", "info")
