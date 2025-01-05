import logging
import os
import sqlite3
from typing import Dict, Any

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
    University Support System with agent orchestration and database-backed tools.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the blueprint.
        """
        return {
            "title": "University Support System",
            "description": "Multi-agent system for university support using MCP tools.",
            "required_mcp_servers": ["sqlite"],
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
        Set up the SQLite database and load sample data if it does not exist.
        """
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        if not sqlite_db_path:
            raise EnvironmentError("Environment variable SQLITE_DB_PATH is not set.")

        # Check if the database file already exists
        db_exists = os.path.isfile(sqlite_db_path)
        if not db_exists:
            logger.info("Database does not exist. Setting up the database.")
            os.makedirs(os.path.dirname(sqlite_db_path), exist_ok=True)
            conn = sqlite3.connect(sqlite_db_path)
            cursor = conn.cursor()

            # Create tables
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

            # Check for and load sample data
            sample_data_path = os.path.join(os.path.dirname(__file__), "sample_data.sql")
            if os.path.isfile(sample_data_path):
                logger.info(f"Loading sample data from {sample_data_path}.")
                try:
                    with open(sample_data_path, 'r') as file:
                        sample_data = file.read()
                        cursor.executescript(sample_data)
                        logger.info("Sample data loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load sample data: {e}", exc_info=True)
                    raise e

            conn.commit()
            conn.close()
            logger.info("SQLite database setup completed.")
        else:
            logger.info("Database already exists. Skipping setup.")

    def _load_instructions(self, agent_name: str) -> str:
        """
        Load agent instructions from an external `.txt` file if available.
        Fallback to hardcoded instructions otherwise.

        Args:
            agent_name (str): Name of the agent.

        Returns:
            str: Instructions for the agent.
        """
        blueprint_dir = os.path.dirname(__file__)
        instruction_filename = f"instructions_{agent_name.replace(' ', '_')}.txt"
        instruction_path = os.path.join(blueprint_dir, instruction_filename)

        if os.path.isfile(instruction_path):
            try:
                logger.info(f"Loading instructions for {agent_name} from {instruction_filename}.")
                with open(instruction_path, 'r') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Error reading {instruction_filename}: {e}", exc_info=True)

        logger.warning(f"Instruction file not found for {agent_name}. Using hardcoded instructions.")
        return self._default_instructions(agent_name)

    def _default_instructions(self, agent_name: str) -> str:
        """
        Provide hardcoded instructions as a fallback.

        Args:
            agent_name (str): Name of the agent.

        Returns:
            str: Default instructions for the agent.
        """
        instructions = {
            "TriageAgent": (
                "You are the Triage Agent. Analyze user queries and direct them to the appropriate specialized agent. "
                "Use tools like `triage_to_course_advisor` to handoff queries."
            ),
            "CourseAdvisor": (
                "You are the Course Advisor. Provide course recommendations based on user interests."
            ),
            "UniversityPoet": (
                "You are the University Poet. Respond creatively to user queries with haikus or poetic advice."
            ),
            "SchedulingAssistant": (
                "You are the Scheduling Assistant. Manage and provide information about schedules and exams."
            ),
        }
        return instructions.get(agent_name, "Default agent instructions.")

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create and register agents for the University Support System.
        """
        agents = {}

        def triage_to_course_advisor() -> Agent:
            return agents["CourseAdvisor"]

        def triage_to_university_poet() -> Agent:
            return agents["UniversityPoet"]

        def triage_to_scheduling_assistant() -> Agent:
            return agents["SchedulingAssistant"]

        # Create agents
        triage_agent = Agent(
            name="TriageAgent",
            instructions=self._load_instructions("TriageAgent"),
            functions=[triage_to_course_advisor, triage_to_university_poet, triage_to_scheduling_assistant],
        )
        course_advisor = Agent(
            name="CourseAdvisor",
            instructions=self._load_instructions("CourseAdvisor"),
        )
        university_poet = Agent(
            name="UniversityPoet",
            instructions=self._load_instructions("UniversityPoet"),
        )
        scheduling_assistant = Agent(
            name="SchedulingAssistant",
            instructions=self._load_instructions("SchedulingAssistant"),
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
    blueprint = UniversitySupportBlueprint(config={})
    blueprint.execute()
