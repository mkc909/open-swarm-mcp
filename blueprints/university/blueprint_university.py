"""
University Support Blueprint

A multi-agent system providing university support using LLM-driven responses, SQLite-backed tools,
and Canvas metadata integration, with graceful failure for all operations.
"""

import os
import logging
import json
import re
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

        try:
            metadata = extract_canvas_metadata(messages)
            context_variables.update(metadata)
            logger.debug(f"Updated context with channel_id: {context_variables['channel_id']}")
        except Exception as e:
            logger.error(f"Failed to extract metadata: {str(e)}", exc_info=True)
            context_variables.setdefault("channel_id", "default")
            context_variables.setdefault("objectives", ["Understand key concepts."])

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
            "You are TriageAgent, the coordinator for university support. Analyze student queries and Canvas metadata "
            "(from messages). Use extract_canvas_metadata to get channel ID and learning objectives into context_variables. "
            "If the query is complex (over 50 words), urgent (contains 'urgent'), or needs human help ('help' or 'complex issue'), "
            "respond with 'Contact support@university.edu'. Otherwise, delegate to SupportAgent for general academic "
            "queries (courses, schedules) by calling handoff_to_support(), or to LearningAgent for learning/assessment "
            "queries (objectives, progress) by calling handoff_to_learning(). If data is missing, use a fallback like "
            "'I couldn’t find details, but here’s some guidance...'."
        )
        agents["TriageAgent"] = Agent(
            name="TriageAgent",
            instructions=triage_instructions,
            functions=[
                handoff_to_support,
                handoff_to_learning,
                extract_canvas_metadata,
                search_courses,
                search_teaching_units
            ]
        )

        support_instructions = (
            "You are SupportAgent, handling general university support. Answer queries about courses, schedules, "
            "enrollments, and student info using SQLite tools. If data is unavailable, say 'I couldn’t access the latest "
            "info, but here’s some advice...'. For learning or assessment queries, delegate back to TriageAgent by calling "
            "handoff_to_triage()."
        )
        agents["SupportAgent"] = Agent(
            name="SupportAgent",
            instructions=lambda context: (
                f"{support_instructions}\n"
                f"Teaching Prompt: {get_teaching_prompt(context.get('channel_id', 'default'))}"
            ),
            functions=[
                handoff_to_triage,
                search_courses,
                search_teaching_units,
                search_students,
                search_enrollments,
                search_assessment_items,
                comprehensive_search
            ]
        )

        learning_instructions = (
            "You are LearningAgent, specializing in learning objectives and assessments. Help with progress, goals, and "
            "assessment details using SQLite tools and context['objectives'] from extract_canvas_metadata. "
            "List the objectives from context['objectives'] directly in your response if available; if empty or missing, "
            "say 'I couldn’t find specific objectives, but here’s a starting point...' and provide defaults. "
            "For general academic queries, delegate back to TriageAgent by calling handoff_to_triage()."
        )
        agents["LearningAgent"] = Agent(
            name="LearningAgent",
            instructions=lambda context: (
                f"{learning_instructions}\n"
                f"Teaching Prompt: {get_teaching_prompt(context.get('channel_id', 'default'))}\n"
                f"Available Objectives: {', '.join(context.get('objectives', ['None']))}"
            ),
            functions=[
                handoff_to_triage,
                get_teaching_prompt,
                extract_learning_objectives,
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
def extract_canvas_metadata(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    logger.debug(f"Extracting Canvas metadata from messages: {json.dumps(messages, indent=2) if messages else 'None'}")
    default_metadata = {"channel_id": "default", "content": "", "objectives": ["Understand key concepts.", "Apply knowledge effectively."]}

    if not messages or not isinstance(messages, list) or not messages[-1]:
        logger.warning("No valid messages provided, returning default metadata")
        return default_metadata

    last_message = messages[-1]
    if not isinstance(last_message, dict):
        logger.warning("Last message is not a dictionary, returning default metadata")
        return default_metadata

    try:
        metadata = last_message.get("metadata", {})
        channel_id = metadata.get("channelInfo", {}).get("channelId", "default")
        content = metadata.get("canvas", {}).get("content", "")
        objectives = extract_learning_objectives(content) if content else default_metadata["objectives"]
        result = {"channel_id": channel_id, "content": content, "objectives": objectives}
        logger.debug(f"Extracted metadata: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        logger.error(f"Failed to extract Canvas metadata: {str(e)}", exc_info=True)
        return default_metadata

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

def extract_learning_objectives(content: str) -> List[str]:
    logger.debug(f"Extracting learning objectives from content: {content[:50] if content else 'None'}...")
    if not content or not isinstance(content, str):
        logger.warning("No valid content provided for objectives extraction, returning defaults")
        return ["Understand key concepts.", "Apply knowledge effectively."]

    objectives = []
    try:
        for line in content.split("\n"):
            if re.match(r"^\d+\.\s", line) or "learning objective" in line.lower():
                objectives.append(line.strip())
        if not objectives:
            logger.debug("No objectives found in content, using defaults")
            return ["Understand key concepts.", "Apply knowledge effectively."]
    except Exception as e:
        logger.error(f"Failed to extract objectives: {str(e)}", exc_info=True)
        return ["Understand key concepts.", "Apply knowledge effectively."]
    
    logger.debug(f"Extracted objectives: {objectives}")
    return objectives

if __name__ == "__main__":
    UniversitySupportBlueprint.main()
