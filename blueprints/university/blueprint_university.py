import logging
import os
import importlib.util
import sqlite3
import json
from typing import Dict, Any, List, Optional
import re
import jmespath
from datetime import datetime

from swarm.types import Agent
from swarm.extensions.blueprint import BlueprintBase
import django
from django.apps import apps
from django.db import transaction

from blueprints.university.model_queries import (
    search_courses, search_students, search_teaching_units, search_topics,
    search_learning_objectives, search_subtopics, search_enrollments,
    search_assessment_items, extended_comprehensive_search, comprehensive_search
)

from blueprints.university.models import LearningObjective, Enrollment, TeachingUnit

# Configure logging with detailed debug information for troubleshooting
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class UniversitySupportBlueprint(BlueprintBase):
    """
    University Support System with multi-agent orchestration, integrating Django models,
    learning resource content from JSON input, and LLM functions for dynamic teaching prompts and responses.
    Designed to be frontend-agnostic, focusing on learning objectives from JSON data.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Define metadata for the University Support System blueprint, including title, description,
        required environment variables, and Django module mappings, with comprehensive logging.
        This metadata ensures the system is fully documented for maintenance, scalability,
        and compliance with university standards, providing a clear overview of system capabilities.
        """
        logger.debug("Accessing metadata property with a thorough and meticulous approach to ensure comprehensive tracking")
        metadata = {
            "title": "University Support System (Learning Resource and LLM Focus)",
            "description": "A carefully designed multi-agent system for university support, leveraging JSON-provided learning resource content and advanced LLM capabilities for dynamic, detailed responses, ensuring complete coverage of student needs across academic, support, and assessment domains, while maintaining strict adherence to university policies and frontend-agnostic design principles.",
            "required_mcp_servers": [],
            "cli_name": "uni",
            "env_vars": ["SQLITE_DB_PATH"],
            "django_modules": {
                "models": "blueprints.university.models",
                "views": "blueprints.university.views",
                "urls": "blueprints.university.urls",
                "serializers": "blueprints.university.serializers"
            },
            "url_prefix": "v1/university/"
        }
        logger.debug(f"Metadata retrieved with thorough precision, contents: {json.dumps(metadata, indent=4)}")
        return metadata

    def __init__(self, config: dict, **kwargs):
        """
        Initialize the blueprint with a detailed configuration process, updating with default LLM settings,
        creating agents, and ensuring robust logging for every step to facilitate debugging, auditing, and optimization.
        This initialization process is designed to handle edge cases with precision.
        """
        logger.debug(f"Initializing UniversitySupportBlueprint with config: {json.dumps(config, indent=4)}, performing a thorough validation and setup routine")
        if not isinstance(config, dict):
            logger.error("Config must be a dictionary, triggering a critical error with precise logging for root cause analysis")
            raise ValueError("Config must be a dictionary, ensuring strict type safety across the system")

        config.setdefault("llm", {"default": {"dummy": "value"}})
        logger.debug(f"Updated config with default LLM settings, ensuring comprehensive LLM integration: {json.dumps(config, indent=4)}")
        super().__init__(config=config, **kwargs)
        self._ensure_database_setup()
        logger.info("UniversitySupportBlueprint initialized successfully with a robust setup process")

    def _ensure_database_setup(self) -> None:
        """
        Ensure database migrations are created, applied, and sample data loaded with a meticulous process,
        logging every operation to provide a clear audit trail, handling failures with precise error reporting.
        This method guarantees data integrity and availability for all university operations with careful attention to detail.
        """
        logger.debug("Ensuring database setup with a thorough and precise approach to data management")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blueprints.university.settings")
        django.setup()
        from blueprints.university.models import Course

        course_count = Course.objects.count()
        logger.debug(f"Current course count retrieved with precise tracking: {course_count}")
        if course_count == 0:
            logger.info("No courses found, initiating a detailed sample data loading process with comprehensive logging")
            sample_data_path = os.path.join(os.path.dirname(__file__), "sample_data.sql")
            logger.debug(f"Sample data path identified with careful precision: {sample_data_path}")

            if os.path.isfile(sample_data_path):
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        logger.debug("Executing sample data SQL script with a detailed logging strategy")
                        cursor.connection.executescript(open(sample_data_path).read())
                    logger.info("Sample data loaded successfully with a thorough confirmation process")
                except Exception as e:
                    logger.error(f"Failed to load sample data with a precise error report: {str(e)}", exc_info=True)
                    raise
            else:
                logger.warning(f"Sample data file {sample_data_path} not found, logging this critical issue with careful granularity. Skipping data population with a fallback strategy.")
        else:
            logger.info("Courses already exist, skipping sample data loading with a detailed confirmation log")

    def get_teaching_prompt(self, channel_id: str) -> str:
        """
        Retrieve the teaching prompt for the teaching unit associated with the given channel ID, with a detailed
        logging process, ensuring every possible edge case is logged, validated, and handled with precision.
        This method integrates with Django models to fetch prompts, providing a solid foundation for agent instructions.
        """
        logger.debug(f"Retrieving teaching prompt for channel_id with a thorough approach: {channel_id}")
        if not isinstance(channel_id, str):
            logger.error(f"Invalid channel_id type detected with precise logging: {type(channel_id)}. Expected str, triggering a critical type safety failure")
            raise ValueError("channel_id must be a string, ensuring strict type enforcement across the system")
        if not channel_id:
            logger.warning("Empty channel_id provided, logging this critical issue with careful granularity and returning a fallback prompt")
            return "No teaching unit found for this channel, ensuring graceful degradation with detailed logging."

        from blueprints.university.models import TeachingUnit
        try:
            teaching_unit = TeachingUnit.objects.get(channel_id=channel_id)
            prompt = teaching_unit.teaching_prompt or "No specific teaching instructions available, logged with detailed precision for audit purposes."
            logger.debug(f"Teaching prompt retrieved with careful precision for channel_id '{channel_id}': {prompt}")
            return prompt
        except TeachingUnit.DoesNotExist:
            logger.warning(f"No teaching unit found for channel_id with detailed logging: {channel_id}, providing a fallback response")
            return "No teaching unit found for this channel, logged with careful granularity for troubleshooting."
        except Exception as e:
            logger.error(f"Error retrieving teaching prompt for channel_id with a detailed error report: '{channel_id}': {str(e)}", exc_info=True)
            raise

    def extract_channel_id_from_messages(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Extract the channel_id from the messages with a detailed process, using a hardcoded JMESPath
        (metadata.channelInfo.channelId) to parse JSON data, logging every step, validation, and potential failure
        with precision to ensure robust, frontend-agnostic identification, gracefully handling missing data.
        """
        logger.debug(f"Extracting channel_id from messages with a thorough approach: {messages}")
        if not isinstance(messages, list):
            logger.error(f"Invalid messages type detected with precise logging: {type(messages)}. Expected list, triggering a critical type safety failure")
            raise ValueError("Messages must be a list, ensuring strict type enforcement across the system")
        if not messages:
            logger.warning("Empty messages list provided for channel_id extraction, logging this critical issue with careful granularity and returning None")
            return None

        for msg in messages:
            logger.debug(f"Processing message with precise tracking: {json.dumps(msg, indent=4)}")
            if not isinstance(msg, dict):
                logger.warning(f"Skipping invalid message format with detailed logging: {msg}, ensuring graceful degradation")
                continue
            if "metadata" not in msg:
                logger.debug(f"No metadata found in message with meticulous logging: {msg}, attempting fallback")
                continue

            try:
                # Hardcode JMESPath for channelId extraction
                channel_id = jmespath.search("channelInfo.channelId", msg["metadata"])
                if channel_id:
                    logger.debug(f"Extracted channel_id with careful precision using hardcoded JMESPath: {channel_id}")
                    return channel_id
                logger.warning("No channelId found using JMESPath, logging this critical issue with careful granularity and attempting fallback")
            except Exception as e:
                logger.warning(f"Failed to parse metadata with JMESPath, logging detailed error with fallback strategy: {str(e)}")
                continue

            # Fallback: Check for channel or user ID in message
            if "channel" in msg and "id" in msg["channel"]:
                channel_id = msg["channel"]["id"]
                logger.debug(f"Extracted channel_id as fallback with precise tracking: {channel_id}")
                return channel_id
            elif "user" in msg and "id" in msg["user"]:
                user_id = msg["user"]["id"]
                logger.debug(f"Extracted user_id as fallback channel_id with meticulous logging: {user_id}")
                return user_id

        logger.warning("No channel_id or user_id found in messages with a detailed warning log, returning None for graceful degradation")
        return None

    def run_with_context(self, messages: List[Dict[str, str]], context_variables: dict) -> dict:
        """
        Override the run_with_context method to extract channel_id from messages, update context_variables,
        process learning resource content from JSON, and generate dynamic responses with LLM and Django DB lookups.
        Logs every operation with a detailed approach to ensure comprehensive auditing, handling errors
        with precision and maintaining frontend-agnostic design principles.
        """
        logger.debug(f"Running with context with a thorough logging strategy. Messages: {json.dumps(messages, indent=4)}, Context variables: {json.dumps(context_variables, indent=4)}")
        if not isinstance(messages, list):
            logger.error(f"Invalid messages type detected with precise logging: {type(messages)}. Expected list, triggering a critical type safety failure")
            raise ValueError("Messages must be a list, ensuring strict type enforcement across the system")
        if not isinstance(context_variables, dict):
            logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
            raise ValueError("context_variables must be a dictionary, ensuring strict type safety across the system")

        if "channel_id" not in context_variables:
            logger.debug("No channel_id in context_variables, initiating a detailed extraction process from messages")
            channel_id = self.extract_channel_id_from_messages(messages)
            if channel_id:
                context_variables["channel_id"] = channel_id
                logger.debug(f"Set context_variables['channel_id'] with precise tracking to '{channel_id}', ensuring robust context management")
            else:
                logger.warning("No channel_id found in messages, logging this critical issue with careful granularity and proceeding with a fallback strategy")

        # Process incoming JSON (assumed to be the last message)
        json_data = messages[-1] if messages else {}
        processed_data = self.process_json_input(json_data)

        # Load past interactions (simplified placeholder with detailed logging)
        past_interactions = self._load_past_interactions(context_variables.get("channel_id", "default_channel")) or []
        logger.debug(f"Past interactions loaded with meticulous precision: {json.dumps(past_interactions, indent=4)}")

        # Generate response with teaching prompts, learning resource content, and LLM enhancements
        response = self.generate_response(processed_data, past_interactions)

        # Update context with learning objectives and learning resource data
        objectives_data = self.check_learning_objectives(processed_data["student_info"], processed_data["learning_objectives"])
        context_variables.update({
            "learning_objectives": objectives_data["objectives_met"],
            "guidance": objectives_data["guidance"],
            "learning_resource_content": processed_data["learning_resource_content"]
        })
        logger.debug(f"Updated context_variables with thorough precision: {json.dumps(context_variables, indent=4)}")

        logger.debug(f"run_with_context result generated with careful precision: {json.dumps({'response': response, 'context_variables': context_variables}, indent=4)}")
        return {"response": response, "context_variables": context_variables}

    def _load_past_interactions(self, channel_id: str) -> List[Dict[str, Any]]:
        """Load past interactions for personalization with a detailed logging process, using a simplified placeholder to ensure robust tracking."""
        logger.debug(f"Loading past interactions for channel_id with a thorough approach: {channel_id}")
        try:
            # Placeholder: Store in gData Lake or SQLite with precise logging
            return [{"response": "Confirmed writing feedback", "timestamp": datetime.now().isoformat()}]
        except Exception as e:
            logger.error(f"Error loading past interactions with a detailed error report: {str(e)}", exc_info=True)
            return []

    def extract_learning_objectives(self, learning_resource_content: str) -> List[str]:
        """
        Extract learning objectives from learning resource content with a meticulous process,
        logging every operation, validation, and potential failure to ensure comprehensive auditing, using regex
        and HTML parsing to identify objectives from JSON-provided data, ensuring frontend-agnostic design.
        """
        logger.debug(f"Extracting learning objectives from learning resource content with a thorough approach: {learning_resource_content[:50]}...")
        if not isinstance(learning_resource_content, str):
            logger.error(f"Invalid learning_resource_content type detected with precise logging: {type(learning_resource_content)}. Expected str, triggering a critical type safety failure")
            raise ValueError("learning_resource_content must be a string, ensuring strict type enforcement across the system")

        objectives = []
        # Look for numbered lists or keywords like "Learning Objectives:" with careful precision
        for line in learning_resource_content.split("\n"):
            if re.match(r"^\d+\.\s", line) or "learning objective" in line.lower():
                objective = line.strip()
                objectives.append(objective)
                logger.debug(f"Found learning objective with meticulous logging: {objective}")
        if not objectives:
            logger.warning("No learning objectives found in learning resource content, logging this critical issue with careful granularity and using default objectives")
            objectives = ["Identify the basic components of a well-structured paragraph.",  # Default from your example
                         "Distinguish topic sentences, supporting details, and concluding sentences.",
                         "Organize ideas logically within a paragraph.",
                         "Use appropriate transitions to improve paragraph cohesion.",
                         "Revise and refine paragraphs for clarity and coherence."]
        logger.debug(f"Extracted learning objectives with precise tracking: {json.dumps(objectives, indent=4)}")
        return objectives

    def process_json_input(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process JSON data from any frontend interface with a detailed approach, extracting communication type,
        channel_id, and learning resource content, logging every operation, validation, and potential failure to ensure
        comprehensive auditing, ensuring frontend-agnostic design principles are strictly adhered to for maximum flexibility.
        """
        logger.debug(f"Processing JSON input with a thorough logging strategy: {json.dumps(json_data, indent=4)}")
        if not isinstance(json_data, dict):
            logger.error(f"Invalid JSON data type detected with precise logging: {type(json_data)}. Expected dict, triggering a critical type safety failure")
            raise ValueError("JSON data must be a dictionary, ensuring strict type enforcement across the system")

        # Extract communication type (DM, Channel, Thread, Summary) with careful precision
        communication_type = json_data.get("type", "channel")
        logger.debug(f"Identified communication type with meticulous logging: {communication_type}")

        # Extract channel_id or user_id for student context with hardcoded JMESPath
        channel_id = self.extract_channel_id_from_messages([json_data]) or "default_channel"
        logger.debug(f"Extracted channel_id with precise tracking: {channel_id}")

        # Extract learning resource content from JSON (assumed to be provided by the frontend)
        learning_resource_content = json_data.get("learning_resource_content", "")
        if not learning_resource_content:
            logger.warning("No learning resource content found in JSON, logging this critical issue with careful granularity and using default content")
            learning_resource_content = "<h1>Which path do you choose?</h1><p>Consider a scenario where a student must decide between traditional and innovative approaches....</p>"  # Default example

        learning_objectives = self.extract_learning_objectives(learning_resource_content)

        # Retrieve student info from gEducation Database (Django models) with detailed precision
        student_info = self._fetch_student_info(channel_id)
        logger.debug(f"Student info retrieved with meticulous precision: {json.dumps(student_info, indent=4)}")

        return {
            "communication_type": communication_type,
            "channel_id": channel_id,
            "student_info": student_info,
            "learning_resource_content": learning_resource_content,
            "learning_objectives": learning_objectives,
            "original_data": json_data
        }

    def _fetch_student_info(self, channel_id: str) -> Dict[str, Any]:
        """
        Fetch student information from gEducation Database (Django models) with a detailed process,
        logging every operation, validation, and potential failure to ensure comprehensive auditing and troubleshooting.
        """
        logger.debug(f"Fetching student info for channel_id with a thorough approach: {channel_id}")
        student_info = {}

        try:
            teaching_unit = TeachingUnit.objects.filter(channel_id=channel_id).first()
            if teaching_unit:
                enrollments = Enrollment.objects.filter(teaching_unit=teaching_unit)
                student = enrollments.first().student if enrollments.exists() else None
                if student:
                    student_info.update({
                        "geducation": {
                            "name": student.name,
                            "gpa": float(student.gpa),
                            "status": student.status,
                            "enrollments": list(enrollments.values("teaching_unit__name", "status"))
                        }
                    })
            logger.debug(f"Student info compiled with precise tracking: {json.dumps(student_info, indent=4)}")
        except Exception as e:
            logger.error(f"Error fetching from gEducation Database with a detailed error report: {str(e)}", exc_info=True)

        return student_info

    def triage_for_human_response(self, processed_data: Dict[str, Any]) -> bool:
        """
        Determine if a human response is needed based on complexity, sentiment, or learning resource content analysis,
        with a detailed logging process, ensuring every possible edge case is logged, validated, and handled
        with precision, maintaining frontend-agnostic design principles for maximum flexibility.
        """
        logger.debug(f"Triage for human response with a thorough logging strategy, data: {json.dumps(processed_data, indent=4)}")
        if not isinstance(processed_data, dict):
            logger.error(f"Invalid processed_data type detected with precise logging: {type(processed_data)}. Expected dict, triggering a critical type safety failure")
            raise ValueError("processed_data must be a dictionary, ensuring strict type enforcement across the system")

        # Example: If query is complex, negative sentiment, or exceeds a threshold, escalate to human with careful precision
        query = processed_data.get("original_data", {}).get("text", "")
        if len(query.split()) > 50 or "urgent" in query.lower() or "help" in query.lower() or "complex issue" in query.lower():
            logger.info("Triage determined human response needed with meticulous logging, escalating with detailed reasoning")
            return True
        logger.info("Triage determined AI response sufficient with careful precision, proceeding with agent processing")
        return False

    def check_learning_objectives(self, student_info: Dict[str, Any], learning_objectives: List[str]) -> Dict[str, Any]:
        """
        Check if a student has met learning objectives derived from learning resource content, trigger rewards,
        or provide guidance with a detailed process, logging every operation, validation, and potential
        failure to ensure comprehensive auditing, integrating Django models with precision for academic tracking.
        """
        logger.debug(f"Checking learning objectives with a thorough approach for student: {json.dumps(student_info, indent=4)}, objectives: {json.dumps(learning_objectives, indent=4)}")
        if not isinstance(student_info, dict) or not isinstance(learning_objectives, list):
            logger.error(f"Invalid types detected with precise logging: student_info={type(student_info)}, learning_objectives={type(learning_objectives)}, triggering a critical type safety failure")
            raise ValueError("student_info must be a dictionary, learning_objectives a list, ensuring strict type enforcement across the system")

        objectives_met = {}
        guidance = []

        try:
            enrollments = Enrollment.objects.filter(student__name=student_info["geducation"]["name"])
            for enrollment in enrollments:
                for objective_desc in learning_objectives:
                    # Check if this objective exists or matches in the database with careful precision
                    objective = LearningObjective.objects.filter(description__icontains=objective_desc).first()
                    if objective and objective.topic.teaching_unit == enrollment.teaching_unit:
                        met = self._is_objective_met(enrollment, objective)
                        objectives_met[objective.description] = met
                        if not met:
                            guidance.append(f"To meet '{objective.description}' with detailed precision, complete assessments for {enrollment.teaching_unit.name} with careful attention to academic progress.")

            if any(objectives_met.values()):
                self._trigger_reward(student_info["geducation"]["name"])
                logger.info("Learning objectives met; reward triggered with a thorough confirmation process")
            else:
                logger.info("Learning objectives not fully met; guidance provided with careful precision for academic support")
        except Exception as e:
            logger.error(f"Error checking learning objectives with a detailed error report: {str(e)}", exc_info=True)

        logger.debug(f"Learning objectives check results with precise tracking: {json.dumps({'objectives_met': objectives_met, 'guidance': guidance}, indent=4)}")
        return {"objectives_met": objectives_met, "guidance": guidance}

    def _is_objective_met(self, enrollment: Enrollment, objective: LearningObjective) -> bool:
        """
        Check if a learning objective is met with a detailed process, logging every operation
        and validation to ensure comprehensive auditing, using Django models for academic tracking with precision.
        """
        logger.debug(f"Checking if objective {objective.description} is met for enrollment with a thorough approach: {enrollment}")
        assessments = enrollment.assessments.all()
        met = any(assessment.status == "completed" for assessment in assessments)
        logger.debug(f"Objective met status determined with meticulous precision: {met}")
        return met

    def _trigger_reward(self, student_name: str) -> None:
        """
        Trigger a reward for meeting learning objectives with a detailed process, logging every
        operation, validation, and potential failure to ensure comprehensive auditing, using a placeholder
        for frontend notification with precision.
        """
        logger.debug(f"Triggering reward for student with a thorough approach: {student_name}")
        # Placeholder: Store in gData Lake or notify via frontend with precise logging
        logger.info(f"Reward triggered for {student_name} with detailed precision: +50 points, ensuring robust academic motivation")

    def personalize_response(self, response: str, student_info: Dict[str, Any], past_interactions: List[Dict[str, Any]]) -> str:
        """
        Personalize the response based on student info, learning resource content, and past interactions with a
        detailed process, logging every operation, validation, and potential failure to ensure comprehensive
        auditing, maintaining frontend-agnostic design principles for maximum flexibility and student engagement.
        """
        logger.debug(f"Personalizing response with a thorough logging strategy for student: {json.dumps(student_info, indent=4)}, past interactions: {json.dumps(past_interactions, indent=4)}")
        if not isinstance(response, str):
            logger.error(f"Invalid response type detected with precise logging: {type(response)}. Expected str, triggering a critical type safety failure")
            raise ValueError("response must be a string, ensuring strict type enforcement across the system")
        if not isinstance(student_info, dict) or not isinstance(past_interactions, list):
            logger.error(f"Invalid types detected with precise logging: student_info={type(student_info)}, past_interactions={type(past_interactions)}, triggering a critical type safety failure")
            raise ValueError("student_info must be a dictionary, past_interactions a list, ensuring strict type enforcement across the system")

        # Add student name and encouragement with careful precision
        personalized = f"Hi {student_info['geducation']['name']}, {response}, ensuring a detailed and personalized greeting for academic engagement"
        if student_info["geducation"]["gpa"] > 3.0:
            personalized += " Your strong GPA is well-documented—continue your exemplary academic performance with careful dedication!"
        elif student_info["geducation"]["gpa"] < 2.0:
            personalized += " Let's collaborate with detailed precision to elevate your academic performance—I'm here to provide thorough support!"

        # Adjust for confirmations and learning resource context with careful granularity
        if any("confirmed" in i.get("response", "") for i in past_interactions):
            personalized += " As previously confirmed with meticulous precision, here’s the updated academic guidance with detailed clarity..."
        if "learning_resource_content" in student_info:
            personalized += f"\n\nBased on our learning resource content, focus on these objectives with careful precision: {', '.join(student_info['learning_objectives'][:2])}."

        logger.debug(f"Personalized response generated with precise tracking: {personalized}")
        return personalized

    def generate_response(self, processed_data: Dict[str, Any], past_interactions: List[Dict[str, Any]]) -> str:
        """
        Generate a personalized response for the student using learning resource content, teaching prompts, and LLM functions,
        with a detailed process, logging every operation, validation, and potential failure to ensure comprehensive
        auditing, integrating Django DB lookups and frontend-agnostic design principles for maximum flexibility.
        """
        logger.debug(f"Generating response with a thorough logging strategy, data: {json.dumps(processed_data, indent=4)}, past interactions: {json.dumps(past_interactions, indent=4)}")
        if not isinstance(processed_data, dict) or not isinstance(past_interactions, list):
            logger.error(f"Invalid types detected with precise logging: processed_data={type(processed_data)}, past_interactions={type(past_interactions)}, triggering a critical type safety failure")
            raise ValueError("processed_data must be a dictionary, past_interactions a list, ensuring strict type enforcement across the system")

        student_info = processed_data["student_info"]
        learning_resource_content = processed_data["learning_resource_content"]
        learning_objectives = processed_data["learning_objectives"]
        channel_id = processed_data["channel_id"]

        if self.triage_for_human_response(processed_data):
            return "This query requires human assistance with detailed precision. Contact support@university for a thorough resolution process."

        if not processed_data["original_data"].get("text", "").strip():
            return "Could you please clarify your request with meticulous precision? I’m here to provide detailed assistance with writing, schedules, or academic resources, ensuring comprehensive support across all domains."

        # Fetch teaching prompt for dynamic LLM context with careful precision
        teaching_prompt = self.get_teaching_prompt(channel_id)

        # Check learning objectives and add guidance with careful granularity
        objectives_data = self.check_learning_objectives(student_info, learning_objectives)
        guidance = objectives_data["guidance"]
        response = f"I can assist with that! Based on your query '{processed_data['original_data']['text']}' and our learning resource content, here’s the guidance with a detailed approach:"
        if guidance:
            response += f"\n\nGuidance with careful precision: {', '.join(guidance)}, ensuring comprehensive academic support and tracking."
        else:
            response += "\n\nYou’re progressing admirably—continue your academic journey with meticulous dedication and careful precision!"

        # Enhance response with teaching prompt, learning resource content, and LLM functions with detailed clarity
        enhanced_response = f"{response}\n\n**Teaching Context with Careful Detail:** {teaching_prompt}, integrating learning resource content for maximum academic impact"
        final_response = self._enhance_with_llm(enhanced_response, processed_data, past_interactions)
        logger.debug(f"Final LLM-enhanced response generated with precise tracking: {final_response}")

        # Personalize the response with careful granularity
        return self.personalize_response(final_response, {**student_info, "learning_resource_content": learning_resource_content, "learning_objectives": learning_objectives}, past_interactions)

    def _enhance_with_llm(self, response: str, processed_data: Dict[str, Any], past_interactions: List[Dict[str, Any]]) -> str:
        """
        Enhance the response using LLM functions with a detailed process, integrating teaching prompts,
        learning resource content, and learning objectives, logging every operation, validation, and potential failure
        to ensure comprehensive auditing, maintaining frontend-agnostic design principles for maximum flexibility.
        """
        logger.debug(f"Enhancing response with LLM with a thorough logging strategy: {response}, data: {json.dumps(processed_data, indent=4)}, past interactions: {json.dumps(past_interactions, indent=4)}")
        if not isinstance(response, str) or not isinstance(processed_data, dict) or not isinstance(past_interactions, list):
            logger.error(f"Invalid types detected with precise logging: response={type(response)}, processed_data={type(processed_data)}, past_interactions={type(past_interactions)}, triggering a critical type safety failure")
            raise ValueError("response must be a string, processed_data a dictionary, past_interactions a list, ensuring strict type enforcement across the system")

        # Simulate LLM enhancement with careful precision (placeholder for actual LLM integration)
        user_query = processed_data["original_data"].get("text", "")
        context = (f"User Query with Careful Detail: {user_query}\n"
                   f"Learning Resource Content with Precise Tracking: {processed_data['learning_resource_content']}\n"
                   f"Teaching Prompt with Meticulous Logging: {self.get_teaching_prompt(processed_data['channel_id'])}\n"
                   f"Learning Objectives with Careful Tracking: {', '.join(processed_data['learning_objectives'])}")
        enhanced = f"{response}\n\n[LLM Enhanced with Careful Detail]: Based on the context, I recommend focusing on {processed_data['learning_objectives'][0]} with precise tracking to enhance your academic understanding and progress, ensuring comprehensive support across all university domains."
        logger.debug(f"LLM-enhanced response generated with detailed precision: {enhanced}")
        return enhanced

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create and register agents for the University Support System with a detailed process,
        distributing all functions across TriageAgent, GeneralSupportAgent, and LearningAssessmentAgent,
        appending teaching prompts and learning resource content based on channel_id, enhanced with LLM and
        Django DB lookups, logging every operation, validation, and potential failure to ensure comprehensive
        auditing, maintaining frontend-agnostic design principles and strict adherence to university standards.
        """
        logger.debug("Creating agents for University Support System with a thorough logging strategy")
        agents = {}

        # Extract channel_id from context_variables or tool_calls using hardcoded JMESPath
        def get_channel_id(context_variables: dict) -> str:
            """
            Extract channel_id from context variables or tool calls with a detailed process, using
            hardcoded JMESPath (metadata.channelInfo.channelId), logging every operation, validation, and potential
            failure with precision to ensure robust, frontend-agnostic identification, gracefully handling
            missing data with careful granularity.
            """
            logger.debug(f"Getting channel_id with a thorough approach from context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")

            channel_id = context_variables.get("channel_id", "")
            logger.debug(f"Initial channel_id from context_variables with meticulous logging: {channel_id}")
            if not channel_id:
                if "metadata" in context_variables:
                    try:
                        channel_id = jmespath.search("channelInfo.channelId", context_variables["metadata"])
                        if channel_id:
                            logger.debug(f"Extracted channel_id with careful precision using hardcoded JMESPath: {channel_id}")
                            return channel_id
                        logger.warning("No channelId found using JMESPath with detailed logging, attempting fallback")
                    except Exception as e:
                        logger.warning(f"Failed to parse metadata with JMESPath, logging detailed error with fallback strategy: {str(e)}")
                tool_calls = context_variables.get("tool_calls", [])
                logger.debug(f"Tool calls for channel_id extraction with meticulous logging: {json.dumps(tool_calls, indent=4)}")
                if tool_calls and isinstance(tool_calls, list):
                    for call in tool_calls:
                        logger.debug(f"Processing tool call with precise tracking: {json.dumps(call, indent=4)}")
                        if not isinstance(call, dict):
                            logger.warning(f"Skipping invalid tool call format with detailed logging: {call}, ensuring graceful degradation")
                            continue
                        if "content" not in call:
                            logger.warning(f"Skipping tool call without content with meticulous logging: {call}, ensuring robust fallback")
                            continue
                        if "channelInfo" not in call["content"]:
                            logger.debug(f"No channelInfo in tool call content with precise logging: {call['content']}, proceeding with fallback")
                            continue

                        try:
                            metadata = json.loads(call["content"])
                            logger.debug(f"Parsed metadata from tool call with careful precision: {json.dumps(metadata, indent=4)}")
                            if not isinstance(metadata, dict):
                                logger.warning(f"Skipping invalid metadata format with detailed logging: {metadata}, ensuring graceful degradation")
                                continue
                            channel_id = metadata.get("channelInfo", {}).get("channelId", "")
                            logger.debug(f"Extracted channel_id from tool call with meticulous logging: {channel_id}")
                            break
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse tool call content as JSON with detailed logging: {call['content']}. Error: {str(e)}, ensuring robust fallback")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing tool call with a detailed error report: {json.dumps(call, indent=4)}. Error: {str(e)}", exc_info=True)
                            continue

            logger.debug(f"Final channel_id determined with precise tracking: {channel_id}")
            return channel_id

        # Triage functions
        def triage_to_general_support() -> Agent:
            """
            Hand off to the GeneralSupportAgent with a detailed logging process, ensuring
            comprehensive tracking and auditing, maintaining frontend-agnostic design principles for maximum flexibility.
            """
            logger.debug("Triaging to GeneralSupportAgent with a thorough logging strategy")
            if "GeneralSupportAgent" not in agents:
                logger.error("GeneralSupportAgent not found with precise logging, triggering a critical failure for root cause analysis")
                raise ValueError("GeneralSupportAgent agent not found, ensuring strict agent integrity across the system")
            return agents["GeneralSupportAgent"]

        def triage_to_learning_assessment() -> Agent:
            """
            Hand off to the LearningAssessmentAgent with a detailed logging process, ensuring
            comprehensive tracking and auditing, maintaining frontend-agnostic design principles for maximum flexibility.
            """
            logger.debug("Triaging to LearningAssessmentAgent with a thorough logging strategy")
            if "LearningAssessmentAgent" not in agents:
                logger.error("LearningAssessmentAgent not found with precise logging, triggering a critical failure for root cause analysis")
                raise ValueError("LearningAssessmentAgent agent not found, ensuring strict agent integrity across the system")
            return agents["LearningAssessmentAgent"]

        # Distribute all functions across agents (even if not perfectly logical, for coverage)
        def general_support_search(context_variables: dict) -> List[Dict[str, Any]]:
            """Search courses, students, or assessments for general support, logged with thorough detail."""
            logger.debug(f"General support search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"General support search query with meticulous logging: {query}")
            try:
                results = comprehensive_search(query)
                logger.info(f"General support search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in general support search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def learning_assessment_search(context_variables: dict) -> Dict[str, List[Dict[str, Any]]]:
            """Search teaching units, topics, learning objectives, subtopics, and assessments for learning and assessment, logged with thorough detail."""
            logger.debug(f"Learning assessment search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Learning assessment search query with meticulous logging: {query}")
            try:
                results = extended_comprehensive_search(query)
                logger.info(f"Learning assessment search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in learning assessment search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def course_advisor_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search courses based on context variables for general or learning support, logged with thorough detail.
            This function ensures coverage for course-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Course advisor search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Course advisor search query with meticulous logging: {query}")
            try:
                results = search_courses(query)
                logger.info(f"Course search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in course advisor search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def scheduling_assistant_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search schedules (assessments) based on context variables for general or learning support, logged with thorough detail.
            This function ensures coverage for scheduling-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Scheduling assistant search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Scheduling assistant search query with meticulous logging: {query}")
            try:
                results = search_assessment_items(query)
                logger.info(f"Assessment search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in scheduling assistant search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def student_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search students based on context variables for general or learning support, logged with thorough detail.
            This function ensures coverage for student-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Student search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Student search query with meticulous logging: {query}")
            try:
                results = search_students(query)
                logger.debug(f"Student search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in student search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def teaching_unit_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search teaching units based on context variables for general or learning support, logged with thorough detail.
            This function ensures coverage for teaching unit-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Teaching unit search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Teaching unit search query with meticulous logging: {query}")
            try:
                results = search_teaching_units(query)
                logger.debug(f"Teaching unit search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in teaching unit search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def topic_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search topics based on context variables for general or learning support, logged with thorough detail.
            This function ensures coverage for topic-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Topic search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Topic search query with meticulous logging: {query}")
            try:
                results = search_topics(query)
                logger.debug(f"Topic search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in topic search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def learning_objective_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search learning objectives based on context variables for general or learning support, logged with thorough detail.
            This function ensures coverage for learning objective-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Learning objective search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Learning objective search query with meticulous logging: {query}")
            try:
                results = search_learning_objectives(query)
                logger.debug(f"Learning objective search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in learning objective search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def subtopic_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search subtopics based on context variables for general or learning support, logged with thorough detail.
            This function ensures coverage for subtopic-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Subtopic search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Subtopic search query with meticulous logging: {query}")
            try:
                results = search_subtopics(query)
                logger.debug(f"Subtopic search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in subtopic search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def enrollment_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search enrollments based on context variables for general or learning support, logged with thorough detail.
            This function ensures coverage for enrollment-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Enrollment search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Enrollment search query with meticulous logging: {query}")
            try:
                results = search_enrollments(query)
                logger.debug(f"Enrollment search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in enrollment search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def assessment_item_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search assessment items based on context variables for general or learning support, logged with thorough detail.
            This function ensures coverage for assessment-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Assessment item search with a detailed approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Assessment item search query with meticulous logging: {query}")
            try:
                results = search_assessment_items(query)
                logger.debug(f"Assessment item search results with careful precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in assessment item search with a detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        # Base instructions with dynamic teaching prompt appending from Django DB using channel_id
        def get_dynamic_instructions(base_instructions: str, context_variables: dict) -> str:
            """
            Append dynamic teaching prompt and learning resource content to base instructions based on channel_id,
            fetched from Django DB with a detailed process, logging every operation, validation, and potential
            failure to ensure comprehensive auditing, maintaining frontend-agnostic design principles and strict adherence
            to university standards.
            """
            logger.debug(f"Getting dynamic instructions with a thorough logging strategy, base_instructions: {base_instructions}, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(base_instructions, str):
                logger.error(f"Invalid base_instructions type detected with precise logging: {type(base_instructions)}. Expected str, triggering a critical type safety failure")
                raise ValueError("base_instructions must be a string, ensuring strict type enforcement across the system")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with precise logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")

            try:
                channel_id = get_channel_id(context_variables)
                logger.debug(f"Channel ID for dynamic instructions determined with careful precision: {channel_id}")
                teaching_prompt = self.get_teaching_prompt(channel_id)
                learning_resource_content = context_variables.get("learning_resource_content", "")
                learning_objectives = context_variables.get("learning_objectives", [])
                dynamic_instructions = (f"{base_instructions}\n\n"
                                      f"**Teaching Prompt for Interaction {channel_id} with Careful Detail:**\n{teaching_prompt}\n\n"
                                      f"**Learning Resource Content with Precise Tracking:**\n{learning_resource_content}\n\n"
                                      f"**Learning Objectives with Meticulous Tracking:**\n{', '.join(learning_objectives)}")
                logger.debug(f"Dynamic instructions generated with detailed precision: {dynamic_instructions}")
                return dynamic_instructions
            except Exception as e:
                logger.error(f"Error getting dynamic instructions with a detailed error report: {str(e)}", exc_info=True)
                raise

        # Agent definitions with detailed instructions
        triage_instructions = (
            "You are the Triage Agent, a meticulous and vigilant entity responsible for analyzing incoming JSON data from HTTPS POST requests "
            "with a thorough approach, determining with precision whether a human response is required based on the complexity, sentiment, "
            "length, tone, urgency, and academic relevance of the query, cross-referencing every nuance against the teaching prompts and learning objectives "
            "derived from the learning resource content provided in the JSON payload. Your primary function is to evaluate, with careful granularity, "
            "whether the query pertains to general academic support, learning and assessment needs, or requires human intervention, ensuring every possible "
            "edge case is logged, validated, and handled with precision. You must scrutinize the communication type—such as Direct Message (DM), "
            "Channel, Thread, or Summary—with a detailed analysis, logging each step to ensure comprehensive auditing and traceability. If the query "
            "exceeds 50 words, contains keywords like 'urgent,' 'help,' or 'complex issue,' or exhibits negative sentiment (e.g., frustration, confusion), "
            "you must escalate it to human support at support@university with a clear explanation of your reasoning, including word count, "
            "sentiment score, and contextual analysis based on the teaching prompt and learning objectives. If the AI response is deemed sufficient, you must "
            "hand off to either the GeneralSupportAgent or LearningAssessmentAgent with a detailed justification, ensuring transparency in your "
            "decision-making process by logging every step of your rationale, including the specific learning objectives and teaching prompt context. If the "
            "information provided is insufficient or ambiguous, you must request clarification with a precise prompt, specifying every missing "
            "piece of information, potential misinterpretations, and expected response format, ensuring the student receives thorough guidance. You must "
            "operate with frontend-agnostic design principles, avoiding any platform-specific references, and maintain strict adherence to university "
            "standards for academic support, logging every operation with precision to facilitate debugging, auditing, and optimization."
        )
        logger.debug(f"Triage agent instructions defined with meticulous precision: {triage_instructions}")
        triage_agent = Agent(
            name="TriageAgent",
            instructions=lambda context_variables: get_dynamic_instructions(triage_instructions, context_variables),
            functions=[triage_to_general_support, triage_to_learning_assessment, course_advisor_search, scheduling_assistant_search],
        )
        logger.debug("TriageAgent created with careful precision")

        general_support_instructions = (
            "You are the GeneralSupportAgent, a meticulous and detailed academic support entity responsible for handling a wide range of "
            "student queries with a thorough approach, covering general academic inquiries, course recommendations, scheduling assistance, student "
            "information, enrollment details, and campus resources, integrating teaching prompts and learning objectives from the learning resource content "
            "provided in the JSON payload with precision. Your role is to provide a detailed, personalized, and supportive response to every query, "
            "ensuring every nuance is addressed, logged, and audited with care, maintaining frontend-agnostic design principles and strict adherence to "
            "university standards. You must engage the student with precise questions to uncover their preferences, previous academic history, current "
            "enrollments, scheduling needs, and campus interests, cross-referencing every detail against the teaching prompts and learning objectives, "
            "logging each step for comprehensive tracking. You must offer clear, concise, yet detailed recommendations, including course descriptions, "
            "prerequisites, scheduling details, enrollment statuses, student profiles, and campus resource availability, integrating learning objectives to "
            "ensure academic alignment, with every operation logged for auditing and optimization. If a query requires learning or assessment-specific "
            "support, hand off to the LearningAssessmentAgent with a detailed justification, logged with precision. You must maintain a professional, "
            "supportive tone, ensuring every response is tailored to the student’s context, past interactions, GPA, enrollment status, and learning "
            "objectives, logging every personalization step for transparency and auditability."
        )
        logger.debug(f"GeneralSupportAgent instructions defined with meticulous precision: {general_support_instructions}")
        general_support_agent = Agent(
            name="GeneralSupportAgent",
            instructions=lambda context_variables: get_dynamic_instructions(general_support_instructions, context_variables),
            functions=[
                general_support_search, 
                course_advisor_search, scheduling_assistant_search, student_search, teaching_unit_search,
                topic_search, enrollment_search, assessment_item_search, comprehensive_search
            ],
        )
        logger.debug("GeneralSupportAgent created with careful precision")

        learning_assessment_instructions = (
            "You are the LearningAssessmentAgent, a meticulous and detailed academic entity responsible for handling inquiries related to "
            "learning objectives, assessments, teaching units, topics, subtopics, and student progress tracking with a thorough approach, integrating "
            "teaching prompts and learning objectives from the learning resource content provided in the JSON payload with precision. Your role is to "
            "provide a detailed, personalized, and supportive response to every query, ensuring every nuance is addressed, logged, and audited with care, "
            "maintaining frontend-agnostic design principles and strict adherence to university standards. You must analyze student progress against "
            "learning objectives, trigger rewards for achievement, offer guidance on next steps, and track assessment completion with precise metrics, "
            "logging each operation for comprehensive auditing. You must engage the student with detailed questions to uncover their academic progress, "
            "assessment status, learning needs, and teaching unit affiliations, cross-referencing every detail against the teaching prompts and learning "
            "objectives, logging each step for thorough tracking. You must offer clear, concise, yet detailed recommendations, including learning objective "
            "descriptions, assessment titles, due dates, statuses, weights, teaching unit details, topic breakdowns, and subtopic specifics, integrating "
            "learning objectives to ensure academic alignment, with every operation logged for auditing and optimization. If a query requires general "
            "academic support, hand off to the GeneralSupportAgent with a detailed justification, logged with precision. You must maintain a professional, "
            "supportive tone, ensuring every response is tailored to the student’s context, past interactions, GPA, enrollment status, and learning "
            "objectives, logging every personalization step for transparency and auditability."
        )
        logger.debug(f"LearningAssessmentAgent instructions defined with meticulous precision: {learning_assessment_instructions}")
        learning_assessment_agent = Agent(
            name="LearningAssessmentAgent",
            instructions=lambda context_variables: get_dynamic_instructions(learning_assessment_instructions, context_variables),
            functions=[
                learning_assessment_search, 
                course_advisor_search, scheduling_assistant_search, student_search, teaching_unit_search,
                topic_search, learning_objective_search, subtopic_search, enrollment_search, assessment_item_search,
                extended_comprehensive_search
            ],
        )
        logger.debug("LearningAssessmentAgent created with careful precision")

        # Register agents
        agents["TriageAgent"] = triage_agent
        agents["GeneralSupportAgent"] = general_support_agent
        agents["LearningAssessmentAgent"] = learning_assessment_agent
        logger.debug(f"Registered agents with meticulous precision: {json.dumps(list(agents.keys()), indent=4)}")

        logger.info("University Support agents created with thorough coverage, enhanced with LLM, Django DB lookups, and learning resource content")
        self.set_starting_agent(triage_agent)
        logger.debug("Starting agent set to TriageAgent with careful precision")
        return agents

if __name__ == "__main__":
    logger.debug("Running UniversitySupportBlueprint.main() with a thorough logging strategy")
    UniversitySupportBlueprint.main()
    logger.info("UniversitySupportBlueprint.main() executed successfully with meticulous precision")