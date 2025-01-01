"""
SQLite Agent

This agent provides capabilities for querying and searching records in an SQLite database.
"""

import os
import logging
from swarm import Agent

logger = logging.getLogger(__name__)

class SQLiteAgent:
    """
    Agent for interacting with an SQLite database.
    """

    def __init__(self):
        """
        Initialize the SQLiteAgent.
        """
        self._agent = Agent(
            name="SQLiteAgent",
            instructions="You can query the SQLite database for information.",
            functions=[self.query_table, self.search_records],
            parallel_tool_calls=True,
        )
        logger.info("Initialized SQLiteAgent.")

    def validate_env_vars(self):
        """
        Validate that the SQLITE_DB_PATH environment variable is set and that the database file exists.

        Raises:
            ValueError: If the environment variable is missing or the file does not exist.
        """
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        if not sqlite_db_path:
            logger.error("Environment variable SQLITE_DB_PATH is not set.")
            raise ValueError("Environment variable SQLITE_DB_PATH is not set.")

        if not os.path.exists(sqlite_db_path):
            logger.error(f"SQLite database file does not exist at: {sqlite_db_path}")
            raise ValueError(f"SQLite database file does not exist at: {sqlite_db_path}")

        logger.info("Validated SQLITE_DB_PATH environment variable and database file existence.")

    def query_table(self, table_name: str) -> str:
        """
        Query all records from a specified table in the SQLite database.

        Args:
            table_name (str): Name of the table to query.

        Returns:
            str: Query results or an error message.
        """
        logger.debug(f"Querying table: {table_name}")
        # Add SQLite database querying logic here
        return f"Queried table '{table_name}' successfully."

    def search_records(self, search_term: str) -> str:
        """
        Search records in the SQLite database that match the search term.

        Args:
            search_term (str): Term to search for in the database records.

        Returns:
            str: Search results or an error message.
        """
        logger.debug(f"Searching records for term: {search_term}")
        # Add SQLite database search logic here
        return f"Searched records for term '{search_term}' successfully."

    def get_agent(self) -> Agent:
        """
        Retrieve the SQLiteAgent instance.

        Returns:
            Agent: The SQLiteAgent instance.
        """
        return self._agent
