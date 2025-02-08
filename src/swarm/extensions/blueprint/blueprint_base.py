import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from swarm.core import Swarm
from swarm.extensions.config.config_loader import load_server_config
from swarm.repl import run_demo_loop
from swarm.settings import DEBUG
from swarm.utils.redact import redact_sensitive_data
from dotenv import load_dotenv
import argparse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

class BlueprintBase(ABC):
    """
    Abstract base class for Swarm blueprints.
    Manages agents, tools, and active context for executing tasks.

    NEW FEATURE: Auto-completion of tasks.
    If auto_complete_task is enabled, after each assistant response the blueprint
    will query an LLM (using a single-token prompt) to check if the overall task is complete.
    It uses the user's original request and a brief conversation summary for context.
    """

    def __init__(self, config: dict, auto_complete_task: bool = False, **kwargs):
        """
        Initialize the blueprint and register agents.

        Args:
            config (dict): Configuration dictionary.
            auto_complete_task (bool): If True, the system will continue running steps
                until a done-check indicates the task is complete.
            **kwargs: Additional parameters (e.g., shared swarm_instance).
        """
        self.auto_complete_task = auto_complete_task

        logger.debug(f"Initializing BlueprintBase with config: {redact_sensitive_data(config)}")

        if not hasattr(self, 'metadata') or not isinstance(self.metadata, dict):
            raise AssertionError("Blueprint metadata must be defined and must be a dictionary.")

        # Load environment variables
        load_dotenv()
        logger.debug("Environment variables loaded from .env.")

        self.config = config

        self.swarm = kwargs.get('swarm_instance')
        if self.swarm is not None:
            logger.debug("Using shared swarm instance from kwargs.")
        else:
            logger.debug("No shared swarm instance provided; creating a new one.")
            self.swarm = Swarm(config=self.config)

        logger.debug("Swarm instance created.")

        # Initialize context variables for tracking active agent and conversation
        self.context_variables: Dict[str, Any] = {}
        # Save the original user goal once, for completion-check context
        self.context_variables["user_goal"] = ""

        self.starting_agent = None
        agents = self.create_agents()
        self.swarm.agents.update(agents)
        logger.debug(f"Agents registered: {list(agents.keys())}")

        required_env_vars = set(self.metadata.get('env_vars', []))
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.debug("Required environment variables validation successful.")

        asyncio.run(self.async_discover_agent_tools())
        logger.debug("Tool discovery completed.")

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Blueprint metadata including title, description, dependencies, and required env_vars.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def create_agents(self) -> Dict[str, Any]:
        """
        Create and return the agents for this blueprint.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    async def async_discover_agent_tools(self) -> None:
        """
        Discover and register tools for each agent asynchronously.
        """
        logger.debug("Discovering tools for agents...")
        for agent_name, agent in self.swarm.agents.items():
            logger.debug(f"Discovering tools for agent: {agent_name}")
            try:
                tools = await self.swarm.discover_and_merge_agent_tools(agent)
                logger.debug(f"Discovered tools for agent '{agent_name}': {tools}")
            except Exception as e:
                logger.error(f"Failed to discover tools for agent '{agent_name}': {e}")

    def set_starting_agent(self, agent: Any) -> None:
        """
        Set the starting agent for the blueprint.

        Args:
            agent (Any): The agent to set as starting agent.
        """
        logger.debug(f"Setting starting agent to: {agent.name}")
        self.starting_agent = agent
        self.context_variables["active_agent_name"] = agent.name

    def determine_active_agent(self) -> Any:
        """
        Determine and return the active agent based on context_variables.
        """
        active_agent_name = self.context_variables.get("active_agent_name")
        if active_agent_name and active_agent_name in self.swarm.agents:
            logger.debug(f"Active agent determined: {active_agent_name}")
            return self.swarm.agents[active_agent_name]
        logger.debug("Falling back to the starting agent as active agent.")
        return self.starting_agent

    def run_with_context(self, messages: List[Dict[str, str]], context_variables: dict) -> dict:
        """
        Execute a task with the given messages and context variables.

        Args:
            messages (list): Conversation history.
            context_variables (dict): Variables to maintain conversation context.

        Returns:
            dict: The response from Swarm and updated context variables.
        """
        self.context_variables.update(context_variables)
        logger.debug(f"Context variables before execution: {self.context_variables}")

        if "active_agent_name" not in self.context_variables:
            if self.starting_agent:
                self.context_variables["active_agent_name"] = self.starting_agent.name
                logger.debug(f"active_agent_name not found, using starting agent: {self.starting_agent.name}")
            else:
                logger.error("No starting agent set and active_agent_name is missing.")
                raise ValueError("No active agent or starting agent available.")

        active_agent = self.determine_active_agent()
        logger.debug(f"Running with active agent: {active_agent.name}")

        response = self.swarm.run(
            agent=active_agent,
            messages=messages,
            context_variables=self.context_variables,
            stream=False,
            debug=True,
        )

        logger.debug(f"Swarm response: {response}")
        if response.agent:
            self.context_variables["active_agent_name"] = response.agent.name
            logger.debug(f"Active agent updated to: {response.agent.name}")

        return {"response": response, "context_variables": self.context_variables}

    def set_active_agent(self, agent_name: str) -> None:
        """
        Explicitly set the active agent.

        Args:
            agent_name (str): Name of the agent to set as active.
        """
        if agent_name in self.swarm.agents:
            self.context_variables["active_agent_name"] = agent_name
            logger.debug(f"Active agent set to: {agent_name}")
        else:
            logger.error(f"Agent '{agent_name}' not found. Cannot set as active agent.")

    def _is_task_done(self, user_goal: str, conversation_summary: str, last_assistant_message: str) -> bool:
        """
        Check if the task is complete by making a minimal LLM call.
        The LLM is prompted with the user goal, a summary of the conversation, and the last assistant message,
        and must respond with a single token: YES or NO.

        Args:
            user_goal (str): The user's original request.
            conversation_summary (str): A brief summary of the conversation progress.
            last_assistant_message (str): The most recent assistant response.

        Returns:
            bool: True if the task is complete, False otherwise.
        """
        check_prompt = [
            {
                "role": "system",
                "content": "You are a completion checker. Respond with ONLY 'YES' or 'NO' (no extra words)."
            },
            {
                "role": "user",
                "content": (
                    f"User's goal: {user_goal}\n"
                    f"Conversation summary: {conversation_summary}\n"
                    f"Last assistant message: {last_assistant_message}\n"
                    "Is the task fully complete? Answer only YES or NO."
                )
            }
        ]
        done_check = self.swarm.run_llm(
            messages=check_prompt,
            max_tokens=1,
            temperature=0
        )
        raw_content = done_check.choices[0].message["content"].strip().upper()
        logger.debug(f"Done check response: {raw_content}")
        return raw_content.startswith("YES")

    def interactive_mode(self, stream: bool = False) -> None:
        """
        Start the interactive REPL loop using the blueprint's Swarm instance.
        If auto_complete_task is enabled, repeatedly calls run_with_context() until
        a completion check indicates the task is done.

        Args:
            stream (bool): Enable streaming mode.
        """
        logger.debug("Starting interactive mode.")
        if not self.starting_agent:
            logger.error("Starting agent is not set. Ensure set_starting_agent is called.")
            raise ValueError("Starting agent is not set.")
        if not self.swarm:
            logger.error("Swarm instance is not initialized.")
            raise ValueError("Swarm instance is not initialized.")

        print("Blueprint Interactive Mode 🐝")
        messages: List[Dict[str, str]] = []
        agent = self.starting_agent

        # Save the first user input as the user goal if not already set.
        first_user_input = True

        while True:
            print("\033[90mUser\033[0m: ", end="")
            user_input = input().strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting interactive mode.")
                break

            # On the first iteration, set the user goal.
            if first_user_input:
                self.context_variables["user_goal"] = user_input
                first_user_input = False

            messages.append({"role": "user", "content": user_input})
            result = self.run_with_context(messages, self.context_variables or {})
            swarm_response = result["response"]

            if stream:
                self._process_and_print_streaming_response(swarm_response)
            else:
                self._pretty_print_response(swarm_response.messages)

            messages.extend(swarm_response.messages)
            agent = swarm_response.agent

            # If auto-complete is enabled, keep calling until the task is complete.
            if self.auto_complete_task:
                # Build a simple conversation summary: join the last few messages.
                conversation_summary = " ".join(
                    [msg["content"] for msg in messages[-4:] if msg.get("content")]
                )
                # Get the last assistant message.
                last_assistant = ""
                for msg in reversed(swarm_response.messages):
                    if msg["role"] == "assistant" and msg.get("content"):
                        last_assistant = msg["content"]
                        break

                # Check if the task is complete.
                while not self._is_task_done(
                    self.context_variables.get("user_goal", ""),
                    conversation_summary,
                    last_assistant
                ):
                    # If not complete, continue running with the same context.
                    result2 = self.run_with_context(messages, self.context_variables or {})
                    swarm_response = result2["response"]
                    if stream:
                        self._process_and_print_streaming_response(swarm_response)
                    else:
                        self._pretty_print_response(swarm_response.messages)
                    messages.extend(swarm_response.messages)
                    agent = swarm_response.agent

                    # Update conversation summary and last assistant message.
                    conversation_summary = " ".join(
                        [msg["content"] for msg in messages[-4:] if msg.get("content")]
                    )
                    for msg in reversed(swarm_response.messages):
                        if msg["role"] == "assistant" and msg.get("content"):
                            last_assistant = msg["content"]
                            break

                print("\033[93m[System]\033[0m: Task is complete.")

    def _process_and_print_streaming_response(self, response):
        """
        Process and display the streaming response from Swarm.
        """
        content = ""
        last_sender = ""
        for chunk in response:
            if "sender" in chunk:
                last_sender = chunk["sender"]
            if "content" in chunk and chunk["content"] is not None:
                if not content and last_sender:
                    print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                    last_sender = ""
                print(chunk["content"], end="", flush=True)
                content += chunk["content"]
            if "tool_calls" in chunk and chunk["tool_calls"] is not None:
                for tool_call in chunk["tool_calls"]:
                    tool_function = tool_call["function"]
                    name = getattr(tool_function, "name", None)
                    if not name:
                        name = tool_function.get("__name__", "Unnamed Tool")
                    print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")
            if "delim" in chunk and chunk["delim"] == "end" and content:
                print()
                content = ""
            if "response" in chunk:
                return chunk["response"]

    def _pretty_print_response(self, messages) -> None:
        """
        Pretty print the messages returned by the Swarm.
        """
        for message in messages:
            if message["role"] != "assistant":
                continue
            print(f"\033[94m{message['sender']}\033[0m:", end=" ")
            if message["content"]:
                print(message["content"])
            tool_calls = message.get("tool_calls") or []
            if len(tool_calls) > 1:
                print()
            for tool_call in tool_calls:
                f = tool_call["function"]
                name, args = f["name"], f["arguments"]
                arg_str = json.dumps(json.loads(args)).replace(":", "=")
                print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")

    @classmethod
    def main(cls):
        """
        Main entry point for running a blueprint in CLI mode.
        """
        parser = argparse.ArgumentParser(description=f"Launch the {cls.__name__} blueprint.")
        parser.add_argument(
            "--config",
            type=str,
            default="./swarm_config.json",
            help="Path to the configuration file (default: ./swarm_config.json)"
        )
        parser.add_argument(
            "--auto-complete-task",
            action="store_true",
            help="Enable multi-step auto-completion until the task is marked complete."
        )
        args = parser.parse_args()

        logger.debug(f"Launching blueprint with config: {args.config}, auto_complete_task={args.auto_complete_task}")

        config = load_server_config(args.config)
        blueprint = cls(config=config, auto_complete_task=args.auto_complete_task)

        blueprint.interactive_mode()

if __name__ == "__main__":
    PrivateDigitalAssistantsBlueprint.main()
