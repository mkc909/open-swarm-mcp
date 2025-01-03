# src/swarm/modes/cli_mode.py

from typing import Any, Dict
from swarm import Agent, Swarm
from swarm.utils.logger import setup_logger
from swarm.utils.color_utils import color_text

logger = setup_logger(__name__)

async def run_cli_mode(agent: Agent, colorama_available: bool = False):
    """
    CLI mode for Open Swarm MCP.
    
    Args:
        agent (Agent): Swarm agent to handle queries.
        colorama_available (bool): Flag indicating if colorama is available for colored outputs.
    """
    if colorama_available:
        print(color_text("Starting CLI mode. Enter your queries (type 'exit' or 'quit' to quit).", "cyan"))
    else:
        print("Starting CLI mode. Enter your queries (type 'exit' or 'quit' to quit).")
    try:
        while True:
            query = input("Enter your query: ").strip()
            if query.lower() in ["exit", "quit"]:
                if colorama_available:
                    print(color_text("Exiting CLI mode.", "green"))
                else:
                    print("Exiting CLI mode.")
                logger.info("Exiting CLI mode.")
                break
            if not query:
                continue  # Skip empty inputs
            response = Swarm().run(  # Removed 'await' since Swarm().run() is synchronous
                agent=agent,
                messages=[{"role": "user", "content": query}],
                stream=False,
            )
            result = next(
                (message.get("content") for message in response.messages if message["role"] == "assistant"),
                "No response."
            )
            print(f"Response: {result}")
    except Exception as e:
        logger.error("Error in CLI mode: %s", str(e))
        if colorama_available:
            print(color_text(f"Error in CLI mode: {e}", "red"))
        else:
            print(f"Error in CLI mode: {e}")
