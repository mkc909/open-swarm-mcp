import logging
import os
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
COURSE_ADVISOR_TABLE = "courses"


class UniversitySupportBlueprint(BlueprintBase):
    """
    University Support System with multi-agent orchestration and SQLite-backed tools.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the blueprint.
        """
        return {
            "title": "University Support System",
            "description": "Multi-agent system for university support using SQLite tools.",
            "required_mcp_servers": [],
            "env_vars": ["SQLITE_DB_PATH"],
        }

    def __init__(self, config: dict, **kwargs):
        """
        Initialize the blueprint, validate environment variables, and create agents.
        """
        self._ensure_database_setup()
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

        # Create tables if they don't exist
        logger.info("Ensuring tables exist...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {COURSE_ADVISOR_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                description TEXT NOT NULL,
                discipline TEXT NOT NULL
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
        conn.commit()

        # Check if the tables are empty
        logger.info("Checking if tables need sample data...")
        cursor.execute(f"SELECT COUNT(*) FROM {COURSE_ADVISOR_TABLE}")
        course_count = cursor.fetchone()[0]

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
                "You are the Triage Agent. Analyze user queries and direct them to the appropriate specialized agent. "
                "Use tools like `triage_to_course_advisor` to handoff queries."
            ),
            functions=[triage_to_course_advisor, triage_to_university_poet, triage_to_scheduling_assistant],
        )
        course_advisor = Agent(
            name="CourseAdvisor",
            instructions="You are the Course Advisor. Provide course recommendations based on user interests.",
            functions=[course_advisor_search, triage_to_university_poet, triage_to_scheduling_assistant],
        )
        university_poet = Agent(
            name="UniversityPoet",
            instructions="You are the University Poet. Respond creatively to user queries with haikus or poetic advice.",
            functions=[triage_to_course_advisor, triage_to_scheduling_assistant],
        )
        scheduling_assistant = Agent(
            name="SchedulingAssistant",
            instructions="You are the Scheduling Assistant. Manage and provide information about schedules and exams.",
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

    def execute(self) -> Dict[str, Any]:
        """
        Main execution logic for the blueprint.
        """
        try:
            user_query = input("How can I assist you today? ")
        except KeyboardInterrupt:
            logger.info("User terminated the session.")
            return {"status": "terminated"}

        messages = [{"role": "user", "content": user_query}]
        context_variables = {}

        result = self.run_with_context(messages, context_variables)
        logger.info("Interaction completed.")
        return result

if __name__ == "__main__":
    UniversitySupportBlueprint.main()
