# blueprints/sqlite_and_search/blueprint_sqlite_and_search.py

"""
SQLite and Search Integration Blueprint

This blueprint integrates SQLite database querying with search capabilities via MCP servers.
"""

import os
from typing import Dict, Any, Optional
from swarm import Agent, Swarm
from open_swarm_mcp.blueprint_base import BlueprintBase
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class SQLiteSearchBlueprint(BlueprintBase):
    """
    SQLite and Search Integration Blueprint Implementation.
    """

    def __init__(self):
        self._metadata = {
            "title": "SQLite and Search Integration",
            "description": "Integrates SQLite database querying with search capabilities via MCP servers.",
            "required_mcp_servers": ["sqlite"],
            "env_vars": ["SQLITE_DB_PATH"]
        }
        self.client = Swarm()
        logger.info("Initialized SQLiteSearch Blueprint with Swarm.")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def validate_env_vars(self) -> None:
        """Validate that required environment variables are set and directories exist."""
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        if not sqlite_db_path:
            raise ValueError("Environment variable SQLITE_DB_PATH is not set.")

        if not os.path.exists(sqlite_db_path):
            raise ValueError(f"SQLite database file does not exist at: {sqlite_db_path}")
        logger.info("Validated SQLITE_DB_PATH environment variable.")

    def create_agent(self) -> Agent:
        """Create and configure the SQLite and Search agent."""
        agent = Agent(
            name="SQLiteSearchAgent",
            instructions="""You can query the SQLite database and perform searches.
Available operations include:
- Querying data from tables
- Searching records
Please ensure all queries are optimized and secure.""",
            functions=[
                self.query_table,
                self.search_records
            ],
            parallel_tool_calls=True
        )
        logger.info("Created SQLiteSearchAgent with SQLite operation functions.")
        return agent

    def get_agents(self) -> Dict[str, Agent]:
        """
        Returns a dictionary of agents.
        """
        return {"SQLiteSearchAgent": self.create_agent()}

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        self.validate_env_vars()
        agent = self.create_agent()

        # Allow for message override from framework config
        default_message = {
            "role": "user",
            "content": "Query all records from the 'users' table."
        }
        messages = config.get('messages', [default_message]) if config else [default_message]

        response = self.client.run(agent=agent, messages=messages)

        return {
            "status": "success",
            "messages": response.messages,
            "metadata": self.metadata
        }

    def interactive_mode(self) -> None:
        """
        Use Swarm's REPL loop, starting with the SQLiteSearchAgent.
        """
        logger.info("Launching interactive mode with SQLiteSearchAgent.")
        run_demo_loop(starting_agent=self.create_agent())

    # SQLite and Search operation functions

    def query_table(self, table_name: str) -> str:
        """
        Query all records from the specified table in the SQLite database.

        Args:
            table_name (str): Name of the table to query.

        Returns:
            str: Query results or error message.
        """
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        try:
            import sqlite3
            conn = sqlite3.connect(sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            conn.close()
            logger.info(f"Queried table '{table_name}' successfully.")
            return f"Records from '{table_name}':\n" + "\n".join(map(str, rows))
        except Exception as e:
            error_msg = f"Error querying table '{table_name}': {e}"
            logger.error(error_msg)
            return error_msg

    def search_records(self, search_term: str) -> str:
        """
        Search records in the SQLite database that match the search term.

        Args:
            search_term (str): Term to search for in the records.

        Returns:
            str: Search results or error message.
        """
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        try:
            import sqlite3
            conn = sqlite3.connect(sqlite_db_path)
            cursor = conn.cursor()
            # Example: Search all text fields in all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            results = []
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                text_columns = [col[1] for col in columns if col[2].upper() in ('TEXT', 'VARCHAR')]
                for col in text_columns:
                    cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE ?", ('%'+search_term+'%',))
                    rows = cursor.fetchall()
                    results.extend(rows)
            conn.close()
            if results:
                logger.info(f"Found {len(results)} records matching '{search_term}'.")
                return f"Search results for '{search_term}':\n" + "\n".join(map(str, results))
            else:
                logger.info(f"No records found matching '{search_term}'.")
                return f"No records found matching '{search_term}'."
        except Exception as e:
            error_msg = f"Error searching records with term '{search_term}': {e}"
            logger.error(error_msg)
            return error_msg
