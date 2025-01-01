# Updated default blueprint for standard alignment.

from open_swarm_mcp.blueprint_base import BlueprintBase
from typing import Dict, Any, Optional
from swarm import Agent, Swarm
from swarm.repl import run_demo_loop
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class DefaultBlueprint(BlueprintBase):
    """
    Default Simple Agent Blueprint Implementation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DefaultBlueprint.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary.
        """
        super().__init__(config=config)
        self._metadata = {
            "title": "Default Simple Agent",
            "description": "A simple agent that echoes user inputs.",
            "required_mcp_servers": [],
            "env_vars": []
        }
        self.client = Swarm()
        logger.info("Initialized Swarm 🐝")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def validate_env_vars(self) -> None:
        """
        Validate that required environment variables are set.
        """
        # No environment variables needed for DefaultBlueprint.
        pass

    def create_agent(self) -> Agent:
        """
        Create and configure the default agent.

        Returns:
            Agent: A configured Agent instance.
        """
        agent = Agent(
            name="DefaultAgent",
            instructions="""You are a simple agent that echoes user inputs.
Please repeat back what the user says.""",
            functions=[self.echo_function],
            parallel_tool_calls=True
        )
        logger.info("Created DefaultAgent with echo function.")
        return agent

    def get_agents(self) -> Dict[str, Agent]:
        """
        Retrieve the dictionary of agents.

        Returns:
            Dict[str, Agent]: A dictionary containing all created agents.
        """
        return {"DefaultAgent": self.create_agent()}

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        self.validate_env_vars()

        agent = self.create_agent()
        default_message = {"role": "user", "content": "Hello, how are you?"}
        messages = config.get('messages', [default_message]) if config else [default_message]

        response = self.client.run(agent=agent, messages=messages)
        return {
            "status": "success",
            "messages": response.messages,
            "metadata": self.metadata
        }

    def interactive_mode(self) -> None:
        """
        Use Swarm's REPL loop, starting with the default agent.
        """
        logger.info("Launching interactive mode with DefaultAgent.")
        run_demo_loop(starting_agent=self.create_agent())

    def echo_function(self, content: str) -> str:
        """
        Echoes the user input.

        Args:
            content (str): The user's input.

        Returns:
            str: The echoed content.
        """
        logger.info(f"Echoing content: {content}")
        return content

# Entry point for standalone execution
if __name__ == "__main__":
    blueprint = DefaultBlueprint()
    try:
        blueprint.interactive_mode()
    except Exception as e:
        print(f"Error running Default Blueprint: {e}")
