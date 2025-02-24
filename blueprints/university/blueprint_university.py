import logging
import os
import importlib.util
import sqlite3
import json
from typing import Dict, Any, List

from swarm.types import Agent
from swarm.extensions.blueprint import BlueprintBase

# Configure logging
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
    """
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
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

    def __init__(self, config: dict, **kwargs):
        """
        Initialize the blueprint, update configuration with default LLM settings,
        and create agents.
        """
        config.setdefault("llm", {"default": {"dummy": "value"}})
        super().__init__(config=config, **kwargs)

    def _ensure_database_setup(self) -> None:
        """
        Ensure that the database migrations are created and applied,
        and load sample data if necessary.
        """
        import django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blueprints.university.settings")
        django.setup()
        from blueprints.university.models import Course
        if Course.objects.count() == 0:
            logger.info("No courses found. Loading sample data...")
            sample_data_path = os.path.join(os.path.dirname(__file__), "sample_data.sql")
            if os.path.isfile(sample_data_path):
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.connection.executescript(open(sample_data_path).read())
                    logger.info("Sample data loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load sample data: {e}", exc_info=True)
            else:
                logger.warning(f"Sample data file {sample_data_path} not found. Skipping data population.")
        else:
            logger.info("Courses already exist. Skipping sample data loading.")

    def get_teaching_prompt(self, channel_id: str) -> str:
        """
        Retrieve the teaching prompt for the teaching unit associated with the given Slack channel ID.
        """
        from blueprints.university.models import TeachingUnit
        try:
            teaching_unit = TeachingUnit.objects.get(channel_id=channel_id)
            return teaching_unit.teaching_prompt or "No specific teaching instructions available."
        except TeachingUnit.DoesNotExist:
            logger.warning(f"No teaching unit found for channel_id: {channel_id}")
            return "No teaching unit found for this channel."

    def search_courses(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Course model for relevant courses based on a search term using Django ORM.
        """
        from django.db.models import Q
        from blueprints.university.models import Course
        qs = Course.objects.filter(
            Q(name__icontains=query) | Q(code__icontains=query) | Q(coordinator__icontains=query)
        )
        return list(qs.values("code", "name", "coordinator"))

    def search_students(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Student model for students matching the query.
        """
        from django.db.models import Q
        from blueprints.university.models import Student
        qs = Student.objects.filter(Q(name__icontains=query))
        return list(qs.values("name", "gpa", "status"))

    def search_teaching_units(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the TeachingUnit model for matching teaching units.
        """
        from django.db.models import Q
        from blueprints.university.models import TeachingUnit
        qs = TeachingUnit.objects.filter(Q(code__icontains=query) | Q(name__icontains=query))
        return list(qs.values("code", "name", "channel_id"))

    def search_topics(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Topic model for matching topics.
        """
        from django.db.models import Q
        from blueprints.university.models import Topic
        qs = Topic.objects.filter(Q(name__icontains=query))
        return list(qs.values("name"))

    def search_learning_objectives(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the LearningObjective model for matching objectives.
        """
        from django.db.models import Q
        from blueprints.university.models import LearningObjective
        qs = LearningObjective.objects.filter(Q(description__icontains=query))
        return list(qs.values("description"))

    def search_subtopics(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Subtopic model for matching subtopics.
        """
        from django.db.models import Q
        from blueprints.university.models import Subtopic
        qs = Subtopic.objects.filter(Q(name__icontains=query))
        return list(qs.values("name"))

    def search_enrollments(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Enrollment model for matching enrollments.
        """
        from django.db.models import Q
        from blueprints.university.models import Enrollment
        qs = Enrollment.objects.filter(Q(status__icontains=query))
        return list(qs.values("status", "enrollment_date"))

    def search_assessment_items(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the AssessmentItem model for matching assessment items.
        """
        from django.db.models import Q
        from blueprints.university.models import AssessmentItem
        qs = AssessmentItem.objects.filter(Q(title__icontains=query))
        return list(qs.values("title", "status", "due_date"))

    def extended_comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform an extended comprehensive search across all university models.
        """
        return {
            "courses": self.search_courses(query),
            "students": self.search_students(query),
            "teaching_units": self.search_teaching_units(query),
            "topics": self.search_topics(query),
            "learning_objectives": self.search_learning_objectives(query),
            "subtopics": self.search_subtopics(query),
            "enrollments": self.search_enrollments(query),
            "assessment_items": self.search_assessment_items(query),
        }

    def comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform a comprehensive search across courses and students.
        """
        return {
            "courses": self.search_courses(query),
            "students": self.search_students(query)
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create and register agents for the University Support System, appending teaching_prompt based on channel_id.
        """
        agents = {}

        # Extract channel_id from context_variables or tool_calls
        def get_channel_id(context_variables: dict) -> str:
            channel_id = context_variables.get("channel_id", "")
            if not channel_id:
                tool_calls = context_variables.get("tool_calls", [])
                if tool_calls and isinstance(tool_calls, list):
                    for call in tool_calls:
                        if "content" in call and "channelInfo" in call["content"]:
                            try:
                                metadata = json.loads(call["content"])
                                channel_id = metadata.get("channelInfo", {}).get("channelId", "")
                                break
                            except json.JSONDecodeError:
                                continue
            return channel_id

        # Triage functions
        def triage_to_course_advisor() -> Agent:
            return agents["CourseAdvisor"]

        def triage_to_university_poet() -> Agent:
            return agents["UniversityPoet"]

        def triage_to_scheduling_assistant() -> Agent:
            return agents["SchedulingAssistant"]

        # Course Advisor and Scheduling Assistant functions
        def course_advisor_search(context_variables: dict) -> List[Dict[str, Any]]:
            """Search courses based on context variables."""
            query = context_variables.get("search_query", "")
            results = self.search_courses(query)
            logger.info(f"Course search results for query '{query}': {results}")
            return results

        def scheduling_assistant_search(context_variables: dict) -> List[Dict[str, Any]]:
            """Search schedules based on context variables."""
            query = context_variables.get("search_query", "")
            results = self.search_assessment_items(query)
            logger.info(f"Assessment search results for query '{query}': {results}")
            return results

        def student_search(context_variables: dict) -> List[Dict[str, Any]]:
            query = context_variables.get("search_query", "")
            return self.search_students(query)

        def teaching_unit_search(context_variables: dict) -> List[Dict[str, Any]]:
            query = context_variables.get("search_query", "")
            return self.search_teaching_units(query)

        def topic_search(context_variables: dict) -> List[Dict[str, Any]]:
            query = context_variables.get("search_query", "")
            return self.search_topics(query)

        def learning_objective_search(context_variables: dict) -> List[Dict[str, Any]]:
            query = context_variables.get("search_query", "")
            return self.search_learning_objectives(query)

        def subtopic_search(context_variables: dict) -> List[Dict[str, Any]]:
            query = context_variables.get("search_query", "")
            return self.search_subtopics(query)

        def enrollment_search(context_variables: dict) -> List[Dict[str, Any]]:
            query = context_variables.get("search_query", "")
            return self.search_enrollments(query)

        def assessment_item_search(context_variables: dict) -> List[Dict[str, Any]]:
            query = context_variables.get("search_query", "")
            return self.search_assessment_items(query)

        def comprehensive_search(context_variables: dict) -> Dict[str, List[Dict[str, Any]]]:
            query = context_variables.get("search_query", "")
            return self.extended_comprehensive_search(query)

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

        # Base instructions with dynamic teaching_prompt appending
        def get_dynamic_instructions(base_instructions: str, context_variables: dict) -> str:
            channel_id = get_channel_id(context_variables)
            if channel_id:
                teaching_prompt = self.get_teaching_prompt(channel_id)
                return f"{base_instructions}\n\n**Teaching Prompt for Channel {channel_id}:**\n{teaching_prompt}"
            return base_instructions

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
        triage_agent = Agent(
            name="TriageAgent",
            instructions=lambda context_variables: get_dynamic_instructions(triage_instructions + function_descriptions, context_variables),
            functions=[triage_to_course_advisor, triage_to_university_poet, triage_to_scheduling_assistant],
        )

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
        course_advisor = Agent(
            name="CourseAdvisor",
            instructions=lambda context_variables: get_dynamic_instructions(course_advisor_instructions + function_descriptions, context_variables),
            functions=[
                course_advisor_search, student_search, teaching_unit_search, topic_search,
                learning_objective_search, subtopic_search, enrollment_search, assessment_item_search,
                comprehensive_search, triage_to_university_poet, triage_to_scheduling_assistant
            ],
        )

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
        university_poet = Agent(
            name="UniversityPoet",
            instructions=lambda context_variables: get_dynamic_instructions(university_poet_instructions + function_descriptions, context_variables),
            functions=[triage_to_course_advisor, triage_to_scheduling_assistant],
        )

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
        scheduling_assistant = Agent(
            name="SchedulingAssistant",
            instructions=lambda context_variables: get_dynamic_instructions(scheduling_assistant_instructions + function_descriptions, context_variables),
            functions=[scheduling_assistant_search, triage_to_course_advisor, triage_to_university_poet],
        )

        # Register agents
        agents["TriageAgent"] = triage_agent
        agents["CourseAdvisor"] = course_advisor
        agents["UniversityPoet"] = university_poet
        agents["SchedulingAssistant"] = scheduling_assistant

        logger.info("University Support agents created.")
        self.set_starting_agent(triage_agent)
        return agents


if __name__ == "__main__":
    UniversitySupportBlueprint.main()