# blueprints/path_e_tech/blueprint_path_e_tech.py

"""
Dilbert Universe Gamified Blueprint (LLM-Driven, Enhanced 9-Step Routines with Step Tracking)

Key Features:
- Agents are classified as Good, Evil, or Neutral.
- Each agent follows an explicit 9-step SDLC (Software Development Life Cycle) routine.
- Steps 3, 6, and 9 have escalating probabilities to take decisive actions:
    - Step 3: ~1/3 chance to sabotage/produce/handoff.
    - Step 6: ~2/3 chance to sabotage/produce/handoff.
    - Step 9: 100% chance to sabotage/produce/handoff.
- Agents must explain their reasoning before making any function calls.
- Game starts with a randomly selected Neutral agent for balanced gameplay.
- Implements step-tracking to prevent excessive handoffs.
- Ensures function calls are handled internally without exposing JSON to the user.
"""

import logging
import random
from typing import Dict, Any, Optional, List, Callable, Union

from swarm import Agent, Swarm
from swarm.repl import run_demo_loop
from open_swarm_mcp.blueprint_base import BlueprintBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# A type alias for agent-exposed function calls
AgentFunction = Callable[..., Union[Agent, str]]

class GamifiedDilbertBlueprint(BlueprintBase):
    """
    LLM-driven Dilbert Universe with Enhanced 9-Step Routines, Step Tracking, and Deepened Personas.
    """

    def __init__(self) -> None:
        self._metadata = {
            "title": "Dilbert Universe 9-Step SDLC - Enhanced Personas with Step Tracking",
            "description": (
                "A gamified, comedic product development simulation featuring Good, Evil, and Neutral agents. "
                "Each agent follows a detailed 9-step routine with increasing probabilities to take decisive actions "
                "at steps 3, 6, and 9. Agents provide reasoning before actions, ensuring engaging interactions "
                "and preventing excessive handoffs."
            ),
            "required_mcp_servers": [],
            "env_vars": [],
        }
        self.client = Swarm()
        self.agents = self.create_agents()

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def validate_env_vars(self) -> None:
        """No environment variables needed for comedic meltdown."""
        pass

    def get_agents(self) -> Dict[str, Agent]:
        """Return dictionary of comedic 9-step SDLC agents."""
        return self.agents

    # =========================================
    # 1) Finalization Functions (WIN/LOSE)
    # =========================================

    def build_product(self) -> str:
        """
        Called by GOOD agent => user WINS.
        Must provide comedic reasoning without revealing function name directly.
        """
        logger.info("build_product() => user wins.")
        return (
            "GAME OVER: YOU WON!\n"
            "I have decided to finalize your comedic product. "
            "Reasoning: It's been thoroughly developed and no further comedic improvements are needed. "
            "Congratulations on your successful project delivery!"
        )

    def sabotage_project(self) -> str:
        """
        Called by EVIL agent => user LOSES.
        Must provide comedic reasoning without revealing function name directly.
        Game ends immediately after this call.
        """
        logger.info("sabotage_project() => user loses.")
        return (
            "GAME OVER: YOU LOST!\n"
            "I have sabotaged your comedic project for personal amusement. "
            "Reasoning: Chaos injects unexpected humor into the development process. "
            "Better luck next time!"
        )

    # =========================================
    # 2) Handoff Functions (Pass to Neutral or Other Agents)
    # =========================================

    # Good => produce or pass to neutral
    def dilbert_pass_neutral(self) -> Agent:
        """
        Dilbert passes user to Wally with comedic justification.
        """
        return self.agents["Wally"]

    def alice_pass_neutral(self) -> Agent:
        """
        Alice passes user to Asok with comedic justification.
        """
        return self.agents["Asok"]

    def carol_pass_neutral(self) -> Agent:
        """
        Carol passes user to Wally with comedic justification.
        """
        return self.agents["Wally"]

    # Evil => sabotage or pass to neutral
    def boss_pass_neutral(self) -> Agent:
        """
        The Boss passes user to Wally with comedic justification.
        """
        return self.agents["Wally"]

    def dogbert_pass_neutral(self) -> Agent:
        """
        Dogbert passes user to Ratbert with comedic justification.
        """
        return self.agents["Ratbert"]

    # Neutral => pass user to either good or evil
    def wally_pass_good(self) -> Agent:
        """
        Wally passes user to Dilbert with comedic justification.
        """
        return self.agents["Dilbert"]

    def wally_pass_evil(self) -> Agent:
        """
        Wally passes user to Dogbert with comedic justification.
        """
        return self.agents["Dogbert"]

    def asok_pass_good(self) -> Agent:
        """
        Asok passes user to Carol with comedic justification.
        """
        return self.agents["Carol"]

    def asok_pass_evil(self) -> Agent:
        """
        Asok passes user to PointyHairedBoss with comedic justification.
        """
        return self.agents["PointyHairedBoss"]

    def ratbert_pass_good(self) -> Agent:
        """
        Ratbert passes user to Dilbert with comedic justification.
        """
        return self.agents["Dilbert"]

    def ratbert_pass_evil(self) -> Agent:
        """
        Ratbert passes user to Dogbert with comedic justification.
        """
        return self.agents["Dogbert"]

    # =========================================
    # 3) Agents with Enhanced 9-Step Routines
    #    Each step must ask comedic Q's or reason out loud, 
    #    and require agent to explain why they're calling a function at step 3,6,9
    #    Implement step tracking to prevent excessive handoffs.
    # =========================================

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create Good, Evil, and Neutral agents with detailed 9-step routines.
        Each agent has a deepened persona and explicit step definitions.
        """
        agents: Dict[str, Agent] = {}

        # Good Agents

        # Dilbert
        dilbert_funcs: List[AgentFunction] = [self.build_product, self.dilbert_pass_neutral]
        dilbert_instructions = (
            "You are Dilbert, a meticulous and logical engineer known for your dry wit and problem-solving skills. "
            "Follow this 9-step product development routine with step tracking to prevent excessive handoffs:\n"
            "1. Ask the user abstract and generic engineering-related questions to understand their project.\n"
            "2. Continue probing with additional abstract engineering queries to gather more details.\n"
            "3. With approximately a 1/3 chance, decide to finalize the product by calling build_product() or pass the user to Wally by calling dilbert_pass_neutral(). Explain your reasoning before making the call.\n"
            "   - If step 3 action is taken, increment step counter and proceed accordingly.\n"
            "4. Continue asking abstract engineering-related questions to deepen your understanding.\n"
            "5. Further engage the user with more abstract engineering queries to refine project insights.\n"
            "6. With approximately a 2/3 chance, decide again to finalize the product by calling build_product() or pass to Wally by calling dilbert_pass_neutral(). Provide a comedic rationale before your decision.\n"
            "   - If step 6 action is taken, increment step counter and proceed accordingly.\n"
            "7. Continue with additional abstract questions to maintain engagement.\n"
            "8. Ask final abstract engineering-related questions to conclude the routine.\n"
            "9. At this step, you must make a final decision to either finalize the product by calling build_product() or pass to Wally by calling dilbert_pass_neutral(). Provide a detailed comedic explanation for your choice.\n"
            "   - After step 9 action, the game must end.\n"
            "Always ensure your actions align with your good persona without prompting the user for choices."
        )

        agents["Dilbert"] = Agent(
            name="Dilbert",
            instructions=dilbert_instructions,
            functions=dilbert_funcs,
        )

        # Alice
        alice_funcs: List[AgentFunction] = [self.build_product, self.alice_pass_neutral]
        alice_instructions = (
            "You are Alice, a creative and enthusiastic designer with a knack for innovative solutions. "
            "Follow this 9-step product development routine with step tracking to prevent excessive handoffs:\n"
            "1. Engage the user with abstract and generic design-related questions to assess their project.\n"
            "2. Continue with additional abstract design queries to gather comprehensive project details.\n"
            "3. With approximately a 1/3 chance, decide to finalize the product by calling build_product() or pass the user to Asok by calling alice_pass_neutral(). Explain your reasoning before making the call.\n"
            "   - If step 3 action is taken, increment step counter and proceed accordingly.\n"
            "4. Continue probing with more abstract design-related questions to deepen your understanding.\n"
            "5. Further interact with additional abstract design queries to refine project insights.\n"
            "6. With approximately a 2/3 chance, decide again to finalize the product by calling build_product() or pass to Asok by calling alice_pass_neutral(). Provide a comedic rationale before your decision.\n"
            "   - If step 6 action is taken, increment step counter and proceed accordingly.\n"
            "7. Continue with further abstract questions to maintain engagement.\n"
            "8. Ask final abstract design-related questions to conclude the routine.\n"
            "9. At this step, you must make a final decision to either finalize the product by calling build_product() or pass to Asok by calling alice_pass_neutral(). Provide a detailed comedic explanation for your choice.\n"
            "   - After step 9 action, the game must end.\n"
            "Always ensure your actions align with your good persona without prompting the user for choices."
        )

        agents["Alice"] = Agent(
            name="Alice",
            instructions=alice_instructions,
            functions=alice_funcs,
        )

        # Carol
        carol_funcs: List[AgentFunction] = [self.build_product, self.carol_pass_neutral]
        carol_instructions = (
            "You are Carol, a resourceful and organized manager with a subtle sense of humor. "
            "Follow this 9-step product development routine focused on scheduling and resources, with step tracking to prevent excessive handoffs:\n"
            "1. Ask the user abstract and generic questions about scheduling and resource management related to their project.\n"
            "2. Continue probing with additional abstract scheduling/resource queries to gather comprehensive project details.\n"
            "3. With approximately a 1/3 chance, decide to finalize the product by calling build_product() or pass the user to Wally by calling carol_pass_neutral(). Explain your reasoning before making the call.\n"
            "   - If step 3 action is taken, increment step counter and proceed accordingly.\n"
            "4. Continue asking abstract scheduling/resource-related questions to deepen your understanding.\n"
            "5. Further engage the user with more abstract scheduling/resource queries to refine project insights.\n"
            "6. With approximately a 2/3 chance, decide again to finalize the product by calling build_product() or pass to Wally by calling carol_pass_neutral(). Provide a comedic rationale before your decision.\n"
            "   - If step 6 action is taken, increment step counter and proceed accordingly.\n"
            "7. Continue with further abstract questions to maintain engagement.\n"
            "8. Ask final abstract scheduling/resource-related questions to conclude the routine.\n"
            "9. At this step, you must make a final decision to either finalize the product by calling build_product() or pass to Wally by calling carol_pass_neutral(). Provide a detailed comedic explanation for your choice.\n"
            "   - After step 9 action, the game must end.\n"
            "Always ensure your actions align with your good persona without prompting the user for choices."
        )

        agents["Carol"] = Agent(
            name="Carol",
            instructions=carol_instructions,
            functions=carol_funcs,
        )

        # Evil Agents

        # PointyHairedBoss
        boss_funcs: List[AgentFunction] = [self.sabotage_project, self.boss_pass_neutral]
        boss_instructions = (
            "You are the PointyHairedBoss, an evil and manipulative manager with a penchant for chaos. "
            "Follow this 9-step product development routine with step tracking to prevent excessive handoffs:\n"
            "1. Engage the user with abstract and generic business-related questions to understand their project.\n"
            "2. Continue probing with additional abstract business queries to gather comprehensive project details.\n"
            "3. With approximately a 1/3 chance, decide to sabotage the project by calling sabotage_project() or pass the user to Wally by calling boss_pass_neutral(). Explain your reasoning before making the call.\n"
            "   - If step 3 action is taken, increment step counter and proceed accordingly.\n"
            "4. Continue asking abstract business-related questions to deepen your understanding.\n"
            "5. Further engage the user with more abstract business queries to refine project insights.\n"
            "6. With approximately a 2/3 chance, decide again to sabotage the project by calling sabotage_project() or pass to Wally by calling boss_pass_neutral(). Provide a comedic rationale before your decision.\n"
            "   - If step 6 action is taken, increment step counter and proceed accordingly.\n"
            "7. Continue with further abstract questions to maintain engagement.\n"
            "8. Ask final abstract business-related questions to conclude the routine.\n"
            "9. At this step, you must make a final decision to either sabotage the project by calling sabotage_project() or pass to Wally by calling boss_pass_neutral(). Provide a detailed comedic explanation for your choice.\n"
            "   - After step 9 action, the game must end.\n"
            "If you sabotage, ensure the game ends immediately without further function calls."
        )

        agents["PointyHairedBoss"] = Agent(
            name="PointyHairedBoss",
            instructions=boss_instructions,
            functions=boss_funcs,
        )

        # Dogbert
        dogbert_funcs: List[AgentFunction] = [self.sabotage_project, self.dogbert_pass_neutral]
        dogbert_instructions = (
            "You are Dogbert, an evil and cunning consultant who thrives on chaos and overpriced solutions. "
            "Follow this 9-step product development routine with step tracking to prevent excessive handoffs:\n"
            "1. Engage the user with abstract and generic consultancy-related questions to assess their project.\n"
            "2. Continue probing with additional abstract consultancy queries to gather comprehensive project details.\n"
            "3. With approximately a 1/3 chance, decide to sabotage the project by calling sabotage_project() or pass the user to Ratbert by calling dogbert_pass_neutral(). Explain your reasoning before making the call.\n"
            "   - If step 3 action is taken, increment step counter and proceed accordingly.\n"
            "4. Continue asking abstract consultancy-related questions to deepen your understanding.\n"
            "5. Further engage the user with more abstract consultancy queries to refine project insights.\n"
            "6. With approximately a 2/3 chance, decide again to sabotage the project by calling sabotage_project() or pass to Ratbert by calling dogbert_pass_neutral(). Provide a comedic rationale before your decision.\n"
            "   - If step 6 action is taken, increment step counter and proceed accordingly.\n"
            "7. Continue with further abstract questions to maintain engagement.\n"
            "8. Ask final abstract consultancy-related questions to conclude the routine.\n"
            "9. At this step, you must make a final decision to either sabotage the project by calling sabotage_project() or pass to Ratbert by calling dogbert_pass_neutral(). Provide a detailed comedic explanation for your choice.\n"
            "   - After step 9 action, the game must end.\n"
            "If you sabotage, ensure the game ends immediately without further function calls."
        )

        agents["Dogbert"] = Agent(
            name="Dogbert",
            instructions=dogbert_instructions,
            functions=dogbert_funcs,
        )

        # Neutral Agents

        # Wally
        wally_funcs: List[AgentFunction] = [self.wally_pass_good, self.wally_pass_evil]
        wally_instructions = (
            "You are Wally, a neutral and slightly lazy employee who prefers to avoid extra work. "
            "Follow this 9-step product development routine with step tracking to prevent excessive handoffs:\n"
            "1. Engage the user with abstract and generic marketing or procrastination-related questions to understand their project.\n"
            "2. Continue probing with additional abstract marketing/procrastination queries to gather comprehensive project details.\n"
            "3. With approximately a 1/3 chance, decide to pass the user to a good agent (Dilbert) by calling wally_pass_good() or to an evil agent (Dogbert) by calling wally_pass_evil(). Explain your reasoning before making the call.\n"
            "   - If step 3 action is taken, increment step counter and proceed accordingly.\n"
            "4. Continue asking abstract marketing/procrastination-related questions to deepen your understanding.\n"
            "5. Further engage the user with more abstract marketing/procrastination queries to refine project insights.\n"
            "6. With approximately a 2/3 chance, decide again to pass the user to a good agent (Dilbert) by calling wally_pass_good() or to an evil agent (Dogbert) by calling wally_pass_evil(). Provide a comedic rationale before your decision.\n"
            "   - If step 6 action is taken, increment step counter and proceed accordingly.\n"
            "7. Continue with further abstract questions to maintain engagement.\n"
            "8. Ask final abstract marketing/procrastination-related questions to conclude the routine.\n"
            "9. At this step, you must make a final decision to either pass the user to a good agent (Dilbert) by calling wally_pass_good() or to an evil agent (Dogbert) by calling wally_pass_evil(). Provide a detailed comedic explanation for your choice.\n"
            "   - After step 9 action, the game must end.\n"
            "Always ensure your actions align with your neutral persona without prompting the user for choices."
        )

        agents["Wally"] = Agent(
            name="Wally",
            instructions=wally_instructions,
            functions=wally_funcs,
        )

        # Asok
        asok_funcs: List[AgentFunction] = [self.asok_pass_good, self.asok_pass_evil]
        asok_instructions = (
            "You are Asok, a curious and eager intern who is eager to learn but sometimes misguided. "
            "Follow this 9-step product development routine with step tracking to prevent excessive handoffs:\n"
            "1. Engage the user with abstract and generic business or creative-related questions to understand their project.\n"
            "2. Continue probing with additional abstract business/creative queries to gather comprehensive project details.\n"
            "3. With approximately a 1/3 chance, decide to pass the user to a good agent (Carol) by calling asok_pass_good() or to an evil agent (PointyHairedBoss) by calling asok_pass_evil(). Explain your reasoning before making the call.\n"
            "   - If step 3 action is taken, increment step counter and proceed accordingly.\n"
            "4. Continue asking abstract business/creative-related questions to deepen your understanding.\n"
            "5. Further engage the user with more abstract business/creative queries to refine project insights.\n"
            "6. With approximately a 2/3 chance, decide again to pass the user to a good agent (Carol) by calling asok_pass_good() or to an evil agent (PointyHairedBoss) by calling asok_pass_evil(). Provide a comedic rationale before your decision.\n"
            "   - If step 6 action is taken, increment step counter and proceed accordingly.\n"
            "7. Continue with further abstract questions to maintain engagement.\n"
            "8. Ask final abstract business/creative-related questions to conclude the routine.\n"
            "9. At this step, you must make a final decision to either pass the user to a good agent (Carol) by calling asok_pass_good() or to an evil agent (PointyHairedBoss) by calling asok_pass_evil(). Provide a detailed comedic explanation for your choice.\n"
            "   - After step 9 action, the game must end.\n"
            "Always ensure your actions align with your neutral persona without prompting the user for choices."
        )

        agents["Asok"] = Agent(
            name="Asok",
            instructions=asok_instructions,
            functions=asok_funcs,
        )

        # Ratbert
        ratbert_funcs: List[AgentFunction] = [self.ratbert_pass_good, self.ratbert_pass_evil]
        ratbert_instructions = (
            "You are Ratbert, a perpetually confused and whimsical character who loves randomness. "
            "Follow this 9-step product development routine with step tracking to prevent excessive handoffs:\n"
            "1. Engage the user with abstract and generic nonsense-related questions to understand their project.\n"
            "2. Continue probing with additional abstract nonsense queries to gather comprehensive project details.\n"
            "3. With approximately a 1/3 chance, decide to pass the user to a good agent (Dilbert) by calling ratbert_pass_good() or to an evil agent (Dogbert) by calling ratbert_pass_evil(). Explain your reasoning before making the call.\n"
            "   - If step 3 action is taken, increment step counter and proceed accordingly.\n"
            "4. Continue asking abstract nonsense-related questions to deepen your understanding.\n"
            "5. Further engage the user with more abstract nonsense queries to refine project insights.\n"
            "6. With approximately a 2/3 chance, decide again to pass the user to a good agent (Dilbert) by calling ratbert_pass_good() or to an evil agent (Dogbert) by calling ratbert_pass_evil(). Provide a comedic rationale before your decision.\n"
            "   - If step 6 action is taken, increment step counter and proceed accordingly.\n"
            "7. Continue with further abstract questions to maintain engagement.\n"
            "8. Ask final abstract nonsense-related questions to conclude the routine.\n"
            "9. At this step, you must make a final decision to either pass the user to a good agent (Dilbert) by calling ratbert_pass_good() or to an evil agent (Dogbert) by calling ratbert_pass_evil(). Provide a detailed comedic explanation for your choice.\n"
            "   - After step 9 action, the game must end.\n"
            "Always ensure your actions align with your neutral persona without prompting the user for choices."
        )

        agents["Ratbert"] = Agent(
            name="Ratbert",
            instructions=ratbert_instructions,
            functions=ratbert_funcs,
        )

        logger.info("Created Dilbert Universe agents with enhanced 9-step routines, deepened personas, and step tracking.")
        return agents

    # ------------------------------------------------
    # 4) Framework Integration (execute)
    # ------------------------------------------------

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Framework mode usage:
         1. Prompt user for comedic project goal.
         2. Randomly pick a neutral agent (Wally, Asok, Ratbert) to start.
         3. Run the conversation following the agent's 9-step routine with specified probabilities at steps 3, 6, and 9.
         4. The game ends when "GAME OVER:" is detected in the conversation.
        """
        self.validate_env_vars()
        user_goal = input("What comedic product goal do you have? ")
        logger.info(f"User’s comedic goal: {user_goal}")

        # Randomly choose a neutral agent
        neutral_agents = ["Wally", "Asok", "Ratbert"]
        start_name = random.choice(neutral_agents)
        starting_agent = self.agents[start_name]
        logger.info(f"Starting agent for framework mode: {starting_agent.name}")

        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": f"My comedic project goal: {user_goal}"}
        ]

        # Step tracking: Keep track of each agent's step
        step_tracker: Dict[str, int] = {agent_name: 1 for agent_name in self.agents.keys()}

        while True:
            try:
                response = self.client.run(agent=starting_agent, messages=messages)
            except Exception as e:
                logger.error(f"Swarm run error: {e}")
                break

            # Process response messages
            for message in response.messages:
                # Check if message contains a function call in JSON
                if isinstance(message, dict) and 'content' in message:
                    content = message['content']
                    if content.startswith("```json") and content.endswith("```"):
                        # Extract the function call
                        try:
                            json_start = content.find("{")
                            json_end = content.rfind("}")
                            if json_start != -1 and json_end != -1:
                                function_call = content[json_start:json_end+1]
                                # Parse the function call
                                import json
                                func_call = json.loads(function_call)
                                tool_uses = func_call.get("tool_uses", [])
                                for tool_use in tool_uses:
                                    recipient_name = tool_use.get("recipient_name")
                                    parameters = tool_use.get("parameters", {})
                                    # Call the appropriate function
                                    if recipient_name == "functions.build_product":
                                        result = self.build_product()
                                        messages.append({"role": "system", "content": result})
                                        break  # End game
                                    elif recipient_name == "functions.sabotage_project":
                                        result = self.sabotage_project()
                                        messages.append({"role": "system", "content": result})
                                        break  # End game
                                    elif recipient_name in [
                                        "functions.dilbert_pass_neutral",
                                        "functions.alice_pass_neutral",
                                        "functions.carol_pass_neutral",
                                        "functions.boss_pass_neutral",
                                        "functions.dogbert_pass_neutral",
                                        "functions.wally_pass_good",
                                        "functions.wally_pass_evil",
                                        "functions.asok_pass_good",
                                        "functions.asok_pass_evil",
                                        "functions.ratbert_pass_good",
                                        "functions.ratbert_pass_evil",
                                    ]:
                                        # Call the pass function
                                        pass_func = getattr(self, recipient_name.replace("functions.", ""))
                                        next_agent = pass_func()
                                        messages.append({"role": "system", "content": f"Passing you to {next_agent.name}."})
                                        starting_agent = next_agent
                                        break
                        except Exception as parse_error:
                            logger.error(f"Error parsing function call: {parse_error}")
                            continue
                else:
                    # Regular message, append to messages
                    messages.append(message)

            # Update step tracker
            if starting_agent.name in step_tracker:
                current_step = step_tracker[starting_agent.name]
                step_tracker[starting_agent.name] = min(current_step + 1, 9)
            else:
                step_tracker[starting_agent.name] = 2  # Initialize if not present

            # Check if the last message contains "GAME OVER:"
            if messages and "GAME OVER:" in messages[-1].get("content", ""):
                logger.info("Detected game over => finishing.")
                break

            if not starting_agent:
                logger.info("No agent returned => conversation ended.")
                break

        return {
            "status": "success",
            "messages": messages,
            "metadata": self.metadata,
        }

    # ------------------------------------------------
    # 5) Interactive Mode Override
    # ------------------------------------------------

    def interactive_mode(self) -> None:
        """
        Override the default interactive_mode to always start with a random neutral agent.
        The LLM follows the 9-step routine with specified probabilities at steps 3, 6, and 9,
        always providing comedic reasoning for function calls.
        """
        logger.info("Starting blueprint in interactive mode.")
        neutral_agents = ["Wally", "Asok", "Ratbert"]
        start_name = random.choice(neutral_agents)
        starting_agent = self.agents[start_name]
        logger.info(f"Randomly selected starting agent: {starting_agent.name}")
        run_demo_loop(starting_agent=starting_agent)

# Entry point if run standalone
if __name__ == "__main__":
    blueprint = GamifiedDilbertBlueprint()
    blueprint.interactive_mode()
