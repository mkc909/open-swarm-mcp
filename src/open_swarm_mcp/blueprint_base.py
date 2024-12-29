# src/open_swarm_mcp/blueprint_base.py

import os
import json
import logging
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from swarm.repl import run_demo_loop
from swarm import Agent

logger = logging.getLogger(__name__)

class BlueprintBase(ABC):
    """
    Abstract Base Class for all Blueprints.
    """

    def __init__(self) -> None:
        """
        Initialize the blueprint and load configuration.
        """
        self.config = self.load_config()
        self.validate_metadata()
        logger.debug("BlueprintBase initialized with configuration.")

    def load_config(self) -> Dict[str, Any]:
        """
        Load the MCP server configuration from mcp_server_config.json.

        Returns:
            Dict[str, Any]: Parsed configuration dictionary.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            json.JSONDecodeError: If the configuration file contains invalid JSON.
        """
        config_file = 'mcp_server_config.json'
        logger.debug(f"Loading configuration from {config_file}.")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {config_file}.")
                    return config
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in {config_file}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error loading {config_file}: {e}")
                raise
        else:
            logger.error(f"Configuration file {config_file} not found.")
            raise FileNotFoundError(f"Configuration file {config_file} not found.")

    def get_llm_config(self) -> Dict[str, Any]:
        """
        Retrieve the LLM configuration from the loaded config.

        Returns:
            Dict[str, Any]: LLM configuration dictionary.
        """
        llm_config = self.config.get("llm", {})
        logger.debug(f"Retrieved LLM configuration: {llm_config}")
        return llm_config

    def get_model(self) -> str:
        """
        Get the model name from the LLM configuration.

        Returns:
            str: The model name.
        """
        model = self.get_llm_config().get("model", "gpt-4")
        logger.debug(f"Using model: {model}")
        return model

    def get_base_url(self) -> str:
        """
        Get the base URL from the LLM configuration.

        Returns:
            str: The base URL.
        """
        base_url = self.get_llm_config().get("base_url", "https://api.openai.com/v1")
        logger.debug(f"Using base_url: {base_url}")
        return base_url

    def get_env_var(self, var_name: str) -> str:
        """
        Retrieve the value of a specified environment variable.

        Args:
            var_name (str): The name of the environment variable.

        Returns:
            str: The value of the environment variable.

        Raises:
            ValueError: If the environment variable is not set.
        """
        value = os.getenv(var_name)
        if not value:
            logger.error(f"Environment variable {var_name} is not set.")
            raise ValueError(f"Environment variable {var_name} is not set.")
        logger.debug(f"Loaded {var_name} from environment variable.")
        return value

    @abstractmethod
    def validate_env_vars(self) -> None:
        """
        Validate that required environment variables are set and any necessary conditions are met.
        """
        pass

    @abstractmethod
    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        pass

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata about the blueprint.

        Returns:
            Dict[str, Any]: Metadata dictionary containing title, description, etc.
        """
        pass

    @abstractmethod
    def get_agents(self) -> Dict[str, Agent]:
        """
        Return the dictionary of agents used by this blueprint.
        """
        pass

    def get_starting_agent(self) -> Agent:
        """
        By default, pick a random agent from self.get_agents().
        Child classes can override if they want a specific logic.

        Returns:
            Agent: The starting agent.
        """
        agent_map = self.get_agents()
        if not agent_map:
            raise ValueError("No agents defined in this blueprint.")
        starting_agent = random.choice(list(agent_map.values()))
        logger.debug(f"Selected starting agent: {starting_agent.name}")
        return starting_agent

    def interactive_mode(self) -> None:
        """
        Default interactive mode that uses swarm.repl.run_demo_loop
        with the 'starting_agent' determined by get_starting_agent().
        """
        logger.info("Starting blueprint in interactive mode.")
        starting_agent = self.get_starting_agent()
        logger.info(f"Starting agent: {starting_agent.name}")
        run_demo_loop(starting_agent=starting_agent)

    def validate_metadata(self) -> None:
        """
        Validate that the metadata property meets the required structure.

        Raises:
            ValueError: If metadata is invalid or missing required fields.
        """
        required_fields = ["title", "description"]
        for field in required_fields:
            if field not in self.metadata:
                raise ValueError(f"Missing required metadata field: {field}")
        logger.debug("Metadata validation passed.")

    def summarize_agents(self) -> Dict[str, str]:
        """
        Provide a summary of all agents defined in the blueprint.

        Returns:
            Dict[str, str]: A dictionary mapping agent names to their instructions.
        """
        summary = {name: agent.instructions for name, agent in self.get_agents().items()}
        logger.debug(f"Agent summaries: {summary}")
        return summary
