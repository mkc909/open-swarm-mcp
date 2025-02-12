import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from nemoguardrails import LLMRails, RailsConfig

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

    NEW FEATURES:
      1. Auto-completion of tasks until completion (via single-token LLM check).
      2. Dynamic updating of the user's goal based on LLM analysis of the conversation history.
      3. Configurable update frequency for the user goal, to optimize inference costs.
    """

    def __init__(
        self,
        config: dict,
        auto_complete_task: bool = False,
        update_user_goal: bool = False,
        update_user_goal_frequency: int = 5,
        **kwargs
    ):
        """
        Initialize the blueprint and register agents.

        Args:
            config (dict): Configuration dictionary.
            auto_complete_task (bool): If True, the system will keep executing steps until
                the task is marked complete by the LLM.
            update_user_goal (bool): If True, the system will dynamically update the user's goal
                based on an LLM analysis of the conversation history.
            update_user_goal_frequency (int): Specifies how many messages (or iterations)
                should occur between user goal updates.
            **kwargs: Additional parameters (e.g., shared swarm_instance).
        """
        self.auto_complete_task = auto_complete_task
        self.update_user_goal = update_user_goal
        self.update_user_goal_frequency = update_user_goal_frequency
        # Initialize a counter to track how many messages have been processed since the last goal update.
        self.last_goal_update_count = 0

        logger.debug(f"Initializing BlueprintBase with config: {redact_sensitive_data(config)}")
        if not hasattr(self, 'metadata') or not isinstance(self.metadata, dict):
            raise AssertionError("Blueprint metadata must be defined and must be a dictionary.")

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
        # Store the original user goal
        self.context_variables["user_goal"] = ""

        self.starting_agent = None

        # Validate Environment Variables First
        required_env_vars = set(self.metadata.get('env_vars', []))
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.debug("Required environment variables validation successful.")

        # Validate MCP Servers Before Creating Agents
        self.required_mcp_servers = self.metadata.get('required_mcp_servers', [])
        logger.debug(f"Required MCP servers: {self.required_mcp_servers}")

        # Create Agents Only After Validation Passes
        agents = self.create_agents()

        # Initialize NeMo Guardrails Before Registering Agents
        for agent_name, agent in agents.items():
            if agent.nemo_guardrails_config:
                guardrails_path = os.path.join("nemo_guardrails", agent.nemo_guardrails_config)
                
                try:
                    # Load NeMo Guardrails configuration
                    rails_config = RailsConfig.from_path(guardrails_path)
                    agent.nemo_guardrails_instance = LLMRails(rails_config)
                    logger.debug(f"✅ Loaded NeMo Guardrails for agent: {agent.name} ({agent.nemo_guardrails_config})")
                except Exception as e:
                    logger.warning(f"Could not load NeMo Guardrails for agent {agent.name}: {e}")

        # Finally Register Agents After Everything is Validated
        self.swarm.agents.update(agents)
        logger.debug(f"Agents registered: {list(agents.keys())}")

        asyncio.run(self.async_discover_agent_tools())
        logger.debug("Tool discovery completed.")

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the blueprint including title, description, and dependencies.
        Subclasses must implement this.
        """
        raise NotImplementedError

    @abstractmethod
    def create_agents(self) -> Dict[str, Any]:
        """
        Create and return the agents for this blueprint.
        Subclasses must implement this.
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
            dict: Response from Swarm and updated context variables.
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

        # Ensure the response has the expected structure
        if not hasattr(response, 'messages'):
            logger.error("Response does not have 'messages' attribute.")
            response.messages = []

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
        The LLM is provided with the user's goal, a brief conversation summary,
        and the last assistant message. It must respond with a single token: YES or NO.

        Args:
            user_goal (str): The user's original (or updated) goal.
            conversation_summary (str): A short summary of recent conversation.
            last_assistant_message (str): The most recent assistant response.

        Returns:
            bool: True if the LLM returns a response starting with 'YES', False otherwise.
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

    def _update_user_goal(self, messages: List[Dict[str, str]]) -> None:
        """
        Update the user's goal based on an LLM analysis of the conversation history.
        This method generates a concise summary of the user's objective from the dialogue.

        Args:
            messages (list): The full conversation history.
        
        Updates:
            self.context_variables["user_goal"] with the new goal.
        """
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are an assistant that summarizes the user's primary objective based on the conversation so far. "
                    "Provide a concise, one-sentence summary capturing the user's goal."
                )
            },
            {
                "role": "user",
                "content": "Summarize the user's goal based on this conversation:\n" +
                           "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            }
        ]
        summary_response = self.swarm.run_llm(
            messages=prompt,
            max_tokens=30,
            temperature=0.3
        )
        new_goal = summary_response.choices[0].message["content"].strip()
        logger.debug(f"Updated user goal from LLM: {new_goal}")
        self.context_variables["user_goal"] = new_goal

    def interactive_mode(self, stream: bool = False) -> None:
        """
        Start the interactive REPL loop using the blueprint's Swarm instance.
        If auto_complete_task is enabled, the system will continue executing steps until
        a completion check indicates the task is complete.
        If update_user_goal is enabled, the user's goal is updated dynamically every N messages,
        as defined by update_user_goal_frequency.

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
        first_user_input = True

        # Counter for updating the user goal
        message_count = 0

        while True:
            print("\033[90mUser\033[0m: ", end="")
            user_input = input().strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting interactive mode.")
                break

            if first_user_input:
                self.context_variables["user_goal"] = user_input
                first_user_input = False

            messages.append({"role": "user", "content": user_input})
            message_count += 1

            result = self.run_with_context(messages, self.context_variables or {})
            swarm_response = result["response"]

            if stream:
                self._process_and_print_streaming_response(swarm_response)
            else:
                self._pretty_print_response(swarm_response.messages)

            messages.extend(swarm_response.messages)
            agent = swarm_response.agent

            # Update user goal only if update_user_goal is enabled and the message count exceeds frequency
            if self.update_user_goal and (message_count - self.last_goal_update_count) >= self.update_user_goal_frequency:
                self._update_user_goal(messages)
                self.last_goal_update_count = message_count

            # If auto-complete is enabled, continue until the task is complete.
            if self.auto_complete_task:
                conversation_summary = " ".join(
                    [msg["content"] for msg in messages[-4:] if msg.get("content")]
                )
                last_assistant = ""
                for msg in reversed(swarm_response.messages):
                    if msg["role"] == "assistant" and msg.get("content"):
                        last_assistant = msg["content"]
                        break

                while not self._is_task_done(
                    self.context_variables.get("user_goal", ""),
                    conversation_summary,
                    last_assistant
                ):
                    result2 = self.run_with_context(messages, self.context_variables or {})
                    swarm_response = result2["response"]
                    if stream:
                        self._process_and_print_streaming_response(swarm_response)
                    else:
                        self._pretty_print_response(swarm_response.messages)
                    messages.extend(swarm_response.messages)
                    agent = swarm_response.agent

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
        parser.add_argument(
            "--update-user-goal",
            action="store_true",
            help="Enable dynamic updating of the user goal based on chat history."
        )
        parser.add_argument(
            "--update-user-goal-frequency",
            type=int,
            default=5,
            help="Number of messages between each dynamic user goal update (default: 5)."
        )
        args = parser.parse_args()

        logger.debug(f"Launching blueprint with config: {args.config}, auto_complete_task={args.auto_complete_task}, update_user_goal={args.update_user_goal}, update_user_goal_frequency={args.update_user_goal_frequency}")

        config = load_server_config(args.config)
        blueprint = cls(
            config=config,
            auto_complete_task=args.auto_complete_task,
            update_user_goal=args.update_user_goal,
            update_user_goal_frequency=args.update_user_goal_frequency
        )

        blueprint.interactive_mode()
