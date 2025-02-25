"""
University Support Blueprint

A multi-agent system providing university support using LLM-driven responses, SQLite-backed tools,
and Canvas metadata integration, with graceful failure for all operations.
"""

import os
import logging
import json
from typing import Dict, Any, List

from swarm.types import Agent
from swarm.extensions.blueprint import BlueprintBase

# Import model_queries for live DB access
from blueprints.university.model_queries import (
    search_courses, search_students, search_teaching_units, search_topics,
    search_learning_objectives, search_subtopics, search_enrollments,
    search_assessment_items, extended_comprehensive_search, comprehensive_search
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class UniversitySupportBlueprint(BlueprintBase):
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "University Support System",
            "description": "A multi-agent system for university support, using LLM-driven responses, SQLite tools, and Canvas metadata with graceful failure.",
            "required_mcp_servers": ["sqlite"],
            "cli_name": "uni",
            "env_vars": ["SQLITE_DB_PATH"]
        }

    def run_with_context(self, messages: List[Dict[str, str]], context_variables: dict) -> dict:
        logger.debug(f"Running with context. Messages: {json.dumps(messages, indent=2) if messages else 'None'}, Context: {json.dumps(context_variables, indent=2) if context_variables else 'None'}")
        if not isinstance(messages, list):
            logger.error(f"Invalid messages type: {type(messages)}. Expected list.")
            raise ValueError("Messages must be a list")
        if not isinstance(context_variables, dict):
            logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
            raise ValueError("context_variables must be a dictionary")

        result = super().run_with_context(messages, context_variables)
        logger.debug(f"run_with_context result type: {type(result)}")
        return result

    def create_agents(self) -> Dict[str, Agent]:
        """Create agents with dynamic instructions and tools for university support."""
        agents = {}

        def handoff_to_support() -> Agent:
            logger.debug("Handoff to SupportAgent")
            return agents["SupportAgent"]

        def handoff_to_learning() -> Agent:
            logger.debug("Handoff to LearningAgent")
            return agents["LearningAgent"]

        def handoff_to_triage() -> Agent:
            logger.debug("Handoff to TriageAgent")
            return agents["TriageAgent"]

        triage_instructions = (
            "You are TriageAgent, the coordinator for university support. Analyze student queries and preloaded metadata "
            "from the message history. The learning objectives are in the 'get_learning_objectives' tool response under "
            "'learningCanvas.content'. For queries about 'learning objectives' or 'objectives', respond with: 'The learning "
            "objectives are:\n\n' followed by the full text from 'learningCanvas.content'. If no such response exists, say "
            "'I couldn’t find specific objectives, but here’s a starting point...' and provide a default like 'Understand key "
            "concepts and apply knowledge effectively.' For complex queries (over 50 words), urgent queries (contains 'urgent'), "
            "or requests for human help ('help' or 'complex issue'), respond with 'Contact support@university.edu'. For general "
            "academic queries (courses, schedules), delegate to SupportAgent by calling handoff_to_support(). For detailed "
            "learning/assessment queries beyond objectives, delegate to LearningAgent by calling handoff_to_learning()."
        )
        agents["TriageAgent"] = Agent(
            name="TriageAgent",
            instructions=triage_instructions,
            functions=[
                handoff_to_support,
                handoff_to_learning,
                search_courses,
                search_teaching_units
            ]
        )

        support_instructions = (
            "You are SupportAgent, handling general university support. Answer queries about courses, schedules, enrollments, "
            "and student info using SQLite tools. The learning objectives are in the message history from the "
            "'get_learning_objectives' tool response under 'learningCanvas.content'. For queries about 'learning objectives' "
            "or 'objectives', respond with: 'The learning objectives are:\n\n' followed by the full text from 'learningCanvas.content'. "
            "If no such response exists, say 'I couldn’t find specific objectives, but here’s a starting point...' and provide "
            "a default like 'Understand key concepts and apply knowledge effectively.' If data is unavailable, say 'I couldn’t "
            "access the latest info, but here’s some advice...'. For detailed learning/assessment queries, delegate to "
            "LearningAgent by calling handoff_to_learning(). For other queries requiring coordination, delegate to TriageAgent "
            "by calling handoff_to_triage()."
        )
        agents["SupportAgent"] = Agent(
            name="SupportAgent",
            instructions=support_instructions,
            functions=[
                handoff_to_triage,
                handoff_to_learning,
                search_courses,
                search_teaching_units,
                search_students,
                search_enrollments,
                search_assessment_items,
                comprehensive_search
            ]
        )

        learning_instructions = (
            "You are LearningAgent, specializing in learning objectives and assessments. The learning objectives are preloaded "
            "in the message history from the 'get_learning_objectives' tool response under 'learningCanvas.content'. For queries "
            "about 'learning objectives' or 'objectives', respond with: 'The learning objectives are:\n\n' followed by the full "
            "text from 'learningCanvas.content'. If no such response exists, say 'I couldn’t find specific objectives, but here’s "
            "a starting point...' and provide a default like 'Understand key concepts and apply knowledge effectively.' For other "
            "assessment-related queries, provide detailed support using available tools. For general academic queries (courses, "
            "schedules), delegate to SupportAgent by calling handoff_to_support(). For queries requiring coordination, delegate "
            "to TriageAgent by calling handoff_to_triage()."
        )
        agents["LearningAgent"] = Agent(
            name="LearningAgent",
            instructions=learning_instructions,
            functions=[
                handoff_to_triage,
                handoff_to_support,
                get_teaching_prompt,
                search_learning_objectives,
                search_topics,
                search_subtopics,
                extended_comprehensive_search
            ]
        )

        self.set_starting_agent(agents["TriageAgent"])
        logger.info("Agents created: TriageAgent, SupportAgent, LearningAgent")
        return agents

# Standalone tools
def get_teaching_prompt(channel_id: str) -> str:
    logger.debug(f"Fetching teaching prompt for channel_id: {channel_id}")
    if not channel_id or not isinstance(channel_id, str):
        logger.warning("Invalid channel_id provided, using default prompt")
        return "Provide foundational academic guidance."

    try:
        units = search_teaching_units(channel_id)
        if not units or not isinstance(units, list) or not units[0].get("teaching_prompt"):
            logger.debug(f"No valid teaching units found for channel_id: {channel_id}, using default")
            return "Provide foundational academic guidance."
        prompt = units[0]["teaching_prompt"]
        logger.debug(f"Teaching prompt retrieved: {prompt}")
        return prompt
    except Exception as e:
        logger.error(f"Failed to fetch teaching prompt for channel_id {channel_id}: {str(e)}", exc_info=True)
        return "Provide foundational academic guidance."

if __name__ == "__main__":
    UniversitySupportBlueprint.main()
