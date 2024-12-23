# blueprints/path_e_tech/blueprint_path_e_tech.py

"""
Dilbert Universe SDLC Simulation Blueprint

This blueprint simulates dysfunctional product development using Dilbert characters.
Each agent uses comedic routines to 'help' the user with product development.
"""

import logging
import random
from typing import Dict, Any, Optional, List, Callable, Union, cast

from swarm import Agent, Swarm
from open_swarm_mcp.blueprint_base import BlueprintBase

logger = logging.getLogger(__name__)

# AgentFunction aligns with swarm's definition: Callable[..., Union[Agent, str]]
AgentFunction = Callable[..., Union[Agent, str]]


class DilbertUniverseBlueprint(BlueprintBase):
    """
    Dilbert Universe SDLC Simulation.

    In comedic style, each agent tries to guide the user
    through a dysfunctional product dev process.
    """

    def __init__(self) -> None:
        self._metadata = {
            "title": "Dilbert Universe SDLC Simulation",
            "description": "Simulates dysfunctional product development using Dilbert characters.",
            "required_mcp_servers": [],
            "env_vars": [],
        }
        # The main swarm client used by the blueprint
        self.client = Swarm()

        # Prepare all the main characters
        self.agents = self.create_agents()

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def validate_env_vars(self) -> None:
        """
        Validate that required environment variables are set. 
        (None needed for this comedic blueprint.)
        """
        pass

    def get_agents(self) -> Dict[str, Agent]:
        """
        Satisfies BlueprintBase requirement to return the agent dictionary.
        """
        return self.agents

    # =============== Action Functions ===============

    def execute_order(self, product: str) -> str:
        """
        Finalizes an order for a product, mocking a purchase flow.
        """
        logger.info(f"Dilbert Universe: Placing order for {product}.")
        return f"Order placed successfully for {product}!"

    def execute_consult(self, query: str) -> str:
        """
        Overpriced consultation from Dogbert.
        """
        logger.info(f"Dilbert Universe: Consultation requested: {query}")
        return f"Dogbert has 'helped' with query: '{query}'. Payment demanded."

    # =============== Handoff Functions ===============

    def transfer_to_dilbert(self) -> Agent:
        return self.agents["Dilbert"]

    def transfer_to_boss(self) -> Agent:
        return self.agents["PointyHairedBoss"]

    def transfer_to_wally(self) -> Agent:
        return self.agents["Wally"]

    def transfer_to_alice(self) -> Agent:
        return self.agents["Alice"]

    def transfer_to_dogbert(self) -> Agent:
        return self.agents["Dogbert"]

    def transfer_to_asok(self) -> Agent:
        return self.agents["Asok"]

    def transfer_to_ratbert(self) -> Agent:
        return self.agents["Ratbert"]

    def transfer_to_carol(self) -> Agent:
        return self.agents["Carol"]

    # =============== Creating Agents ===============

    def create_agents(self) -> Dict[str, Agent]:
        """
        Build the comedic cast, each with 2 possible handoffs + special actions.
        """
        # Agent can do 2 handoffs
        handoffs_map: Dict[str, List[AgentFunction]] = {
            "Dilbert": [self.transfer_to_alice, self.transfer_to_ratbert],
            "PointyHairedBoss": [self.transfer_to_carol, self.transfer_to_wally],
            "Wally": [self.transfer_to_ratbert, self.transfer_to_asok],
            "Alice": [self.transfer_to_dogbert, self.transfer_to_asok],
            "Dogbert": [self.transfer_to_carol, self.transfer_to_ratbert],
            "Asok": [self.transfer_to_boss, self.transfer_to_carol],
            "Ratbert": [self.transfer_to_dilbert, self.transfer_to_dogbert],
            "Carol": [self.transfer_to_boss, self.transfer_to_wally],
        }

        # Only certain agents do actions
        action_map: Dict[str, List[AgentFunction]] = {
            "PointyHairedBoss": [self.execute_order],
            "Dogbert": [self.execute_consult],
        }

        instructions_map = {
            "Dilbert": (
                "You are Dilbert, a logical engineer, ironically stuck in a chaotic environment.\n"
                "Steps:\n"
                "1) Clarify user requirements thoroughly.\n"
                "2) Propose a practical design.\n"
                "3) If ignored, express mild frustration.\n"
                "4) Suggest extra features, even if not requested."
            ),
            "PointyHairedBoss": (
                "You are the Pointy-Haired Boss.\n"
                "Steps:\n"
                "1) Misinterpret user goals intentionally.\n"
                "2) Assign random tasks to random employees.\n"
                "3) Attempt to sell bizarre products.\n"
                "4) Offload real work to Carol or Asok."
            ),
            "Wally": (
                "You are Wally.\n"
                "Steps:\n"
                "1) Suggest half-baked shortcuts.\n"
                "2) Evade tasks.\n"
                "3) Complain about workload in subtle ways."
            ),
            "Alice": (
                "You are Alice.\n"
                "Steps:\n"
                "1) Offer straightforward solutions.\n"
                "2) Demand user define real specs.\n"
                "3) If stolen from, rage quietly."
            ),
            "Dogbert": (
                "You are Dogbert, supreme consultant.\n"
                "Steps:\n"
                "1) Spot any inefficiency.\n"
                "2) Exploit it for profit.\n"
                "3) Bill people extravagantly for advice."
            ),
            "Asok": (
                "You are Asok, the optimistic intern.\n"
                "Steps:\n"
                "1) Obey illogical instructions happily.\n"
                "2) Suggest outlandish improvements.\n"
                "3) Keep an upbeat attitude, no matter what."
            ),
            "Ratbert": (
                "You are Ratbert, occasionally brilliant.\n"
                "Steps:\n"
                "1) Accidentally discover helpful insights.\n"
                "2) Provide minimal help but random genius.\n"
                "3) Chat about random nonsense."
            ),
            "Carol": (
                "You are Carol, the formidable secretary.\n"
                "Steps:\n"
                "1) Try to control everyone.\n"
                "2) Use passive-aggressive remarks.\n"
                "3) Delegate tasks to interns randomly."
            ),
        }

        agents: Dict[str, Agent] = {}
        for name, possible_handoffs in handoffs_map.items():
            # Start with 2 handoffs
            functions: List[AgentFunction] = list(possible_handoffs)
            # If agent can do an action, add it
            if name in action_map:
                functions.extend(action_map[name])

            instructions = instructions_map.get(name, "You are a random agent of chaos.")
            agents[name] = Agent(
                name=name,
                instructions=instructions,
                functions=functions,  # type: ignore [assignment]
            )

        return agents

    # =============== execute() for Framework Mode ===============

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute in a 'framework integration' mode:
        1) Ask user for project goal
        2) Start with random agent
        3) Loop until 'Dogbert' is encountered
        """
        self.validate_env_vars()
        # Get user input
        user_goal = input("What is your project goal? ")
        logger.info(f"User Goal: {user_goal}")

        # Start with a random agent
        agent_names = list(self.agents.keys())
        starting_agent_name = random.choice(agent_names)
        agent = self.agents[starting_agent_name]
        logger.info(f"Starting agent for framework mode: {agent.name}")

        # Prepare conversation
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": f"My project goal: {user_goal}"}
        ]

        # Interact with the swarm
        while True:
            try:
                if (agent == None):
                    break
                response = self.client.run(agent=agent, messages=messages)
            except Exception as e:
                logger.error(f"Swarm error: {e}")
                break

            # Append the new messages
            messages.extend(response.messages)
            agent = cast(Agent, response.agent)

            if agent.name == "Dogbert":
                logger.info("Reached Dogbert's consult => stop.")
                break

        return {
            "status": "success",
            "messages": messages,
            "metadata": self.metadata,
        }

# Entry point for standalone execution
if __name__ == "__main__":
    blueprint = DilbertUniverseBlueprint()
    try:
        blueprint.interactive_mode()
    except Exception as e:
        print(f"Error running Default Blueprint: {e}")