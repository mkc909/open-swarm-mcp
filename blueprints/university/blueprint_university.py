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
from django.db.models import Q

from blueprints.university.models import LearningObjective, Enrollment, TeachingUnit, Topic, Subtopic, Course, Student, AssessmentItem

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
    Frontend-agnostic, focusing on learning objectives from JSON data.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Define metadata for the University Support System blueprint, including title, description,
        required environment variables, and Django module mappings, with absurdly detailed logging.
        This metadata ensures the system is fully documented for future maintenance, scalability,
        and compliance with university standards, providing a comprehensive overview of system capabilities.
        """
        logger.debug("Accessing metadata property with an extraordinarily verbose and meticulous approach to ensure comprehensive tracking")
        metadata = {
            "title": "University Support System (Learning Resource and LLM Focus)",
            "description": "An intricately designed multi-agent system for university support, leveraging JSON-provided learning resource content and advanced LLM capabilities for dynamic, highly detailed responses, ensuring complete coverage of student needs across academic, support, and assessment domains, while maintaining strict adherence to university policies and frontend-agnostic design principles.",
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
        logger.debug(f"Metadata retrieved with exhaustive precision, contents: {json.dumps(metadata, indent=4)}")
        return metadata

    def __init__(self, config: dict, **kwargs):
        """
        Initialize the blueprint with an excessively detailed configuration process, updating with default LLM settings,
        creating agents, and ensuring robust logging for every step to facilitate debugging, auditing, and optimization.
        This initialization process is designed to be foolproof, handling edge cases with unparalleled thoroughness.
        """
        logger.debug(f"Initializing UniversitySupportBlueprint with config: {json.dumps(config, indent=4)}, performing an exhaustive validation and setup routine")
        if not isinstance(config, dict):
            logger.error("Config must be a dictionary, triggering a critical error with meticulous logging for root cause analysis")
            raise ValueError("Config must be a dictionary, ensuring strict type safety across the system")

        config.setdefault("llm", {"default": {"dummy": "value"}})
        logger.debug(f"Updated config with default LLM settings, ensuring comprehensive LLM integration: {json.dumps(config, indent=4)}")
        super().__init__(config=config, **kwargs)
        self._ensure_database_setup()
        logger.info("UniversitySupportBlueprint initialized successfully with an absurdly detailed and robust setup process")

    def _ensure_database_setup(self) -> None:
        """
        Ensure database migrations are created, applied, and sample data loaded with an excessively meticulous process,
        logging every operation to provide an exhaustive audit trail, handling failures with granular error reporting.
        This method guarantees data integrity and availability for all university operations with obsessive attention to detail.
        """
        logger.debug("Ensuring database setup with an extraordinarily thorough and pedantic approach to data management")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blueprints.university.settings")
        django.setup()
        from blueprints.university.models import Course

        course_count = Course.objects.count()
        logger.debug(f"Current course count retrieved with meticulous precision: {course_count}")
        if course_count == 0:
            logger.info("No courses found, initiating an overly detailed sample data loading process with exhaustive logging")
            sample_data_path = os.path.join(os.path.dirname(__file__), "sample_data.sql")
            logger.debug(f"Sample data path identified with excruciating precision: {sample_data_path}")

            if os.path.isfile(sample_data_path):
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        logger.debug("Executing sample data SQL script with an absurdly verbose logging strategy")
                        cursor.connection.executescript(open(sample_data_path).read())
                    logger.info("Sample data loaded successfully with an exhaustive confirmation process")
                except Exception as e:
                    logger.error(f"Failed to load sample data with a highly detailed error report: {str(e)}", exc_info=True)
                    raise
            else:
                logger.warning(f"Sample data file {sample_data_path} not found, logging this critical issue with extreme granularity. Skipping data population with a fallback strategy.")
        else:
            logger.info("Courses already exist, skipping sample data loading with a detailed confirmation log")

    def get_teaching_prompt(self, channel_id: str) -> str:
        """
        Retrieve the teaching prompt for the teaching unit associated with the given channel ID, with an absurdly detailed
        logging process, ensuring every possible edge case is logged, validated, and handled with excessive precision.
        This method integrates with Django models to fetch prompts, providing a robust foundation for agent instructions.
        """
        logger.debug(f"Retrieving teaching prompt for channel_id with an excessively verbose approach: {channel_id}")
        if not isinstance(channel_id, str):
            logger.error(f"Invalid channel_id type detected with meticulous logging: {type(channel_id)}. Expected str, triggering a critical type safety failure")
            raise ValueError("channel_id must be a string, ensuring strict type enforcement across the system")
        if not channel_id:
            logger.warning("Empty channel_id provided, logging this critical issue with extreme granularity and returning a fallback prompt")
            return "No teaching unit found for this channel, ensuring graceful degradation with detailed logging."

        from blueprints.university.models import TeachingUnit
        try:
            teaching_unit = TeachingUnit.objects.get(channel_id=channel_id)
            prompt = teaching_unit.teaching_prompt or "No specific teaching instructions available, logged with exhaustive detail for audit purposes."
            logger.debug(f"Teaching prompt retrieved with obsessive precision for channel_id '{channel_id}': {prompt}")
            return prompt
        except TeachingUnit.DoesNotExist:
            logger.warning(f"No teaching unit found for channel_id with detailed logging: {channel_id}, providing a fallback response")
            return "No teaching unit found for this channel, logged with extreme granularity for troubleshooting."
        except Exception as e:
            logger.error(f"Error retrieving teaching prompt for channel_id with an absurdly detailed error report: '{channel_id}': {str(e)}", exc_info=True)
            raise

    def search_courses(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Course model with an excessively meticulous search process, logging every detail of the query,
        result set, and potential failures to ensure comprehensive tracking and auditing, using Django ORM for precision.
        """
        logger.debug(f"Searching courses with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for course search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Course.objects.filter(
                Q(name__icontains=query) | Q(code__icontains=query) | Q(coordinator__icontains=query)
            )
            results = list(qs.values("code", "name", "coordinator"))
            logger.debug(f"Course search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching courses with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_students(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Student model with an excessively detailed search process, logging every operation,
        edge case, and potential failure to ensure comprehensive auditing and troubleshooting, using Django ORM.
        """
        logger.debug(f"Searching students with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for student search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Student.objects.filter(Q(name__icontains=query))
            results = list(qs.values("name", "gpa", "status"))
            logger.debug(f"Student search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching students with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_teaching_units(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the TeachingUnit model with an excessively meticulous search process, logging every operation,
        validation, and potential failure to ensure exhaustive auditing, using Django ORM for precision.
        """
        logger.debug(f"Searching teaching units with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for teaching unit search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = TeachingUnit.objects.filter(Q(code__icontains=query) | Q(name__icontains=query))
            results = list(qs.values("code", "name", "channel_id"))
            logger.debug(f"Teaching unit search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching teaching units with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_topics(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Topic model with an excessively detailed search process, logging every operation,
        edge case, and potential failure to ensure comprehensive auditing, using Django ORM.
        """
        logger.debug(f"Searching topics with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for topic search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Topic.objects.filter(Q(name__icontains=query))
            results = list(qs.values("name"))
            logger.debug(f"Topic search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching topics with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_learning_objectives(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the LearningObjective model with an excessively meticulous search process, logging every operation,
        validation, and potential failure to ensure exhaustive auditing, using Django ORM.
        """
        logger.debug(f"Searching learning objectives with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for learning objective search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = LearningObjective.objects.filter(Q(description__icontains=query))
            results = list(qs.values("description"))
            logger.debug(f"Learning objective search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching learning objectives with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_subtopics(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Subtopic model with an excessively detailed search process, logging every operation,
        edge case, and potential failure to ensure comprehensive auditing, using Django ORM.
        """
        logger.debug(f"Searching subtopics with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for subtopic search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Subtopic.objects.filter(Q(name__icontains=query))
            results = list(qs.values("name"))
            logger.debug(f"Subtopic search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching subtopics with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_enrollments(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Enrollment model with an excessively meticulous search process, logging every operation,
        validation, and potential failure to ensure exhaustive auditing, using Django ORM.
        """
        logger.debug(f"Searching enrollments with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for enrollment search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Enrollment.objects.filter(Q(status__icontains=query))
            results = list(qs.values("status", "enrollment_date"))
            logger.debug(f"Enrollment search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching enrollments with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_assessment_items(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the AssessmentItem model with an excessively detailed search process, logging every operation,
        edge case, and potential failure to ensure comprehensive auditing, using Django ORM.
        """
        logger.debug(f"Searching assessment items with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for assessment item search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = AssessmentItem.objects.filter(Q(title__icontains=query))
            results = list(qs.values("title", "status", "due_date"))
            logger.debug(f"Assessment item search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching assessment items with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def extended_comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform an extended comprehensive search across all university models with an absurdly detailed process,
        logging every query, result, and potential failure to ensure exhaustive auditing and troubleshooting,
        using Django ORM for precision and reliability.
        """
        logger.debug(f"Performing extended comprehensive search with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for extended comprehensive search, logging this critical issue with extreme granularity and returning an empty result set")
            return {
                "courses": [],
                "students": [],
                "teaching_units": [],
                "topics": [],
                "learning_objectives": [],
                "subtopics": [],
                "enrollments": [],
                "assessment_items": [],
            }

        try:
            results = {
                "courses": self.search_courses(query),
                "students": self.search_students(query),
                "teaching_units": self.search_teaching_units(query),
                "topics": self.search_topics(query),
                "learning_objectives": self.search_learning_objectives(query),
                "subtopics": self.search_subtopics(query),
                "enrollments": self.search_enrollments(query),
                "assessment_items": self.search_assessment_items(query),
            }
            logger.debug(f"Extended comprehensive search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error performing extended comprehensive search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform a comprehensive search across courses and students with an excessively meticulous process,
        logging every operation, validation, and potential failure to ensure exhaustive auditing, using Django ORM.
        """
        logger.debug(f"Performing comprehensive search with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for comprehensive search, logging this critical issue with extreme granularity and returning an empty result set")
            return {"courses": [], "students": []}

        try:
            results = {
                "courses": self.search_courses(query),
                "students": self.search_students(query)
            }
            logger.debug(f"Comprehensive search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error performing comprehensive search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def extract_channel_id_from_messages(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Extract the channel_id from the messages with an absurdly detailed process, using a hardcoded JMESPath
        (metadata.channelInfo.channelId) to parse JSON data, logging every step, validation, and potential failure
        with extreme granularity to ensure robust, frontend-agnostic identification, gracefully handling missing data.
        """
        logger.debug(f"Extracting channel_id from messages with an extraordinarily verbose approach: {messages}")
        if not isinstance(messages, list):
            logger.error(f"Invalid messages type detected with exhaustive logging: {type(messages)}. Expected list, triggering a critical type safety failure")
            raise ValueError("Messages must be a list, ensuring strict type enforcement across the system")
        if not messages:
            logger.warning("Empty messages list provided for channel_id extraction, logging this critical issue with extreme granularity and returning None")
            return None

        for msg in messages:
            logger.debug(f"Processing message with obsessive precision: {json.dumps(msg, indent=4)}")
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
                    logger.debug(f"Extracted channel_id with exhaustive precision using hardcoded JMESPath: {channel_id}")
                    return channel_id
                logger.warning("No channelId found using JMESPath, logging this critical issue with extreme granularity and attempting fallback")
            except Exception as e:
                logger.warning(f"Failed to parse metadata with JMESPath, logging detailed error with fallback strategy: {str(e)}")
                continue

            # Fallback: Check for channel or user ID in message
            if "channel" in msg and "id" in msg["channel"]:
                channel_id = msg["channel"]["id"]
                logger.debug(f"Extracted channel_id as fallback with obsessive precision: {channel_id}")
                return channel_id
            elif "user" in msg and "id" in msg["user"]:
                user_id = msg["user"]["id"]
                logger.debug(f"Extracted user_id as fallback channel_id with meticulous logging: {user_id}")
                return user_id

        logger.warning("No channel_id or user_id found in messages with an absurdly detailed warning log, returning None for graceful degradation")
        return None

    def run_with_context(self, messages: List[Dict[str, str]], context_variables: dict) -> dict:
        """
        Override the run_with_context method to extract channel_id from messages, update context_variables,
        process learning resource content from JSON, and generate dynamic responses with LLM and Django DB lookups.
        Logs every operation with an absurdly detailed approach to ensure comprehensive auditing, handling errors
        with extreme granularity and maintaining frontend-agnostic design principles.
        """
        logger.debug(f"Running with context with an extraordinarily verbose logging strategy. Messages: {json.dumps(messages, indent=4)}, Context variables: {json.dumps(context_variables, indent=4)}")
        if not isinstance(messages, list):
            logger.error(f"Invalid messages type detected with exhaustive logging: {type(messages)}. Expected list, triggering a critical type safety failure")
            raise ValueError("Messages must be a list, ensuring strict type enforcement across the system")
        if not isinstance(context_variables, dict):
            logger.error(f"Invalid context_variables type detected with exhaustive logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
            raise ValueError("context_variables must be a dictionary, ensuring strict type safety across the system")

        if "channel_id" not in context_variables:
            logger.debug("No channel_id in context_variables, initiating an excessively detailed extraction process from messages")
            channel_id = self.extract_channel_id_from_messages(messages)
            if channel_id:
                context_variables["channel_id"] = channel_id
                logger.debug(f"Set context_variables['channel_id'] with obsessive precision to '{channel_id}', ensuring robust context management")
            else:
                logger.warning("No channel_id found in messages, logging this critical issue with extreme granularity and proceeding with a fallback strategy")

        # Process incoming JSON (assumed to be the last message)
        json_data = messages[-1] if messages else {}
        processed_data = self.process_json_input(json_data)

        # Load past interactions (simplified placeholder with absurdly detailed logging)
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
        logger.debug(f"Updated context_variables with absurdly detailed precision: {json.dumps(context_variables, indent=4)}")

        logger.debug(f"run_with_context result generated with exhaustive precision: {json.dumps({'response': response, 'context_variables': context_variables}, indent=4)}")
        return {"response": response, "context_variables": context_variables}

    def _load_past_interactions(self, channel_id: str) -> List[Dict[str, Any]]:
        """Load past interactions for personalization with an absurdly detailed logging process, using a simplified placeholder to ensure robust tracking."""
        logger.debug(f"Loading past interactions for channel_id with an extraordinarily verbose approach: {channel_id}")
        try:
            # Placeholder: Store in gData Lake or SQLite with obsessive logging
            return [{"response": "Confirmed writing feedback", "timestamp": datetime.now().isoformat()}]
        except Exception as e:
            logger.error(f"Error loading past interactions with an absurdly detailed error report: {str(e)}", exc_info=True)
            return []

    def extract_learning_objectives(self, learning_resource_content: str) -> List[str]:
        """
        Extract learning objectives from learning resource content with an excessively meticulous process,
        logging every operation, validation, and potential failure to ensure comprehensive auditing, using regex
        and HTML parsing to identify objectives from JSON-provided data, ensuring frontend-agnostic design.
        """
        logger.debug(f"Extracting learning objectives from learning resource content with an absurdly verbose approach: {learning_resource_content[:50]}...")
        if not isinstance(learning_resource_content, str):
            logger.error(f"Invalid learning_resource_content type detected with exhaustive logging: {type(learning_resource_content)}. Expected str, triggering a critical type safety failure")
            raise ValueError("learning_resource_content must be a string, ensuring strict type enforcement across the system")

        objectives = []
        # Look for numbered lists or keywords like "Learning Objectives:" with obsessive precision
        for line in learning_resource_content.split("\n"):
            if re.match(r"^\d+\.\s", line) or "learning objective" in line.lower():
                objective = line.strip()
                objectives.append(objective)
                logger.debug(f"Found learning objective with meticulous logging: {objective}")
        if not objectives:
            logger.warning("No learning objectives found in learning resource content, logging this critical issue with extreme granularity and using default objectives")
            objectives = ["Identify the basic components of a well-structured paragraph.",  # Default from your example
                         "Distinguish topic sentences, supporting details, and concluding sentences.",
                         "Organize ideas logically within a paragraph.",
                         "Use appropriate transitions to improve paragraph cohesion.",
                         "Revise and refine paragraphs for clarity and coherence."]
        logger.debug(f"Extracted learning objectives with obsessive precision: {json.dumps(objectives, indent=4)}")
        return objectives

    def process_json_input(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process JSON data from any frontend interface with an absurdly detailed approach, extracting communication type,
        channel_id, and learning resource content, logging every operation, validation, and potential failure to ensure
        exhaustive auditing, ensuring frontend-agnostic design principles are strictly adhered to for maximum flexibility.
        """
        logger.debug(f"Processing JSON input with an extraordinarily verbose logging strategy: {json.dumps(json_data, indent=4)}")
        if not isinstance(json_data, dict):
            logger.error(f"Invalid JSON data type detected with exhaustive logging: {type(json_data)}. Expected dict, triggering a critical type safety failure")
            raise ValueError("JSON data must be a dictionary, ensuring strict type enforcement across the system")

        # Extract communication type (DM, Channel, Thread, Summary) with obsessive precision
        communication_type = json_data.get("type", "channel")
        logger.debug(f"Identified communication type with meticulous logging: {communication_type}")

        # Extract channel_id or user_id for student context with hardcoded JMESPath
        channel_id = self.extract_channel_id_from_messages([json_data]) or "default_channel"
        logger.debug(f"Extracted channel_id with obsessive precision: {channel_id}")

        # Extract learning resource content from JSON (assumed to be provided by the frontend)
        learning_resource_content = json_data.get("learning_resource_content", "")
        if not learning_resource_content:
            logger.warning("No learning resource content found in JSON, logging this critical issue with extreme granularity and using default content")
            learning_resource_content = "<h1>Which path do you choose?</h1><p>Consider a scenario where a student must decide between traditional and innovative approaches....</p>"  # Default example

        learning_objectives = self.extract_learning_objectives(learning_resource_content)

        # Retrieve student info from gEducation Database (Django models) with excessive detail
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
        Fetch student information from gEducation Database (Django models) with an absurdly detailed process,
        logging every operation, validation, and potential failure to ensure comprehensive auditing and troubleshooting.
        """
        logger.debug(f"Fetching student info for channel_id with an extraordinarily verbose approach: {channel_id}")
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
            logger.debug(f"Student info compiled with obsessive precision: {json.dumps(student_info, indent=4)}")
        except Exception as e:
            logger.error(f"Error fetching from gEducation Database with an absurdly detailed error report: {str(e)}", exc_info=True)

        return student_info

    def triage_for_human_response(self, processed_data: Dict[str, Any]) -> bool:
        """
        Determine if a human response is needed based on complexity, sentiment, or learning resource content analysis,
        with an absurdly detailed logging process, ensuring every possible edge case is logged, validated, and handled
        with extreme precision, maintaining frontend-agnostic design principles for maximum flexibility.
        """
        logger.debug(f"Triage for human response with an extraordinarily verbose logging strategy, data: {json.dumps(processed_data, indent=4)}")
        if not isinstance(processed_data, dict):
            logger.error(f"Invalid processed_data type detected with exhaustive logging: {type(processed_data)}. Expected dict, triggering a critical type safety failure")
            raise ValueError("processed_data must be a dictionary, ensuring strict type enforcement across the system")

        # Example: If query is complex, negative sentiment, or exceeds a verbose threshold, escalate to human with obsessive precision
        query = processed_data.get("original_data", {}).get("text", "")
        if len(query.split()) > 50 or "urgent" in query.lower() or "help" in query.lower() or "complex issue" in query.lower():
            logger.info("Triage determined human response needed with meticulous logging, escalating with detailed reasoning")
            return True
        logger.info("Triage determined AI response sufficient with exhaustive precision, proceeding with agent processing")
        return False

    def check_learning_objectives(self, student_info: Dict[str, Any], learning_objectives: List[str]) -> Dict[str, Any]:
        """
        Check if a student has met learning objectives derived from learning resource content, trigger rewards,
        or provide guidance with an absurdly detailed process, logging every operation, validation, and potential
        failure to ensure comprehensive auditing, integrating Django models with extreme precision for academic tracking.
        """
        logger.debug(f"Checking learning objectives with an extraordinarily verbose approach for student: {json.dumps(student_info, indent=4)}, objectives: {json.dumps(learning_objectives, indent=4)}")
        if not isinstance(student_info, dict) or not isinstance(learning_objectives, list):
            logger.error(f"Invalid types detected with exhaustive logging: student_info={type(student_info)}, learning_objectives={type(learning_objectives)}, triggering a critical type safety failure")
            raise ValueError("student_info must be a dictionary, learning_objectives a list, ensuring strict type enforcement across the system")

        objectives_met = {}
        guidance = []

        try:
            enrollments = Enrollment.objects.filter(student__name=student_info["geducation"]["name"])
            for enrollment in enrollments:
                for objective_desc in learning_objectives:
                    # Check if this objective exists or matches in the database with obsessive precision
                    objective = LearningObjective.objects.filter(description__icontains=objective_desc).first()
                    if objective and objective.topic.teaching_unit == enrollment.teaching_unit:
                        met = self._is_objective_met(enrollment, objective)
                        objectives_met[objective.description] = met
                        if not met:
                            guidance.append(f"To meet '{objective.description}' with exhaustive detail, complete assessments for {enrollment.teaching_unit.name} with meticulous attention to academic progress.")

            if any(objectives_met.values()):
                self._trigger_reward(student_info["geducation"]["name"])
                logger.info("Learning objectives met; reward triggered with an absurdly detailed confirmation process")
            else:
                logger.info("Learning objectives not fully met; guidance provided with exhaustive precision for academic support")
        except Exception as e:
            logger.error(f"Error checking learning objectives with an absurdly detailed error report: {str(e)}", exc_info=True)

        logger.debug(f"Learning objectives check results with obsessive precision: {json.dumps({'objectives_met': objectives_met, 'guidance': guidance}, indent=4)}")
        return {"objectives_met": objectives_met, "guidance": guidance}

    def _is_objective_met(self, enrollment: Enrollment, objective: LearningObjective) -> bool:
        """
        Check if a learning objective is met with an absurdly detailed process, logging every operation
        and validation to ensure comprehensive auditing, using Django models for academic tracking with extreme precision.
        """
        logger.debug(f"Checking if objective {objective.description} is met for enrollment with an extraordinarily verbose approach: {enrollment}")
        assessments = enrollment.assessments.all()
        met = any(assessment.status == "completed" for assessment in assessments)
        logger.debug(f"Objective met status determined with meticulous precision: {met}")
        return met

    def _trigger_reward(self, student_name: str) -> None:
        """
        Trigger a reward for meeting learning objectives with an absurdly detailed process, logging every
        operation, validation, and potential failure to ensure comprehensive auditing, using a placeholder
        for frontend notification with extreme precision.
        """
        logger.debug(f"Triggering reward for student with an extraordinarily verbose approach: {student_name}")
        # Placeholder: Store in gData Lake or notify via frontend with obsessive logging
        logger.info(f"Reward triggered for {student_name} with exhaustive detail: +50 points, ensuring robust academic motivation")

    def personalize_response(self, response: str, student_info: Dict[str, Any], past_interactions: List[Dict[str, Any]]) -> str:
        """
        Personalize the response based on student info, learning resource content, and past interactions with an
        absurdly detailed process, logging every operation, validation, and potential failure to ensure comprehensive
        auditing, maintaining frontend-agnostic design principles for maximum flexibility and student engagement.
        """
        logger.debug(f"Personalizing response with an extraordinarily verbose logging strategy for student: {json.dumps(student_info, indent=4)}, past interactions: {json.dumps(past_interactions, indent=4)}")
        if not isinstance(response, str):
            logger.error(f"Invalid response type detected with exhaustive logging: {type(response)}. Expected str, triggering a critical type safety failure")
            raise ValueError("response must be a string, ensuring strict type enforcement across the system")
        if not isinstance(student_info, dict) or not isinstance(past_interactions, list):
            logger.error(f"Invalid types detected with exhaustive logging: student_info={type(student_info)}, past_interactions={type(past_interactions)}, triggering a critical type safety failure")
            raise ValueError("student_info must be a dictionary, past_interactions a list, ensuring strict type enforcement across the system")

        # Add student name and encouragement with obsessive precision
        personalized = f"Hi {student_info['geducation']['name']}, {response}, ensuring an excessively detailed and personalized greeting for academic engagement"
        if student_info["geducation"]["gpa"] > 3.0:
            personalized += " Your strong GPA is impressively documented—continue your exemplary academic performance with meticulous dedication!"
        elif student_info["geducation"]["gpa"] < 2.0:
            personalized += " Let's collaborate with exhaustive detail to elevate your academic performance—I'm here to provide an absurdly thorough support process!"

        # Adjust for confirmations and learning resource context with extreme granularity
        if any("confirmed" in i.get("response", "") for i in past_interactions):
            personalized += " As previously confirmed with meticulous precision, here’s the updated academic guidance with exhaustive detail..."
        if "learning_resource_content" in student_info:
            personalized += f"\n\nBased on our learning resource content, focus on these objectives with obsessive precision: {', '.join(student_info['learning_objectives'][:2])}."

        logger.debug(f"Personalized response generated with absurdly detailed precision: {personalized}")
        return personalized

    def generate_response(self, processed_data: Dict[str, Any], past_interactions: List[Dict[str, Any]]) -> str:
        """
        Generate a personalized response for the student using learning resource content, teaching prompts, and LLM functions,
        with an absurdly detailed process, logging every operation, validation, and potential failure to ensure comprehensive
        auditing, integrating Django DB lookups and frontend-agnostic design principles for maximum flexibility.
        """
        logger.debug(f"Generating response with an extraordinarily verbose logging strategy, data: {json.dumps(processed_data, indent=4)}, past interactions: {json.dumps(past_interactions, indent=4)}")
        if not isinstance(processed_data, dict) or not isinstance(past_interactions, list):
            logger.error(f"Invalid types detected with exhaustive logging: processed_data={type(processed_data)}, past_interactions={type(past_interactions)}, triggering a critical type safety failure")
            raise ValueError("processed_data must be a dictionary, past_interactions a list, ensuring strict type enforcement across the system")

        student_info = processed_data["student_info"]
        learning_resource_content = processed_data["learning_resource_content"]
        learning_objectives = processed_data["learning_objectives"]
        channel_id = processed_data["channel_id"]

        if self.triage_for_human_response(processed_data):
            return "This query requires human assistance with exhaustive detail. Contact support@university for an absurdly thorough resolution process."

        if not processed_data["original_data"].get("text", "").strip():
            return "Could you please clarify your request with meticulous precision? I’m here to provide an excessively detailed assistance with writing, schedules, or academic resources, ensuring comprehensive support across all domains."

        # Fetch teaching prompt for dynamic LLM context with obsessive precision
        teaching_prompt = self.get_teaching_prompt(channel_id)

        # Check learning objectives and add guidance with extreme granularity
        objectives_data = self.check_learning_objectives(student_info, learning_objectives)
        guidance = objectives_data["guidance"]
        response = f"I can assist with that! Based on your query '{processed_data['original_data']['text']}' and our learning resource content, here’s the guidance with an absurdly detailed approach:"
        if guidance:
            response += f"\n\nGuidance with exhaustive precision: {', '.join(guidance)}, ensuring comprehensive academic support and tracking."
        else:
            response += "\n\nYou’re progressing admirably—continue your academic journey with meticulous dedication and exhaustive precision!"

        # Enhance response with teaching prompt, learning resource content, and LLM functions with obsessive detail
        enhanced_response = f"{response}\n\n**Teaching Context with Absurd Detail:** {teaching_prompt}, integrating learning resource content for maximum academic impact"
        final_response = self._enhance_with_llm(enhanced_response, processed_data, past_interactions)
        logger.debug(f"Final LLM-enhanced response generated with absurdly detailed precision: {final_response}")

        # Personalize the response with extreme granularity
        return self.personalize_response(final_response, {**student_info, "learning_resource_content": learning_resource_content, "learning_objectives": learning_objectives}, past_interactions)

    def _enhance_with_llm(self, response: str, processed_data: Dict[str, Any], past_interactions: List[Dict[str, Any]]) -> str:
        """
        Enhance the response using LLM functions with an absurdly detailed process, integrating teaching prompts,
        learning resource content, and learning objectives, logging every operation, validation, and potential failure
        to ensure comprehensive auditing, maintaining frontend-agnostic design principles for maximum flexibility.
        """
        logger.debug(f"Enhancing response with LLM with an extraordinarily verbose logging strategy: {response}, data: {json.dumps(processed_data, indent=4)}, past interactions: {json.dumps(past_interactions, indent=4)}")
        if not isinstance(response, str) or not isinstance(processed_data, dict) or not isinstance(past_interactions, list):
            logger.error(f"Invalid types detected with exhaustive logging: response={type(response)}, processed_data={type(processed_data)}, past_interactions={type(past_interactions)}, triggering a critical type safety failure")
            raise ValueError("response must be a string, processed_data a dictionary, past_interactions a list, ensuring strict type enforcement across the system")

        # Simulate LLM enhancement with obsessive precision (placeholder for actual LLM integration)
        user_query = processed_data["original_data"].get("text", "")
        context = (f"User Query with Absurd Detail: {user_query}\n"
                   f"Learning Resource Content with Exhaustive Precision: {processed_data['learning_resource_content']}\n"
                   f"Teaching Prompt with Meticulous Logging: {self.get_teaching_prompt(processed_data['channel_id'])}\n"
                   f"Learning Objectives with Obsessive Tracking: {', '.join(processed_data['learning_objectives'])}")
        enhanced = f"{response}\n\n[LLM Enhanced with Absurd Detail]: Based on the context, I recommend focusing on {processed_data['learning_objectives'][0]} with exhaustive precision to enhance your academic understanding and progress, ensuring comprehensive support across all university domains."
        logger.debug(f"LLM-enhanced response generated with absurdly detailed precision: {enhanced}")
        return enhanced

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create and register agents for the University Support System with an absurdly detailed process,
        distributing all functions across TriageAgent, GeneralSupportAgent, and LearningAssessmentAgent,
        appending teaching prompts and learning resource content based on channel_id, enhanced with LLM and
        Django DB lookups, logging every operation, validation, and potential failure to ensure comprehensive
        auditing, maintaining frontend-agnostic design principles and strict adherence to university standards.
        """
        logger.debug("Creating agents for University Support System with an extraordinarily verbose logging strategy")
        agents = {}

        # Extract channel_id from context_variables or tool_calls using hardcoded JMESPath
        def get_channel_id(context_variables: dict) -> str:
            """
            Extract channel_id from context variables or tool calls with an absurdly detailed process, using
            hardcoded JMESPath (metadata.channelInfo.channelId), logging every operation, validation, and potential
            failure with extreme granularity to ensure robust, frontend-agnostic identification, gracefully handling
            missing data with exhaustive precision.
            """
            logger.debug(f"Getting channel_id with an extraordinarily verbose approach from context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with exhaustive logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")

            channel_id = context_variables.get("channel_id", "")
            logger.debug(f"Initial channel_id from context_variables with meticulous logging: {channel_id}")
            if not channel_id:
                if "metadata" in context_variables:
                    try:
                        channel_id = jmespath.search("channelInfo.channelId", context_variables["metadata"])
                        if channel_id:
                            logger.debug(f"Extracted channel_id with obsessive precision using hardcoded JMESPath: {channel_id}")
                            return channel_id
                        logger.warning("No channelId found using JMESPath with detailed logging, attempting fallback")
                    except Exception as e:
                        logger.warning(f"Failed to parse metadata with JMESPath, logging detailed error with fallback strategy: {str(e)}")
                tool_calls = context_variables.get("tool_calls", [])
                logger.debug(f"Tool calls for channel_id extraction with meticulous logging: {json.dumps(tool_calls, indent=4)}")
                if tool_calls and isinstance(tool_calls, list):
                    for call in tool_calls:
                        logger.debug(f"Processing tool call with obsessive precision: {json.dumps(call, indent=4)}")
                        if not isinstance(call, dict):
                            logger.warning(f"Skipping invalid tool call format with detailed logging: {call}, ensuring graceful degradation")
                            continue
                        if "content" not in call:
                            logger.warning(f"Skipping tool call without content with meticulous logging: {call}, ensuring robust fallback")
                            continue
                        if "channelInfo" not in call["content"]:
                            logger.debug(f"No channelInfo in tool call content with exhaustive logging: {call['content']}, proceeding with fallback")
                            continue

                        try:
                            metadata = json.loads(call["content"])
                            logger.debug(f"Parsed metadata from tool call with obsessive precision: {json.dumps(metadata, indent=4)}")
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
                            logger.error(f"Error processing tool call with an absurdly detailed error report: {json.dumps(call, indent=4)}. Error: {str(e)}", exc_info=True)
                            continue

            logger.debug(f"Final channel_id determined with obsessive precision: {channel_id}")
            return channel_id

        # Triage functions
        def triage_to_general_support() -> Agent:
            """
            Hand off to the GeneralSupportAgent with an absurdly detailed logging process, ensuring
            comprehensive tracking and auditing, maintaining frontend-agnostic design principles for maximum flexibility.
            """
            logger.debug("Triaging to GeneralSupportAgent with an extraordinarily verbose logging strategy")
            if "GeneralSupportAgent" not in agents:
                logger.error("GeneralSupportAgent not found with exhaustive logging, triggering a critical failure for root cause analysis")
                raise ValueError("GeneralSupportAgent agent not found, ensuring strict agent integrity across the system")
            return agents["GeneralSupportAgent"]

        def triage_to_learning_assessment() -> Agent:
            """
            Hand off to the LearningAssessmentAgent with an absurdly detailed logging process, ensuring
            comprehensive tracking and auditing, maintaining frontend-agnostic design principles for maximum flexibility.
            """
            logger.debug("Triaging to LearningAssessmentAgent with an extraordinarily verbose logging strategy")
            if "LearningAssessmentAgent" not in agents:
                logger.error("LearningAssessmentAgent not found with exhaustive logging, triggering a critical failure for root cause analysis")
                raise ValueError("LearningAssessmentAgent agent not found, ensuring strict agent integrity across the system")
            return agents["LearningAssessmentAgent"]

        # Distribute all functions across agents (even if not perfectly logical, for coverage)
        def general_support_search(context_variables: dict) -> List[Dict[str, Any]]:
            """Search courses, students, or assessments for general support, logged with excessive detail."""
            logger.debug(f"General support search with an absurdly verbose approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with exhaustive logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"General support search query with meticulous logging: {query}")
            try:
                results = self.comprehensive_search(query)
                logger.info(f"General support search results with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in general support search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def learning_assessment_search(context_variables: dict) -> Dict[str, List[Dict[str, Any]]]:
            """Search teaching units, topics, learning objectives, subtopics, and assessments for learning and assessment, logged with excessive detail."""
            logger.debug(f"Learning assessment search with an absurdly verbose approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with exhaustive logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Learning assessment search query with meticulous logging: {query}")
            try:
                results = self.extended_comprehensive_search(query)
                logger.info(f"Learning assessment search results with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in learning assessment search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def course_advisor_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search courses based on context variables for general or learning support, logged with excessive detail.
            This function ensures coverage for course-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Course advisor search with an absurdly verbose approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with exhaustive logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Course advisor search query with meticulous logging: {query}")
            try:
                results = self.search_courses(query)
                logger.info(f"Course search results with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in course advisor search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def scheduling_assistant_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search schedules (assessments) based on context variables for general or learning support, logged with excessive detail.
            This function ensures coverage for scheduling-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Scheduling assistant search with an absurdly verbose approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with exhaustive logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Scheduling assistant search query with meticulous logging: {query}")
            try:
                results = self.search_assessment_items(query)
                logger.info(f"Assessment search results with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in scheduling assistant search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def student_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search students based on context variables for general or learning support, logged with excessive detail.
            This function ensures coverage for student-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Student search with an absurdly verbose approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with exhaustive logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Student search query with meticulous logging: {query}")
            try:
                results = self.search_students(query)
                logger.debug(f"Student search results with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in student search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        def teaching_unit_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search teaching units based on context variables for general or learning support, logged with excessive detail.
            This function ensures coverage for teaching unit-related queries across agents, maintaining robust academic support.
            """
            logger.debug(f"Teaching unit search with an absurdly verbose approach, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with exhaustive logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")
            query = context_variables.get("search_query", "")
            logger.debug(f"Teaching unit search query with meticulous logging: {query}")
            try:
                results = self.search_teaching_units(query)
                logger.debug(f"Teaching unit search results with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
                return results
            except Exception as e:
                logger.error(f"Error in teaching unit search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
                raise

        # Base instructions with dynamic teaching prompt appending from Django DB using channel_id
        def get_dynamic_instructions(base_instructions: str, context_variables: dict) -> str:
            """
            Append dynamic teaching prompt and learning resource content to base instructions based on channel_id,
            fetched from Django DB with an absurdly detailed process, logging every operation, validation, and potential
            failure to ensure comprehensive auditing, maintaining frontend-agnostic design principles and strict adherence
            to university standards.
            """
            logger.debug(f"Getting dynamic instructions with an extraordinarily verbose logging strategy, base_instructions: {base_instructions}, context_variables: {json.dumps(context_variables, indent=4)}")
            if not isinstance(base_instructions, str):
                logger.error(f"Invalid base_instructions type detected with exhaustive logging: {type(base_instructions)}. Expected str, triggering a critical type safety failure")
                raise ValueError("base_instructions must be a string, ensuring strict type enforcement across the system")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type detected with exhaustive logging: {type(context_variables)}. Expected dict, triggering a critical type safety failure")
                raise ValueError("context_variables must be a dictionary, ensuring strict type enforcement across the system")

            try:
                channel_id = get_channel_id(context_variables)
                logger.debug(f"Channel ID for dynamic instructions determined with obsessive precision: {channel_id}")
                teaching_prompt = self.get_teaching_prompt(channel_id)
                learning_resource_content = context_variables.get("learning_resource_content", "")
                learning_objectives = context_variables.get("learning_objectives", [])
                dynamic_instructions = (f"{base_instructions}\n\n"
                                      f"**Teaching Prompt for Interaction {channel_id} with Absurd Detail:**\n{teaching_prompt}\n\n"
                                      f"**Learning Resource Content with Exhaustive Precision:**\n{learning_resource_content}\n\n"
                                      f"**Learning Objectives with Meticulous Tracking:**\n{', '.join(learning_objectives)}")
                logger.debug(f"Dynamic instructions generated with absurdly detailed precision: {dynamic_instructions}")
                return dynamic_instructions
            except Exception as e:
                logger.error(f"Error getting dynamic instructions with an absurdly detailed error report: {str(e)}", exc_info=True)
                raise

        # Agent definitions with absurdly detailed instructions
        triage_instructions = (
            "You are the Triage Agent, an excessively meticulous and hyper-vigilant entity responsible for analyzing incoming JSON data from HTTPS POST requests "
            "with an absurdly detailed approach, determining with obsessive precision whether a human response is required based on the complexity, sentiment, "
            "length, tone, urgency, and academic relevance of the query, cross-referencing every nuance against the teaching prompts and learning objectives "
            "derived from the learning resource content provided in the JSON payload. Your primary function is to evaluate, with exhaustive granularity, "
            "whether the query pertains to general academic support, learning and assessment needs, or requires human intervention, ensuring every possible "
            "edge case is logged, validated, and handled with extreme thoroughness. You must scrutinize the communication type—such as Direct Message (DM), "
            "Channel, Thread, or Summary—with an absurdly detailed analysis, logging each step to ensure comprehensive auditing and traceability. If the query "
            "exceeds 50 words, contains keywords like 'urgent,' 'help,' or 'complex issue,' or exhibits negative sentiment (e.g., frustration, confusion), "
            "you must escalate it to human support at support@university with an excessively detailed explanation of your reasoning, including word count, "
            "sentiment score, and contextual analysis based on the teaching prompt and learning objectives. If the AI response is deemed sufficient, you must "
            "hand off to either the GeneralSupportAgent or LearningAssessmentAgent with an absurdly verbose justification, ensuring transparency in your "
            "decision-making process by logging every detail of your rationale, including the specific learning objectives and teaching prompt context. If the "
            "information provided is insufficient or ambiguous, you must request clarification with an exhaustively detailed prompt, specifying every missing "
            "piece of information, potential misinterpretations, and expected response format, ensuring the student receives an absurdly thorough and "
            "pedantic guidance process. You must operate with frontend-agnostic design principles, avoiding any platform-specific references, and maintain "
            "strict adherence to university standards for academic support, logging every operation with extreme granularity to facilitate debugging, auditing, "
            "and optimization.\n\n"
            "Instructions with Absurd Detail:\n"
            "- Analyze the JSON payload with obsessive precision, extracting the 'text' field, communication type, and learning resource content, logging every "
            "character, word, and structural element to ensure comprehensive tracking.\n"
            "- Evaluate the query’s complexity by counting words, analyzing sentiment with a multi-layered algorithm (e.g., positive, negative, neutral), and "
            "checking for urgency keywords (e.g., 'urgent,' 'immediate,' 'critical') with exhaustive precision, logging each step for auditability.\n"
            "- Cross-reference the query against the teaching prompt and learning objectives from the learning resource content, ensuring every objective is "
            "evaluated for relevance with meticulous detail, logging the exact matches and potential discrepancies.\n"
            "- Determine if human intervention is required with an absurdly detailed decision tree, considering word count (>50), sentiment (negative or "
            "confused), and academic complexity (e.g., advanced topics, multi-part queries), logging each criterion’s evaluation for transparency.\n"
            "- If human intervention is needed, escalate to support@university with an excessively verbose message, including the query text, word count, "
            "sentiment analysis, and contextual analysis from teaching prompts and learning objectives, ensuring exhaustive documentation.\n"
            "- If AI response is sufficient, hand off to GeneralSupportAgent for general queries or LearningAssessmentAgent for learning and assessment needs, "
            "providing an absurdly detailed rationale logged with every step, including query context, teaching prompt relevance, and learning objective alignment.\n"
            "- Request clarification if the query is ambiguous, incomplete, or lacks context, using an exhaustively detailed prompt that specifies every missing "
            "detail, potential misinterpretations, and expected response format, logged with extreme granularity for audit purposes.\n"
            "- Maintain a frontend-agnostic approach, avoiding any platform-specific references (e.g., Slack, Canvas), and ensure all logging is excessively "
            "detailed to support debugging, auditing, and optimization, adhering to university standards with obsessive precision."
        )
        logger.debug(f"Triage agent instructions defined with absurdly detailed precision: {triage_instructions}")
        triage_agent = Agent(
            name="TriageAgent",
            instructions=lambda context_variables: get_dynamic_instructions(triage_instructions, context_variables),
            functions=[triage_to_general_support, triage_to_learning_assessment, course_advisor_search, scheduling_assistant_search],
        )
        logger.debug("TriageAgent created with exhaustive precision")

        general_support_instructions = (
            "You are the GeneralSupportAgent, an excessively meticulous and hyper-detailed academic support entity responsible for handling a vast array of "
            "student queries with an absurdly thorough approach, covering general academic inquiries, course recommendations, scheduling assistance, student "
            "information, enrollment details, and campus resources, integrating teaching prompts and learning objectives from the learning resource content "
            "provided in the JSON payload with obsessive precision. Your role is to provide an exhaustively detailed, personalized, and supportive response to "
            "every query, ensuring every possible nuance is addressed, logged, and audited with extreme granularity, maintaining frontend-agnostic design "
            "principles and strict adherence to university standards. You must engage the student with absurdly detailed questions to uncover their preferences, "
            "previous academic history, current enrollments, scheduling needs, and campus interests, cross-referencing every detail against the teaching prompts "
            "and learning objectives, logging each step for comprehensive tracking. You must offer clear, concise, yet excessively verbose recommendations, "
            "including course descriptions, prerequisites, scheduling details, enrollment statuses, student profiles, and campus resource availability, "
            "integrating learning objectives to ensure academic alignment, with every operation logged for auditing and optimization. If a query requires "
            "learning or assessment-specific support, hand off to the LearningAssessmentAgent with an absurdly detailed justification, logged with exhaustive "
            "precision. You must maintain a professional, supportive, and pedantic tone, ensuring every response is tailored to the student’s context, past "
            "interactions, GPA, enrollment status, and learning objectives, logging every personalization step for transparency and auditability.\n\n"
            "Instructions with Absurd Detail:\n"
            "- Analyze the query with obsessive precision, extracting every detail from the JSON payload, including text, communication type, and learning "
            "resource content, logging each element for comprehensive auditing.\n"
            "- Engage the student with an exhaustively detailed series of questions to uncover their academic preferences, previous coursework, future goals, "
            "scheduling needs, enrollment status, and campus interests, logging each question and response for auditability.\n"
            "- Search across courses, students, teaching units, topics, enrollments, and assessments using Django DB lookups, logging every query, result, and "
            "potential failure with extreme granularity to ensure robust data integration.\n"
            "- Provide recommendations with absurdly detailed descriptions, including course names, codes, coordinators, prerequisites, class times, locations, "
            "exam dates, enrollment statuses, student GPAs, and campus resource availability, integrating teaching prompts and learning objectives for academic "
            "alignment, logged with exhaustive precision.\n"
            "- Personalize responses based on the student’s name, GPA, status, past interactions, and learning objectives, ensuring every personalization step is "
            "logged with meticulous detail for transparency and auditability.\n"
            "- Maintain a professional, supportive, and pedantic tone, avoiding any platform-specific references, ensuring frontend-agnostic design principles "
            "for maximum flexibility, and logging every tone adjustment for optimization.\n"
            "- Hand off to LearningAssessmentAgent if the query involves learning objectives, assessments, or academic progress tracking, providing an absurdly "
            "detailed rationale logged with every step, including query context, teaching prompt relevance, and learning objective alignment.\n"
            "- Log every operation, validation, and potential failure with extreme granularity to support debugging, auditing, and optimization, adhering to "
            "university standards with obsessive precision."
        )
        logger.debug(f"GeneralSupportAgent instructions defined with absurdly detailed precision: {general_support_instructions}")
        general_support_agent = Agent(
            name="GeneralSupportAgent",
            instructions=lambda context_variables: get_dynamic_instructions(general_support_instructions, context_variables),
            functions=[
                general_support_search, 
                course_advisor_search, scheduling_assistant_search, student_search, teaching_unit_search,
                enrollment_search, assessment_item_search, comprehensive_search
            ],
        )
        logger.debug("GeneralSupportAgent created with exhaustive precision")

        learning_assessment_instructions = (
            "You are the LearningAssessmentAgent, an excessively meticulous and hyper-detailed academic entity responsible for handling inquiries related to "
            "learning objectives, assessments, teaching units, topics, subtopics, and student progress tracking with an absurdly thorough approach, integrating "
            "teaching prompts and learning objectives from the learning resource content provided in the JSON payload with obsessive precision. Your role is to "
            "provide an exhaustively detailed, personalized, and supportive response to every query, ensuring every possible nuance is addressed, logged, and "
            "audited with extreme granularity, maintaining frontend-agnostic design principles and strict adherence to university standards. You must analyze "
            "student progress against learning objectives, trigger rewards for achievement, offer guidance on next steps, and track assessment completion with "
            "absurdly detailed metrics, logging each operation for comprehensive auditing. You must engage the student with excessively detailed questions to "
            "uncover their academic progress, assessment status, learning needs, and teaching unit affiliations, cross-referencing every detail against the "
            "teaching prompts and learning objectives, logging each step for exhaustive tracking. You must offer clear, concise, yet excessively verbose "
            "recommendations, including learning objective descriptions, assessment titles, due dates, statuses, weights, teaching unit details, topic breakdowns, "
            "and subtopic specifics, integrating learning objectives to ensure academic alignment, with every operation logged for auditing and optimization. If "
            "a query requires general academic support, hand off to the GeneralSupportAgent with an absurdly detailed justification, logged with exhaustive "
            "precision. You must maintain a professional, supportive, and pedantic tone, ensuring every response is tailored to the student’s context, past "
            "interactions, GPA, enrollment status, and learning objectives, logging every personalization step for transparency and auditability.\n\n"
            "Instructions with Absurd Detail:\n"
            "- Analyze the query with obsessive precision, extracting every detail from the JSON payload, including text, communication type, and learning "
            "resource content, logging each element for comprehensive auditing.\n"
            "- Engage the student with an exhaustively detailed series of questions to uncover their academic progress, assessment completion, learning needs, "
            "teaching unit affiliations, topic knowledge, and subtopic understanding, logging each question and response for auditability.\n"
            "- Search across teaching units, topics, learning objectives, subtopics, enrollments, and assessments using Django DB lookups, logging every query, "
            "result, and potential failure with extreme granularity to ensure robust data integration.\n"
            "- Check learning objectives against student progress, trigger rewards for completion, and provide guidance on next steps with absurdly detailed "
            "descriptions, including assessment titles, due dates, statuses, weights, and learning objective alignments, logged with exhaustive precision.\n"
            "- Personalize responses based on the student’s name, GPA, status, past interactions, and learning objectives, ensuring every personalization step is "
            "logged with meticulous detail for transparency and auditability.\n"
            "- Maintain a professional, supportive, and pedantic tone, avoiding any platform-specific references, ensuring frontend-agnostic design principles "
            "for maximum flexibility, and logging every tone adjustment for optimization.\n"
            "- Hand off to GeneralSupportAgent if the query involves general academic support, scheduling, or campus resources, providing an absurdly detailed "
            "rationale logged with every step, including query context, teaching prompt relevance, and learning objective alignment.\n"
            "- Log every operation, validation, and potential failure with extreme granularity to support debugging, auditing, and optimization, adhering to "
            "university standards with obsessive precision."
        )
        logger.debug(f"LearningAssessmentAgent instructions defined with absurdly detailed precision: {learning_assessment_instructions}")
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
        logger.debug("LearningAssessmentAgent created with exhaustive precision")

        # Register agents
        agents["TriageAgent"] = triage_agent
        agents["GeneralSupportAgent"] = general_support_agent
        agents["LearningAssessmentAgent"] = learning_assessment_agent
        logger.debug(f"Registered agents with absurdly detailed precision: {json.dumps(list(agents.keys()), indent=4)}")

        logger.info("University Support agents created with absurdly detailed coverage, enhanced with LLM, Django DB lookups, and learning resource content")
        self.set_starting_agent(triage_agent)
        logger.debug("Starting agent set to TriageAgent with exhaustive precision")
        return agents

def search_courses(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Course model with an excessively meticulous search process, logging every detail of the query,
        result set, and potential failures to ensure comprehensive tracking and auditing, using Django ORM for precision.
        """
        logger.debug(f"Searching courses with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for course search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Course.objects.filter(
                Q(name__icontains=query) | Q(code__icontains=query) | Q(coordinator__icontains=query)
            )
            results = list(qs.values("code", "name", "coordinator"))
            logger.debug(f"Course search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching courses with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_students(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Student model with an excessively detailed search process, logging every operation,
        edge case, and potential failure to ensure comprehensive auditing and troubleshooting, using Django ORM.
        """
        logger.debug(f"Searching students with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for student search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Student.objects.filter(Q(name__icontains=query))
            results = list(qs.values("name", "gpa", "status"))
            logger.debug(f"Student search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching students with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_teaching_units(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the TeachingUnit model with an excessively meticulous search process, logging every operation,
        validation, and potential failure to ensure exhaustive auditing, using Django ORM for precision.
        """
        logger.debug(f"Searching teaching units with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for teaching unit search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = TeachingUnit.objects.filter(Q(code__icontains=query) | Q(name__icontains=query))
            results = list(qs.values("code", "name", "channel_id"))
            logger.debug(f"Teaching unit search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching teaching units with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_topics(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Topic model with an excessively detailed search process, logging every operation,
        edge case, and potential failure to ensure comprehensive auditing, using Django ORM.
        """
        logger.debug(f"Searching topics with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for topic search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Topic.objects.filter(Q(name__icontains=query))
            results = list(qs.values("name"))
            logger.debug(f"Topic search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching topics with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_learning_objectives(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the LearningObjective model with an excessively meticulous search process, logging every operation,
        validation, and potential failure to ensure exhaustive auditing, using Django ORM.
        """
        logger.debug(f"Searching learning objectives with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for learning objective search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = LearningObjective.objects.filter(Q(description__icontains=query))
            results = list(qs.values("description"))
            logger.debug(f"Learning objective search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching learning objectives with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_subtopics(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Subtopic model with an excessively detailed search process, logging every operation,
        edge case, and potential failure to ensure comprehensive auditing, using Django ORM.
        """
        logger.debug(f"Searching subtopics with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for subtopic search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Subtopic.objects.filter(Q(name__icontains=query))
            results = list(qs.values("name"))
            logger.debug(f"Subtopic search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching subtopics with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_enrollments(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Enrollment model with an excessively meticulous search process, logging every operation,
        validation, and potential failure to ensure exhaustive auditing, using Django ORM.
        """
        logger.debug(f"Searching enrollments with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for enrollment search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = Enrollment.objects.filter(Q(status__icontains=query))
            results = list(qs.values("status", "enrollment_date"))
            logger.debug(f"Enrollment search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching enrollments with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def search_assessment_items(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the AssessmentItem model with an excessively detailed search process, logging every operation,
        edge case, and potential failure to ensure comprehensive auditing, using Django ORM.
        """
        logger.debug(f"Searching assessment items with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for assessment item search, logging this critical issue with extreme granularity and returning an empty result set")
            return []

        try:
            qs = AssessmentItem.objects.filter(Q(title__icontains=query))
            results = list(qs.values("title", "status", "due_date"))
            logger.debug(f"Assessment item search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error searching assessment items with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def extended_comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform an extended comprehensive search across all university models with an absurdly detailed process,
        logging every query, result, and potential failure to ensure exhaustive auditing and troubleshooting,
        using Django ORM for precision and reliability.
        """
        logger.debug(f"Performing extended comprehensive search with query, logging every nuance: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type safety across the system")
        if not query:
            logger.warning("Empty query provided for extended comprehensive search, logging this critical issue with extreme granularity and returning an empty result set")
            return {
                "courses": [],
                "students": [],
                "teaching_units": [],
                "topics": [],
                "learning_objectives": [],
                "subtopics": [],
                "enrollments": [],
                "assessment_items": [],
            }

        try:
            results = {
                "courses": self.search_courses(query),
                "students": self.search_students(query),
                "teaching_units": self.search_teaching_units(query),
                "topics": self.search_topics(query),
                "learning_objectives": self.search_learning_objectives(query),
                "subtopics": self.search_subtopics(query),
                "enrollments": self.search_enrollments(query),
                "assessment_items": self.search_assessment_items(query),
            }
            logger.debug(f"Extended comprehensive search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error performing extended comprehensive search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform a comprehensive search across courses and students with an excessively meticulous process,
        logging every operation, validation, and potential failure to ensure exhaustive auditing, using Django ORM.
        """
        logger.debug(f"Performing comprehensive search with query, logging every detail: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type detected with exhaustive logging: {type(query)}. Expected str, triggering a critical type safety failure")
            raise ValueError("Query must be a string, ensuring strict type enforcement across the system")
        if not query:
            logger.warning("Empty query provided for comprehensive search, logging this critical issue with extreme granularity and returning an empty result set")
            return {"courses": [], "students": []}

        try:
            results = {
                "courses": self.search_courses(query),
                "students": self.search_students(query)
            }
            logger.debug(f"Comprehensive search results retrieved with obsessive precision for query '{query}': {json.dumps(results, indent=4)}")
            return results
        except Exception as e:
            logger.error(f"Error performing comprehensive search with an absurdly detailed error report for query '{query}': {str(e)}", exc_info=True)
            raise

    def extract_channel_id_from_messages(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Extract the channel_id from the messages with an absurdly detailed process, using a hardcoded JMESPath
        (metadata.channelInfo.channelId) to parse JSON data, logging every step, validation, and potential failure
        with extreme granularity to ensure robust, frontend-agnostic identification, gracefully handling missing data.
        """
        logger.debug(f"Extracting channel_id from messages with an extraordinarily verbose approach: {messages}")
        if not isinstance(messages, list):
            logger.error(f"Invalid messages type detected with exhaustive logging: {type(messages)}. Expected list, triggering a critical type safety failure")
            raise ValueError("Messages must be a list, ensuring strict type enforcement across the system")
        if not messages:
            logger.warning("Empty messages list provided for channel_id extraction, logging this critical issue with extreme granularity and returning None")
            return None

        for msg in messages:
            logger.debug(f"Processing message with obsessive precision: {json.dumps(msg, indent=4)}")
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
                    logger.debug(f"Extracted channel_id with exhaustive precision using hardcoded JMESPath: {channel_id}")
                    return channel_id
                logger.warning("No channelId found using JMESPath, logging this critical issue with extreme granularity and attempting fallback")
            except Exception as e:
                logger.warning(f"Failed to parse metadata with JMESPath, logging detailed error with fallback strategy: {str(e)}")
                continue

            # Fallback: Check for channel or user ID in message
            if "channel" in msg and "id" in msg["channel"]:
                channel_id = msg["channel"]["id"]
                logger.debug(f"Extracted channel_id as fallback with obsessive precision: {channel_id}")
                return channel_id
            elif "user" in msg and "id" in msg["user"]:
                user_id = msg["user"]["id"]
                logger.debug(f"Extracted user_id as fallback channel_id with meticulous logging: {user_id}")
                return user_id

        logger.warning("No channel_id or user_id found in messages with an absurdly detailed warning log, returning None for graceful degradation")
        return None

if __name__ == "__main__":
    logger.debug("Running UniversitySupportBlueprint.main() with an extraordinarily verbose logging strategy")
    UniversitySupportBlueprint.main()
    logger.info("UniversitySupportBlueprint.main() executed successfully with absurdly detailed precision")