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
    """
    Blueprint for university support with a professional agent team.

    Agents:
    - TriageAgent: Analyzes queries and delegates tasks, extracts Canvas metadata.
    - SupportAgent: Handles general academic support (courses, schedules).
    - LearningAgent: Manages learning objectives and assessments, integrates teaching prompts.
    
    All operations fail gracefully with defaults or fallback messages.
    """
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "University Support System",
            "description": "A multi-agent system for university support, using LLM-driven responses, SQLite tools, and Canvas metadata with graceful failure.",
            "required_mcp_servers": ["sqlite"],
            "cli_name": "uni",
            "env_vars": ["SQLITE_DB_PATH"]
        }

    def extract_learning_objectives(self, content: str) -> List[str]:
        """Extract learning objectives from Canvas content using regex, with graceful failure."""
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

    def get_teaching_prompt(self, channel_id: str) -> str:
        """Fetch teaching prompt for a channel ID from the SQLite database, with graceful failure."""
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

    def extract_canvas_metadata(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract Canvas metadata from messages, with graceful failure."""
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
            content = last_message.get("learning_resource_content", last_message.get("text", ""))
            objectives = self.extract_learning_objectives(content) if content else default_metadata["objectives"]
            result = {"channel_id": channel_id, "content": content, "objectives": objectives}
            logger.debug(f"Extracted metadata: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            logger.error(f"Failed to extract Canvas metadata: {str(e)}", exc_info=True)
            return default_metadata

    def create_agents(self) -> Dict[str, Agent]:
        """Create agents with dynamic instructions and tools for university support, ensuring graceful failure."""
        agents = {}

        # TriageAgent: Coordinator and metadata extractor
        triage_instructions = (
            "You are TriageAgent, the coordinator for university support. Analyze incoming student queries and metadata "
            "from Canvas (provided in messages). Use extract_canvas_metadata to get the channel ID and learning objectives, "
            "ensuring these are available in context for other agents. If the query is complex (over 50 words), urgent "
            "(contains 'urgent'), or requires human assistance (contains 'help' or 'complex issue'), respond with a message "
            "directing the student to 'support@university.edu'. Otherwise, delegate to SupportAgent for general academic "
            "queries (e.g., courses, schedules, enrollments) or LearningAgent for learning and assessment queries "
            "(e.g., objectives, progress). If tools fail or data is missing, provide a helpful fallback response like "
            "'I couldn’t find specific details, but here’s some general guidance...'. Use tools to gather context and "
            "provide clear, professional responses."
        )
        agents["TriageAgent"] = Agent(
            name="TriageAgent",
            instructions=triage_instructions,
            functions=[
                self.handoff_to_support,
                self.handoff_to_learning,
                self.extract_canvas_metadata,
                search_courses,
                search_teaching_units
            ]
        )

        # SupportAgent: General academic support
        support_instructions = (
            "You are SupportAgent, responsible for general university support. Answer queries about courses, schedules, "
            "enrollments, and student information. Use tools to fetch data from the SQLite database and provide clear, "
            "professional, and supportive responses. If data is unavailable, offer a fallback like 'I couldn’t access the "
            "latest course info, but here’s some general advice...'. If the query involves learning objectives or assessments, "
            "hand off to LearningAgent."
        )
        agents["SupportAgent"] = Agent(
            name="SupportAgent",
            instructions=lambda context: (
                f"{support_instructions}\n"
                f"Teaching Prompt: {self.get_teaching_prompt(context.get('channel_id', 'default'))}"
            ),
            functions=[
                self.handoff_to_learning,
                search_courses,
                search_teaching_units,
                search_students,
                search_enrollments,
                search_assessment_items,
                comprehensive_search
            ]
        )

        # LearningAgent: Learning and assessment support
        learning_instructions = (
            "You are LearningAgent, specializing in learning objectives and assessments. Assist students with their academic "
            "progress, learning goals, and assessment details. Use tools to fetch teaching prompts, objectives, and topics "
            "from the SQLite database, tailoring responses to their needs. If data is missing, provide a fallback like "
            "'I couldn’t find specific objectives, but here’s a general starting point...'. If the query is about general "
            "academic support, hand off to SupportAgent."
        )
        agents["LearningAgent"] = Agent(
            name="LearningAgent",
            instructions=lambda context: (
                f"{learning_instructions}\n"
                f"Teaching Prompt: {self.get_teaching_prompt(context.get('channel_id', 'default'))}\n"
                f"Canvas Learning Objectives: {', '.join(context.get('objectives', self.extract_learning_objectives('')))}"
            ),
            functions=[
                self.handoff_to_support,
                self.get_teaching_prompt,
                self.extract_learning_objectives,
                search_learning_objectives,
                search_topics,
                search_subtopics,
                extended_comprehensive_search
            ]
        )

        self.set_starting_agent(agents["TriageAgent"])
        logger.info("Agents created: TriageAgent, SupportAgent, LearningAgent")
        return agents

    def handoff_to_support(self, context_variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Delegate to SupportAgent with updated context, handling failures gracefully."""
        try:
            metadata = self.extract_canvas_metadata(self.swarm.messages)
        except Exception as e:
            logger.error(f"Failed to extract metadata during handoff: {str(e)}", exc_info=True)
            metadata = {"channel_id": "default", "content": "", "objectives": ["Understand key concepts."]}
        
        if context_variables is None:
            context_variables = {}
        context_variables.update(metadata)
        logger.debug(f"Handoff to SupportAgent with context: {json.dumps(context_variables, indent=2)}")
        return {"agent": self.swarm.agents["SupportAgent"], "context_variables": context_variables}

    def handoff_to_learning(self, context_variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Delegate to LearningAgent with updated context, handling failures gracefully."""
        try:
            metadata = self.extract_canvas_metadata(self.swarm.messages)
        except Exception as e:
            logger.error(f"Failed to extract metadata during handoff: {str(e)}", exc_info=True)
            metadata = {"channel_id": "default", "content": "", "objectives": ["Understand key concepts."]}
        
        if context_variables is None:
            context_variables = {}
        context_variables.update(metadata)
        logger.debug(f"Handoff to LearningAgent with context: {json.dumps(context_variables, indent=2)}")
        return {"agent": self.swarm.agents["LearningAgent"], "context_variables": context_variables}

if __name__ == "__main__":
    UniversitySupportBlueprint.main()