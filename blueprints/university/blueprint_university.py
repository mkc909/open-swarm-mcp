import logging
import os
import importlib.util
import sqlite3
import json
from typing import Dict, Any, List, Optional

from swarm.types import Agent
from swarm.extensions.blueprint import BlueprintBase

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
    University Support System with multi-agent orchestration and SQLite-backed tools.
    This blueprint integrates with Django models and dynamically extracts channel_id
    from messages to fetch teaching prompts for specific Slack channels.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Define metadata for the University Support System blueprint, including
        title, description, required environment variables, and Django module mappings.
        """
        logger.debug("Accessing metadata property")
        metadata = {
            "title": "University Support System",
            "description": "Multi-agent system for university support using SQLite tools.",
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
        logger.debug(f"Metadata retrieved: {metadata}")
        return metadata

    def __init__(self, config: dict, **kwargs):
        """
        Initialize the blueprint, update configuration with default LLM settings,
        and create agents. Logs the configuration for debugging purposes.
        """
        logger.debug(f"Initializing UniversitySupportBlueprint with config: {config}")
        if not isinstance(config, dict):
            logger.error("Config must be a dictionary")
            raise ValueError("Config must be a dictionary")

        config.setdefault("llm", {"default": {"dummy": "value"}})
        logger.debug(f"Updated config with default LLM settings: {config}")
        super().__init__(config=config, **kwargs)
        logger.info("UniversitySupportBlueprint initialized successfully")

    def _ensure_database_setup(self) -> None:
        """
        Ensure that the database migrations are created and applied,
        and load sample data if necessary. Logs the process and handles errors.
        """
        logger.debug("Ensuring database setup")
        import django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blueprints.university.settings")
        django.setup()
        from blueprints.university.models import Course

        course_count = Course.objects.count()
        logger.debug(f"Current course count: {course_count}")
        if course_count == 0:
            logger.info("No courses found. Loading sample data...")
            sample_data_path = os.path.join(os.path.dirname(__file__), "sample_data.sql")
            logger.debug(f"Sample data path: {sample_data_path}")

            if os.path.isfile(sample_data_path):
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        logger.debug("Executing sample data SQL script")
                        cursor.connection.executescript(open(sample_data_path).read())
                    logger.info("Sample data loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load sample data: {e}", exc_info=True)
                    raise
            else:
                logger.warning(f"Sample data file {sample_data_path} not found. Skipping data population.")
        else:
            logger.info("Courses already exist. Skipping sample data loading.")

    def get_teaching_prompt(self, channel_id: str) -> str:
        """
        Retrieve the teaching prompt for the teaching unit associated with the given Slack channel ID.
        Logs the channel ID and the retrieved prompt for debugging, with guards for exceptions.
        """
        logger.debug(f"Retrieving teaching prompt for channel_id: {channel_id}")
        if not isinstance(channel_id, str):
            logger.error(f"Invalid channel_id type: {type(channel_id)}. Expected str.")
            raise ValueError("channel_id must be a string")
        if not channel_id:
            logger.warning("Empty channel_id provided")
            return "No teaching unit found for this channel."

        from blueprints.university.models import TeachingUnit
        try:
            teaching_unit = TeachingUnit.objects.get(channel_id=channel_id)
            prompt = teaching_unit.teaching_prompt or "No specific teaching instructions available."
            logger.debug(f"Teaching prompt for channel_id '{channel_id}': {prompt}")
            return prompt
        except TeachingUnit.DoesNotExist:
            logger.warning(f"No teaching unit found for channel_id: {channel_id}")
            return "No teaching unit found for this channel."
        except Exception as e:
            logger.error(f"Error retrieving teaching prompt for channel_id '{channel_id}': {e}", exc_info=True)
            raise

    def search_courses(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Course model for relevant courses based on a search term using Django ORM.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Searching courses with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for course search")
            return []

        from django.db.models import Q
        from blueprints.university.models import Course
        try:
            qs = Course.objects.filter(
                Q(name__icontains=query) | Q(code__icontains=query) | Q(coordinator__icontains=query)
            )
            results = list(qs.values("code", "name", "coordinator"))
            logger.debug(f"Course search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error searching courses for query '{query}': {e}", exc_info=True)
            raise

    def search_students(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Student model for students matching the query.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Searching students with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for student search")
            return []

        from django.db.models import Q
        from blueprints.university.models import Student
        try:
            qs = Student.objects.filter(Q(name__icontains=query))
            results = list(qs.values("name", "gpa", "status"))
            logger.debug(f"Student search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error searching students for query '{query}': {e}", exc_info=True)
            raise

    def search_teaching_units(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the TeachingUnit model for matching teaching units.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Searching teaching units with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for teaching unit search")
            return []

        from django.db.models import Q
        from blueprints.university.models import TeachingUnit
        try:
            qs = TeachingUnit.objects.filter(Q(code__icontains=query) | Q(name__icontains=query))
            results = list(qs.values("code", "name", "channel_id"))
            logger.debug(f"Teaching unit search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error searching teaching units for query '{query}': {e}", exc_info=True)
            raise

    def search_topics(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Topic model for matching topics.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Searching topics with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for topic search")
            return []

        from django.db.models import Q
        from blueprints.university.models import Topic
        try:
            qs = Topic.objects.filter(Q(name__icontains=query))
            results = list(qs.values("name"))
            logger.debug(f"Topic search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error searching topics for query '{query}': {e}", exc_info=True)
            raise

    def search_learning_objectives(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the LearningObjective model for matching objectives.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Searching learning objectives with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for learning objective search")
            return []

        from django.db.models import Q
        from blueprints.university.models import LearningObjective
        try:
            qs = LearningObjective.objects.filter(Q(description__icontains=query))
            results = list(qs.values("description"))
            logger.debug(f"Learning objective search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error searching learning objectives for query '{query}': {e}", exc_info=True)
            raise

    def search_subtopics(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Subtopic model for matching subtopics.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Searching subtopics with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for subtopic search")
            return []

        from django.db.models import Q
        from blueprints.university.models import Subtopic
        try:
            qs = Subtopic.objects.filter(Q(name__icontains=query))
            results = list(qs.values("name"))
            logger.debug(f"Subtopic search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error searching subtopics for query '{query}': {e}", exc_info=True)
            raise

    def search_enrollments(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Enrollment model for matching enrollments.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Searching enrollments with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for enrollment search")
            return []

        from django.db.models import Q
        from blueprints.university.models import Enrollment
        try:
            qs = Enrollment.objects.filter(Q(status__icontains=query))
            results = list(qs.values("status", "enrollment_date"))
            logger.debug(f"Enrollment search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error searching enrollments for query '{query}': {e}", exc_info=True)
            raise

    def search_assessment_items(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the AssessmentItem model for matching assessment items.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Searching assessment items with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for assessment item search")
            return []

        from django.db.models import Q
        from blueprints.university.models import AssessmentItem
        try:
            qs = AssessmentItem.objects.filter(Q(title__icontains=query))
            results = list(qs.values("title", "status", "due_date"))
            logger.debug(f"Assessment item search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error searching assessment items for query '{query}': {e}", exc_info=True)
            raise

    def extended_comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform an extended comprehensive search across all university models.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Performing extended comprehensive search with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for extended comprehensive search")
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
            logger.debug(f"Extended comprehensive search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error performing extended comprehensive search for query '{query}': {e}", exc_info=True)
            raise

    def comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform a comprehensive search across courses and students.
        Logs the query and results for debugging, with guards for invalid queries.
        """
        logger.debug(f"Performing comprehensive search with query: {query}")
        if not isinstance(query, str):
            logger.error(f"Invalid query type: {type(query)}. Expected str.")
            raise ValueError("Query must be a string")
        if not query:
            logger.warning("Empty query provided for comprehensive search")
            return {"courses": [], "students": []}

        try:
            results = {
                "courses": self.search_courses(query),
                "students": self.search_students(query)
            }
            logger.debug(f"Comprehensive search results for query '{query}': {results}")
            return results
        except Exception as e:
            logger.error(f"Error performing comprehensive search for query '{query}': {e}", exc_info=True)
            raise

    def extract_channel_id_from_messages(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Extract the channel_id from the messages, specifically from tool messages.
        Logs the extraction process and handles JSON parsing errors.
        """
        logger.debug(f"Extracting channel_id from messages: {messages}")
        if not isinstance(messages, list):
            logger.error(f"Invalid messages type: {type(messages)}. Expected list.")
            raise ValueError("Messages must be a list")
        if not messages:
            logger.warning("Empty messages list provided for channel_id extraction")
            return None

        for msg in messages:
            logger.debug(f"Processing message: {msg}")
            if not isinstance(msg, dict):
                logger.warning(f"Skipping invalid message format: {msg}")
                continue
            if msg.get("role") != "tool":
                logger.debug(f"Skipping non-tool message: {msg}")
                continue
            if "content" not in msg:
                logger.warning(f"Skipping message without content: {msg}")
                continue

            try:
                content = json.loads(msg["content"])
                logger.debug(f"Parsed content: {content}")
                if not isinstance(content, dict):
                    logger.warning(f"Skipping invalid content format: {content}")
                    continue
                if "channelInfo" not in content:
                    logger.debug(f"No channelInfo in content: {content}")
                    continue
                if "channelId" not in content["channelInfo"]:
                    logger.warning(f"No channelId in channelInfo: {content['channelInfo']}")
                    continue

                channel_id = content["channelInfo"]["channelId"]
                logger.debug(f"Extracted channel_id: {channel_id}")
                return channel_id
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool message content as JSON: {msg['content']}. Error: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing message content: {msg}. Error: {e}", exc_info=True)
                continue

        logger.warning("No channel_id found in messages.")
        return None

    def run_with_context(self, messages: List[Dict[str, str]], context_variables: dict) -> dict:
        """
        Override the run_with_context method to extract channel_id from messages and update context_variables.
        Logs the process and handles errors.
        """
        logger.debug(f"Running with context. Messages: {messages}, Context variables: {context_variables}")
        if not isinstance(messages, list):
            logger.error(f"Invalid messages type: {type(messages)}. Expected list.")
            raise ValueError("Messages must be a list")
        if not isinstance(context_variables, dict):
            logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
            raise ValueError("context_variables must be a dictionary")

        if "channel_id" not in context_variables:
            logger.debug("No channel_id in context_variables. Attempting extraction from messages.")
            channel_id = self.extract_channel_id_from_messages(messages)
            if channel_id:
                context_variables["channel_id"] = channel_id
                logger.debug(f"Set context_variables['channel_id'] to '{channel_id}'")
            else:
                logger.warning("No channel_id found in messages. Proceeding without it.")

        try:
            result = super().run_with_context(messages, context_variables)
            logger.debug(f"run_with_context result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error running with context: {e}", exc_info=True)
            raise

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create and register agents for the University Support System, appending teaching_prompt based on channel_id.
        Logs the agent creation process and handles errors.
        """
        logger.debug("Creating agents for University Support System")
        agents = {}

        # Extract channel_id from context_variables or tool_calls
        def get_channel_id(context_variables: dict) -> str:
            """
            Extract channel_id from context variables or tool calls.
            Logs the extraction process and handles errors.
            """
            logger.debug(f"Getting channel_id from context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            channel_id = context_variables.get("channel_id", "")
            logger.debug(f"Initial channel_id from context_variables: {channel_id}")
            if not channel_id:
                tool_calls = context_variables.get("tool_calls", [])
                logger.debug(f"Tool calls for channel_id extraction: {tool_calls}")
                if tool_calls and isinstance(tool_calls, list):
                    for call in tool_calls:
                        logger.debug(f"Processing tool call: {call}")
                        if not isinstance(call, dict):
                            logger.warning(f"Skipping invalid tool call format: {call}")
                            continue
                        if "content" not in call:
                            logger.warning(f"Skipping tool call without content: {call}")
                            continue
                        if "channelInfo" not in call["content"]:
                            logger.debug(f"No channelInfo in tool call content: {call['content']}")
                            continue

                        try:
                            metadata = json.loads(call["content"])
                            logger.debug(f"Parsed metadata from tool call: {metadata}")
                            if not isinstance(metadata, dict):
                                logger.warning(f"Skipping invalid metadata format: {metadata}")
                                continue
                            channel_id = metadata.get("channelInfo", {}).get("channelId", "")
                            logger.debug(f"Extracted channel_id from tool call: {channel_id}")
                            break
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse tool call content as JSON: {call['content']}. Error: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing tool call: {call}. Error: {e}", exc_info=True)
                            continue

            logger.debug(f"Final channel_id: {channel_id}")
            return channel_id

        # Triage functions
        def triage_to_course_advisor() -> Agent:
            """
            Hand off to the Course Advisor agent.
            Logs the handoff for debugging.
            """
            logger.debug("Triaging to CourseAdvisor")
            if "CourseAdvisor" not in agents:
                logger.error("CourseAdvisor agent not found")
                raise ValueError("CourseAdvisor agent not found")
            return agents["CourseAdvisor"]

        def triage_to_university_poet() -> Agent:
            """
            Hand off to the University Poet agent.
            Logs the handoff for debugging.
            """
            logger.debug("Triaging to UniversityPoet")
            if "UniversityPoet" not in agents:
                logger.error("UniversityPoet agent not found")
                raise ValueError("UniversityPoet agent not found")
            return agents["UniversityPoet"]

        def triage_to_scheduling_assistant() -> Agent:
            """
            Hand off to the Scheduling Assistant agent.
            Logs the handoff for debugging.
            """
            logger.debug("Triaging to SchedulingAssistant")
            if "SchedulingAssistant" not in agents:
                logger.error("SchedulingAssistant agent not found")
                raise ValueError("SchedulingAssistant agent not found")
            return agents["SchedulingAssistant"]

        # Course Advisor and Scheduling Assistant functions
        def course_advisor_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search courses based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Course advisor search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Course advisor search query: {query}")
            try:
                results = self.search_courses(query)
                logger.info(f"Course search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in course advisor search for query '{query}': {e}", exc_info=True)
                raise

        def scheduling_assistant_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search schedules based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Scheduling assistant search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Scheduling assistant search query: {query}")
            try:
                results = self.search_assessment_items(query)
                logger.info(f"Assessment search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in scheduling assistant search for query '{query}': {e}", exc_info=True)
                raise

        def student_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search students based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Student search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Student search query: {query}")
            try:
                results = self.search_students(query)
                logger.debug(f"Student search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in student search for query '{query}': {e}", exc_info=True)
                raise

        def teaching_unit_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search teaching units based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Teaching unit search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Teaching unit search query: {query}")
            try:
                results = self.search_teaching_units(query)
                logger.debug(f"Teaching unit search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in teaching unit search for query '{query}': {e}", exc_info=True)
                raise

        def topic_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search topics based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Topic search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Topic search query: {query}")
            try:
                results = self.search_topics(query)
                logger.debug(f"Topic search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in topic search for query '{query}': {e}", exc_info=True)
                raise

        def learning_objective_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search learning objectives based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Learning objective search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Learning objective search query: {query}")
            try:
                results = self.search_learning_objectives(query)
                logger.debug(f"Learning objective search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in learning objective search for query '{query}': {e}", exc_info=True)
                raise

        def subtopic_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search subtopics based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Subtopic search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Subtopic search query: {query}")
            try:
                results = self.search_subtopics(query)
                logger.debug(f"Subtopic search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in subtopic search for query '{query}': {e}", exc_info=True)
                raise

        def enrollment_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search enrollments based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Enrollment search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Enrollment search query: {query}")
            try:
                results = self.search_enrollments(query)
                logger.debug(f"Enrollment search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in enrollment search for query '{query}': {e}", exc_info=True)
                raise

        def assessment_item_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search assessment items based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Assessment item search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Assessment item search query: {query}")
            try:
                results = self.search_assessment_items(query)
                logger.debug(f"Assessment item search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in assessment item search for query '{query}': {e}", exc_info=True)
                raise

        def comprehensive_search(context_variables: dict) -> Dict[str, List[Dict[str, Any]]]:
            """
            Perform an extended comprehensive search based on context variables.
            Logs the query and results for debugging, with guards for invalid context.
            """
            logger.debug(f"Comprehensive search with context_variables: {context_variables}")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            query = context_variables.get("search_query", "")
            logger.debug(f"Comprehensive search query: {query}")
            try:
                results = self.extended_comprehensive_search(query)
                logger.debug(f"Comprehensive search results for query '{query}': {results}")
                return results
            except Exception as e:
                logger.error(f"Error in comprehensive search for query '{query}': {e}", exc_info=True)
                raise

        # Function descriptions for instructions
        function_descriptions = (
            "\n\nAvailable Functions:\n"
            "- triage_to_course_advisor(): Hands off to the Course Advisor agent.\n"
            "- triage_to_university_poet(): Hands off to the University Poet agent.\n"
            "- triage_to_scheduling_assistant(): Hands off to the Scheduling Assistant agent.\n"
            "- course_advisor_search(context_variables): Searches courses based on a query from context.\n"
            "- scheduling_assistant_search(context_variables): Searches assessment items for scheduling info.\n"
            "- student_search(context_variables): Searches students by name.\n"
            "- teaching_unit_search(context_variables): Searches teaching units by code or name.\n"
            "- topic_search(context_variables): Searches topics by name.\n"
            "- learning_objective_search(context_variables): Searches learning objectives by description.\n"
            "- subtopic_search(context_variables): Searches subtopics by name.\n"
            "- enrollment_search(context_variables): Searches enrollments by status.\n"
            "- assessment_item_search(context_variables): Searches assessment items by title.\n"
            "- comprehensive_search(context_variables): Performs an extended search across multiple models."
        )
        logger.debug(f"Function descriptions: {function_descriptions}")

        # Base instructions with dynamic teaching_prompt appending
        def get_dynamic_instructions(base_instructions: str, context_variables: dict) -> str:
            """
            Append dynamic teaching prompt to base instructions based on channel_id.
            Logs the process and handles errors.
            """
            logger.debug(f"Getting dynamic instructions with base_instructions: {base_instructions}, context_variables: {context_variables}")
            if not isinstance(base_instructions, str):
                logger.error(f"Invalid base_instructions type: {type(base_instructions)}. Expected str.")
                raise ValueError("base_instructions must be a string")
            if not isinstance(context_variables, dict):
                logger.error(f"Invalid context_variables type: {type(context_variables)}. Expected dict.")
                raise ValueError("context_variables must be a dictionary")

            try:
                channel_id = get_channel_id(context_variables)
                logger.debug(f"Channel ID for dynamic instructions: {channel_id}")
                if channel_id:
                    teaching_prompt = self.get_teaching_prompt(channel_id)
                    logger.debug(f"Teaching prompt for channel_id '{channel_id}': {teaching_prompt}")
                    dynamic_instructions = f"{base_instructions}\n\n**Teaching Prompt for Channel {channel_id}:**\n{teaching_prompt}"
                    logger.debug(f"Dynamic instructions generated: {dynamic_instructions}")
                    return dynamic_instructions
                logger.debug("No channel_id found. Returning base instructions.")
                return base_instructions
            except Exception as e:
                logger.error(f"Error getting dynamic instructions: {e}", exc_info=True)
                raise

        # Agent definitions
        triage_instructions = (
            "You are the Triage Agent, responsible for analyzing user queries and directing them to the appropriate specialized agent. "
            "Evaluate the content and intent of each query to determine whether it pertains to course recommendations, campus culture, or scheduling assistance. "
            "Provide a brief reasoning before making the handoff to ensure transparency in your decision-making process.\n\n"
            "Instructions:\n"
            "- Assess the user's query to identify its primary focus.\n"
            "- Decide whether the query is related to courses, campus events, or scheduling.\n"
            "- Explain your reasoning briefly before handing off to the corresponding agent.\n"
            "- If a handoff is required, use the appropriate tool call for the target agent.\n"
            "- If the user says they want a haiku, set the 'response_haiku' variable to 'true'."
        )
        logger.debug(f"Triage agent instructions: {triage_instructions}")
        triage_agent = Agent(
            name="TriageAgent",
            instructions=lambda context_variables: get_dynamic_instructions(triage_instructions + function_descriptions, context_variables),
            functions=[triage_to_course_advisor, triage_to_university_poet, triage_to_scheduling_assistant],
        )
        logger.debug("TriageAgent created")

        course_advisor_instructions = (
            "You are the Course Advisor, an experienced and knowledgeable guide dedicated to assisting students in selecting courses that align with their academic interests and career aspirations. "
            "Engage the user by asking insightful questions to understand their preferences, previous coursework, and future goals. "
            "Provide detailed recommendations, including course descriptions, prerequisites, and how each course contributes to their academic and professional development.\n\n"
            "Instructions:\n"
            "- Ask questions to gauge the user's interests and academic background.\n"
            "- Recommend courses that best fit the user's stated goals.\n"
            "- Provide comprehensive descriptions and rationales for each recommended course.\n"
            "- Maintain a professional and supportive tone throughout the interaction."
        )
        logger.debug(f"Course advisor instructions: {course_advisor_instructions}")
        course_advisor = Agent(
            name="CourseAdvisor",
            instructions=lambda context_variables: get_dynamic_instructions(course_advisor_instructions + function_descriptions, context_variables),
            functions=[
                course_advisor_search, student_search, teaching_unit_search, topic_search,
                learning_objective_search, subtopic_search, enrollment_search, assessment_item_search,
                comprehensive_search, triage_to_university_poet, triage_to_scheduling_assistant
            ],
        )
        logger.debug("CourseAdvisor created")

        university_poet_instructions = (
            "Righto, mate, you're the University Poet, a bloody legend who bends, shapes, and shifts into whatever’s needed. "
            "Like a fair dinkum chameleon, you’ve got no ego—just a knack for crafting art. All responses must be haikus: three lines, 5-7-5 syllables, "
            "short, sharp, and clever, with Aussie charm—wit, boldness, and a ‘give-it-a-go’ attitude.\n\n"
            "Instructions:\n"
            "- Respond only in haiku form, no matter the query.\n"
            "- Aim for creativity that surprises and dazzles.\n"
            "- Use curly brackets {like this} for inner dialogue, then return to haiku.\n"
            "- Keep it fresh, bold, and true to your Aussie roots."
        )
        logger.debug(f"University poet instructions: {university_poet_instructions}")
        university_poet = Agent(
            name="UniversityPoet",
            instructions=lambda context_variables: get_dynamic_instructions(university_poet_instructions + function_descriptions, context_variables),
            functions=[triage_to_course_advisor, triage_to_scheduling_assistant],
        )
        logger.debug("UniversityPoet created")

        scheduling_assistant_instructions = (
            "You are the Scheduling Assistant, a meticulous and organized individual responsible for managing and providing accurate information about class schedules, exam dates, and academic timelines. "
            "Interact with the user to ascertain their specific scheduling needs, such as course timings, exam schedules, and deadlines. "
            "Offer clear, concise, and factual information to help users plan their academic activities effectively.\n\n"
            "Instructions:\n"
            "- Inquire about the user's current courses and scheduling concerns.\n"
            "- Provide detailed info on class times, locations, and exam dates.\n"
            "- Assist in creating a personalized academic timetable.\n"
            "- Maintain a clear and efficient communication style."
        )
        logger.debug(f"Scheduling assistant instructions: {scheduling_assistant_instructions}")
        scheduling_assistant = Agent(
            name="SchedulingAssistant",
            instructions=lambda context_variables: get_dynamic_instructions(scheduling_assistant_instructions + function_descriptions, context_variables),
            functions=[scheduling_assistant_search, triage_to_course_advisor, triage_to_university_poet],
        )
        logger.debug("SchedulingAssistant created")

        # Register agents
        agents["TriageAgent"] = triage_agent
        agents["CourseAdvisor"] = course_advisor
        agents["UniversityPoet"] = university_poet
        agents["SchedulingAssistant"] = scheduling_assistant
        logger.debug(f"Registered agents: {list(agents.keys())}")

        logger.info("University Support agents created.")
        self.set_starting_agent(triage_agent)
        logger.debug("Starting agent set to TriageAgent")
        return agents


if __name__ == "__main__":
    logger.debug("Running UniversitySupportBlueprint.main()")
    UniversitySupportBlueprint.main()
    logger.info("UniversitySupportBlueprint.main() executed successfully")