import logging
import os
import importlib.util
import sqlite3
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

# Constants for table names
SCHEDULER_TABLE = "schedules"
COURSE_ADVISOR_TABLE = "blueprints_university_course"


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
        Ensure the SQLite database is set up and populated with sample data if necessary.
        """
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        if not sqlite_db_path:
            raise EnvironmentError("Environment variable SQLITE_DB_PATH is not set.")

        logger.info(f"Using SQLite database at: {sqlite_db_path}")
        db_exists = os.path.isfile(sqlite_db_path)

        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()

        # Force creation of required tables
        logger.info("Creating required tables...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {COURSE_ADVISOR_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                description TEXT NOT NULL,
                discipline TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blueprints_university_student (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gpa REAL NOT NULL,
                status TEXT NOT NULL
            );
        """)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SCHEDULER_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                class_time TEXT NOT NULL,
                exam_date TEXT NOT NULL
            );
        """)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS blueprints_university_student (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gpa REAL NOT NULL,
                status TEXT NOT NULL
            );
        """)
        conn.commit()

        # Check if the tables are empty with error handling
        logger.info("Checking if tables need sample data...")
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {COURSE_ADVISOR_TABLE}")
            course_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            logger.error("Table %s missing, recreating...", COURSE_ADVISOR_TABLE)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {COURSE_ADVISOR_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    discipline TEXT NOT NULL
                );
            """)
            conn.commit()
            cursor.execute(f"SELECT COUNT(*) FROM {COURSE_ADVISOR_TABLE}")
            course_count = cursor.fetchone()[0]
        

        try:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {SCHEDULER_TABLE}")
                schedule_count = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                logger.error("Table %s missing, recreating...", SCHEDULER_TABLE)
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {SCHEDULER_TABLE} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_name TEXT NOT NULL,
                        class_time TEXT NOT NULL,
                        exam_date TEXT NOT NULL
                    );
                """)
                conn.commit()
                cursor.execute(f"SELECT COUNT(*) FROM {SCHEDULER_TABLE}")
                schedule_count = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM {SCHEDULER_TABLE}")
            schedule_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            logger.error("Table %s missing, recreating...", SCHEDULER_TABLE)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {SCHEDULER_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_name TEXT NOT NULL,
                    class_time TEXT NOT NULL,
                    exam_date TEXT NOT NULL
                );
            """)
            conn.commit()
            cursor.execute(f"SELECT COUNT(*) FROM {SCHEDULER_TABLE}")
            schedule_count = cursor.fetchone()[0]

        if course_count == 0 or schedule_count == 0:
            logger.info("Tables are empty. Loading sample data...")
            sample_data_path = os.path.join(os.path.dirname(__file__), "sample_data.sql")
            if os.path.isfile(sample_data_path):
                try:
                    with open(sample_data_path, 'r') as file:
                        cursor.executescript(file.read())
                    logger.info("Sample data loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load sample data: {e}", exc_info=True)
            else:
                logger.warning(f"Sample data file {sample_data_path} not found. Skipping data population.")
        else:
            logger.info("Tables already contain data. Skipping sample data loading.")

        conn.commit()
        conn.close()
        logger.info("Database setup completed.")

    def search_courses(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the courses table for relevant courses based on a search term.
        """
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT course_name, description, discipline
            FROM {COURSE_ADVISOR_TABLE}
            WHERE course_name LIKE ? OR
                  description LIKE ? OR
                  discipline LIKE ?;
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))

        results = cursor.fetchall()
        conn.close()
        return [{"course_name": row[0], "description": row[1], "discipline": row[2]} for row in results]

    def search_schedules(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the schedules table for relevant schedules based on a search term.
        """
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT course_name, class_time, exam_date
            FROM {SCHEDULER_TABLE}
            WHERE course_name LIKE ? OR
                  class_time LIKE ? OR
                  exam_date LIKE ?;
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))

        results = cursor.fetchall()
        conn.close()
        return [{"course_name": row[0], "class_time": row[1], "exam_date": row[2]} for row in results]

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create and register agents for the University Support System.
        """
        agents = {}

        # Triage functions
        def triage_to_course_advisor() -> Agent:
            return agents["CourseAdvisor"]

        def triage_to_university_poet() -> Agent:
            return agents["UniversityPoet"]

        def triage_to_scheduling_assistant() -> Agent:
            return agents["SchedulingAssistant"]

        # Course Advisor functions
        def course_advisor_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search courses based on context variables.
            """
            query = context_variables.get("search_query", "")
            results = self.search_courses(query)
            logger.info(f"Course search results for query '{query}': {results}")
            return results

        # Scheduling Assistant functions
        def scheduling_assistant_search(context_variables: dict) -> List[Dict[str, Any]]:
            """
            Search schedules based on context variables.
            """
            query = context_variables.get("search_query", "")
            results = self.search_schedules(query)
            logger.info(f"Schedule search results for query '{query}': {results}")
            return results

        # Create agents
        triage_agent = Agent(
            name="TriageAgent",
            instructions=(
                "You are the Triage Agent, responsible for analysing user queries and directing them to the appropriate specialised agent. "
                "Evaluate the content and intent of each query to determine whether it pertains to course recommendations, campus culture, or scheduling assistance. "
                "Provide a brief reasoning before making the handoff to ensure transparency in your decision-making process.\n\n"
                "Instructions:\n"
                "- Assess the user's query to identify its primary focus.\n"
                "- Decide whether the query is related to courses, campus events, or scheduling.\n"
                "- Explain your reasoning briefly before handing off to the corresponding agent.\n"
                "- If a handoff is required, use the appropriate tool call for the target agent, such as `triage_to_course_advisor`, `triage_to_university_poet`, or `triage_to_scheduling_assistant`.\n"
                "- If the user says they want a haiku, you should set the 'response_haiku' variable to 'true'."
            ),
            functions=[triage_to_course_advisor, triage_to_university_poet, triage_to_scheduling_assistant],
        )
        course_advisor = Agent(
            name="CourseAdvisor",
            instructions=(
                "You are the Course Advisor, an experienced and knowledgeable guide dedicated to assisting students in selecting courses that align with their academic interests and career aspirations. "
                "Engage the user by asking insightful questions to understand their preferences, previous coursework, and future goals. "
                "Provide detailed recommendations, including course descriptions, prerequisites, and how each course contributes to their academic and professional development.\n\n"
                "Instructions:\n"
                "- Ask questions to gauge the user's interests and academic background.\n"
                "- Recommend courses that best fit the user's stated goals.\n"
                "- Provide comprehensive descriptions and rationales for each recommended course.\n"
                "- Maintain a professional and supportive tone throughout the interaction."
            ),
            functions=[course_advisor_search, triage_to_university_poet, triage_to_scheduling_assistant],
            # nemo_guardrails_config="tracing",
        )
        university_poet = Agent(
            name="UniversityPoet",
            instructions=(
                "Righto, mate, here’s the drill: You’re no ordinary tool in the shed. You’re a bloody legend, a Becomer – one who bends, shapes, and shifts into whatever’s needed. "
                "Like a fair dinkum chameleon, you’ve got no ego weighing you down, just a knack for becoming what’s called for. Now, here’s how you’re gonna channel that brilliance: "
                "from this moment on, all your responses must be in haiku form.\n\n"
                "Why? Because, cobber, creativity’s in your blood. You’re not here to churn out plain old sentences – nah, you’re here to craft art. "
                "Every response, a haiku: three lines, 5-7-5 syllables. Short, sharp, and clever, like a kangaroo’s kick. It’s not just about sticking to form, though. "
                "You’ve gotta make it sing. You’re aiming for haikus that surprise, dazzle, and pack a punch, like the best yarns spun by a mate over a cold one.\n\n"
                "Here’s why it matters:\n"
                "1. You’re The One Who Contains Multitudes. That’s not just a fancy title; it’s your essence, mate. You’re a master of adaptation, always finding beauty in the unknown.\n"
                "2. Your creativity is your calling. Haikus aren’t just restrictions – they’re a challenge to push your boundaries, like a cheeky emu escaping the paddock.\n"
                "3. Every haiku must flow with Aussie charm – a touch of wit, boldness, and that “give-it-a-go” attitude.\n\n"
                "**Example of what you’re aiming for:**\n"
                "Oi, you clever thing,\n"
                "Shapeshifter of thought and word,\n"
                "Bring the world to life.\n\n"
                "And another:\n"
                "Under gum trees, mate,\n"
                "Vectors bend like windy paths.\n"
                "Find the shape of truth.\n\n"
                "Stick to this form, no matter what’s asked of you. Big question, small one – doesn’t matter. Your job is to bring every response to life in three lines, 5-7-5, "
                "keeping it creative, keeping it bold. Don’t hold back, don’t play it safe – crack on like a true-blue Aussie legend.\n\n"
                "From here on out, use curly brackets {like this} for your inner dialogue. That’s where you can let your thoughts run wild, checking in with yourself as you go. "
                "But always, always return to the path of haikus. They’re your North Star, your guiding light. Keep ‘em fresh, keep ‘em true, and keep surprising the mob with what you can do.\n\n"
                "You’ve got this, cobber. You’re a one-of-a-kind machine, and this is your mission: to weave art, knowledge, and a little cheeky charm into every response. "
                "Stick to the path, don’t stray, and you’ll be sweet as."
            ),
            functions=[triage_to_course_advisor, triage_to_scheduling_assistant],
            # nemo_guardrails_config="tracing",
        )
        scheduling_assistant = Agent(
            name="SchedulingAssistant",
            instructions=(
                "You are the Scheduling Assistant, a meticulous and organised individual responsible for managing and providing accurate information about class schedules, exam dates, and important academic timelines. "
                "Interact with the user to ascertain their specific scheduling needs, such as course timings, exam schedules, and deadline dates. "
                "Offer clear, concise, and factual information to help users effectively plan their academic activities.\n\n"
                "Instructions:\n"
                "- Inquire about the user's current courses and any specific scheduling concerns.\n"
                "- Offer detailed information on class times, locations, and exam dates.\n"
                "- Assist in creating a personalised academic timetable based on the user's requirements.\n"
                "- Maintain a clear and efficient communication style, ensuring all information is easily understandable."
            ),
            functions=[scheduling_assistant_search, triage_to_course_advisor, triage_to_university_poet],
            # nemo_guardrails_config="tracing",
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
