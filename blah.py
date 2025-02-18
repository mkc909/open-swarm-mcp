"""
Blah Blueprint for Open Swarm.
This minimal blueprint is provided as an example.
"""

import logging
from typing import Dict, Any
from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    fmt = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)

class BlahBlueprint(BlueprintBase):
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "Blah Blueprint",
            "description": "A minimal blueprint example.",
            "required_mcp_servers": [],
            "env_vars": [],
        }
    
    def create_agents(self) -> Dict[str, Agent]:
        logger.debug("Creating agent for BlahBlueprint.")
        
        def echo(content: str) -> str:
            logger.info("Echoing: %s", content)
            return content
        
        agent = Agent(
            name="BlahAgent",
            instructions="Simply echoes any provided input.",
            mcp_servers=[],
            env_vars={},
            functions=[echo],
            parallel_tool_calls=False,
            nemo_guardrails_config="",
        )
        self.set_starting_agent(agent)
        return {"BlahAgent": agent}

# Expose the blueprint's main function at the module level
main = BlahBlueprint.main
