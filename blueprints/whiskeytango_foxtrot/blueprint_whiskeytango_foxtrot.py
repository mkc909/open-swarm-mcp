"""
WhiskeyTangoFoxtrot: Tracking Free Online Services

A chaotic spy-themed blueprint with a multi-tiered agent hierarchy for tracking and managing free online services using SQLite and web search capabilities.
The hierarchy includes a top-tier coordinator, middle managers for database and web operations, and minions for specific tasks.
"""

import logging
import sqlite3
from typing import Dict, Any

from swarm.types import Agent
from swarm.extensions.blueprint import BlueprintBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class WhiskeyTangoFoxtrotBlueprint(BlueprintBase):
    """
    Blueprint for tracking free online services with a hierarchical spy-inspired agent team.

    This blueprint manages a SQLite database at SQLITE_DB_PATH to track free online services (e.g., Fly.io for container hosting, Grok for AI inference) and uses web search capabilities to fetch and process service data. It demonstrates a multi-tiered agent hierarchy with explicit handoffs for efficient task delegation.

    Hierarchy:
    - **Top Tier**: Valory (Coordinator) - Oversees operations, delegates to middle managers.
    - **Middle Managers**:
      - Tyril (DB Manager) - Manages database and filesystem tasks, delegates to Larry (filesystem) and Kriegs (DB updates).
      - Tray (Web Manager) - Manages web data tasks, delegates to Vanna (search/fetch) and Marcher (processing/docs).
    - **Minions**:
      - Under Tyril:
        - Larry - Manages temporary file storage using filesystem MCP server.
        - Kriegs - Performs CRUD operations on the SQLite database.
      - Under Tray:
        - Vanna - Locates services and fetches data using brave-search and mcp-npx-fetch.
        - Marcher - Processes fetched data into a standardized format using mcp-doc-forge.

    Attributes:
        metadata (Dict[str, Any]): Blueprint metadata including title, description, required MCP servers, and environment variables.

    Methods:
        initialize_db(db_path: str) -> None: Initializes the SQLite database schema if not present.
        create_agents() -> Dict[str, Agent]: Creates and configures the agent hierarchy.
    """
    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for the WhiskeyTangoFoxtrot blueprint.

        Returns:
            Dict[str, Any]: A dictionary containing the blueprint's title, description, required MCP servers, and environment variables.
        """
        return {
            "title": "WhiskeyTangoFoxtrot",
            "description": "Tracks free online services with SQLite and web search using a multi-tiered agent hierarchy.",
            "required_mcp_servers": ["sqlite", "brave-search", "mcp-npx-fetch", "mcp-doc-forge", "filesystem"],
            "cli_name": "wtf",
            "env_vars": ["BRAVE_API_KEY", "SQLITE_DB_PATH", "ALLOWED_PATH"]
        }

    def initialize_db(self, db_path: str) -> None:
        """
        Initialize the SQLite database schema if the 'services' table doesn't exist.

        Creates a table named 'services' with columns: id (INTEGER PRIMARY KEY), name (TEXT NOT NULL), type (TEXT NOT NULL),
        url (TEXT), api_key (TEXT), usage_limits (TEXT), documentation_link (TEXT). This table stores details of free online services.

        Args:
            db_path (str): Path to the SQLite database file, sourced from the SQLITE_DB_PATH environment variable.

        Raises:
            sqlite3.Error: If there's an error connecting to or initializing the database.
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='services';")
            if not cursor.fetchone():
                logger.info("Initializing 'services' table in SQLite database.")
                cursor.execute("""
                    CREATE TABLE services (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        url TEXT,
                        api_key TEXT,
                        usage_limits TEXT,
                        documentation_link TEXT
                    );
                """)
                conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Error initializing SQLite database: {e}")
            raise

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create and configure the multi-tiered agent hierarchy for tracking free online services.

        Initializes the SQLite database schema, sets up agents with explicit instructions and named handoff functions,
        and returns a dictionary of configured agents. The hierarchy ensures efficient task delegation and data flow.

        Returns:
            Dict[str, Agent]: A dictionary mapping agent names to their configured Agent instances.

        Raises:
            EnvironmentError: If required environment variables (BRAVE_API_KEY, SQLITE_DB_PATH, ALLOWED_PATH) are not set.
        """
        import os
        brave_api_key = os.getenv("BRAVE_API_KEY")
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        allowed_path = os.getenv("ALLOWED_PATH", "/default/path")
        if not brave_api_key:
            raise EnvironmentError("Environment variable 'BRAVE_API_KEY' is not set.")
        if not sqlite_db_path:
            raise EnvironmentError("Environment variable 'SQLITE_DB_PATH' is not set.")
        if not allowed_path:
            raise EnvironmentError("Environment variable 'ALLOWED_PATH' is not set.")

        # Initialize the database schema
        self.initialize_db(sqlite_db_path)
        
        agents = {}

        # Handoff Functions
        def handoff_to_tyril() -> Agent:
            """Delegate to Tyril, the database and filesystem middle manager."""
            return agents["Tyril"]
        def handoff_to_tray() -> Agent:
            """Delegate to Tray, the web data middle manager."""
            return agents["Tray"]
        def handoff_to_larry() -> Agent:
            """Delegate to Larry, the filesystem minion."""
            return agents["Larry"]
        def handoff_to_kriegs() -> Agent:
            """Delegate to Kriegs, the database updates minion."""
            return agents["Kriegs"]
        def handoff_to_vanna() -> Agent:
            """Delegate to Vanna, the web search/fetch minion."""
            return agents["Vanna"]
        def handoff_to_marcher() -> Agent:
            """Delegate to Marcher, the data processing/docs minion."""
            return agents["Marcher"]
        def handoff_back_to_valory() -> Agent:
            """Return control to Valory, the top-tier coordinator."""
            return agents["Valory"]
        def handoff_back_to_tyril() -> Agent:
            """Return control to Tyril, the database and filesystem manager."""
            return agents["Tyril"]
        def handoff_back_to_tray() -> Agent:
            """Return control to Tray, the web data manager."""
            return agents["Tray"]

        # Top Tier: Coordinator
        agents["Valory"] = Agent(
            name="Valory",
            instructions="You are Valory, the top-tier spy coordinator overseeing the tracking of free online services. Delegate tasks to middle managers: Tyril manages database and filesystem operations (delegating to Larry for filesystem tasks and Kriegs for SQLite updates), Tray manages web data operations (delegating to Vanna for search/fetch and Marcher for processing/docs).",
            functions=[handoff_to_tyril, handoff_to_tray]
        )

        # Middle Managers
        agents["Tyril"] = Agent(
            name="Tyril",
            instructions="You are Tyril, the middle manager for database and filesystem operations. Delegate tasks to minions: Larry uses filesystem MCP server to manage temporary files at ALLOWED_PATH, Kriegs uses sqlite MCP server to perform CRUD operations on the 'services' table at SQLITE_DB_PATH with schema (id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, url TEXT, api_key TEXT, usage_limits TEXT, documentation_link TEXT). Handoff back to Valory when complete.",
            mcp_servers=["sqlite"],
            env_vars={"SQLITE_DB_PATH": sqlite_db_path},
            functions=[handoff_to_larry, handoff_to_kriegs, handoff_back_to_valory]
        )
        agents["Tray"] = Agent(
            name="Tray",
            instructions="You are Tray, the middle manager for web data operations. Delegate tasks to minions: Vanna uses brave-search and mcp-npx-fetch to locate and fetch data about free online services (e.g., Fly.io, Grok), Marcher uses mcp-doc-forge to process fetched data into a standardized format (name, type, url, api_key, usage_limits, documentation_link). Handoff back to Valory when complete.",
            mcp_servers=["brave-search"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
            functions=[handoff_to_vanna, handoff_to_marcher, handoff_back_to_valory]
        )

        # Minions under Tyril
        agents["Larry"] = Agent(
            name="Larry",
            instructions="You are Larry, a filesystem minion under Tyril. Use the filesystem MCP server at ALLOWED_PATH to manage temporary files for free online service data (e.g., storing fetched content from Vanna via Tyril before Kriegs updates the database). Kriegs handles SQLite CRUD operations, while Vanna and Marcher (under Tray) handle web data fetching and processing. Handoff back to Tyril when complete.",
            mcp_servers=["filesystem"],
            env_vars={"ALLOWED_PATH": allowed_path},
            functions=[handoff_back_to_tyril]
        )
        agents["Kriegs"] = Agent(
            name="Kriegs",
            instructions="You are Kriegs, a database minion under Tyril. Use the sqlite MCP server to perform CRUD operations (create, read, update, delete) on the 'services' table at SQLITE_DB_PATH with schema (id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, url TEXT, api_key TEXT, usage_limits TEXT, documentation_link TEXT) to manage details of free online services (e.g., Fly.io for container hosting, Grok for AI inference). Receive processed data from Marcher via Tyril, update the database, and handoff back to Tyril. Larry handles filesystem tasks under Tyril, while Vanna and Marcher (under Tray) fetch and process web data.",
            mcp_servers=["sqlite"],
            env_vars={"SQLITE_DB_PATH": sqlite_db_path},
            functions=[handoff_back_to_tyril]
        )

        # Minions under Tray
        agents["Vanna"] = Agent(
            name="Vanna",
            instructions="You are Vanna, a web minion under Tray. Use brave-search to locate free online services (e.g., Fly.io for container hosting, Grok for AI inference) and mcp-npx-fetch to retrieve detailed web content or API documentation from their URLs. Handoff fetched data to Marcher for processing, who then passes it to Kriegs via Tray for database updates. Kriegs and Larry (under Tyril) handle database and filesystem tasks. Handoff back to Tray when complete.",
            mcp_servers=["brave-search", "mcp-npx-fetch"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
            functions=[handoff_to_marcher, handoff_back_to_tray]
        )
        agents["Marcher"] = Agent(
            name="Marcher",
            instructions="You are Marcher, a web minion under Tray. Receive fetched data from Vanna, use mcp-doc-forge to process it into a standardized format (extracting name, type, url, api_key if applicable, usage_limits, documentation_link), and handoff the processed data to Kriegs via Tray for database updates. Vanna fetches data using brave-search and mcp-npx-fetch, while Kriegs (under Tyril) updates the SQLite database and Larry manages filesystem tasks. Handoff back to Tray when complete.",
            mcp_servers=["mcp-doc-forge"],
            env_vars={},
            functions=[handoff_to_kriegs, handoff_back_to_tray]
        )

        self.set_starting_agent(agents["Valory"])
        logger.info("Agents created: Valory, Tyril, Tray, Larry, Kriegs, Vanna, Marcher.")
        return agents

if __name__ == "__main__":
    WhiskeyTangoFoxtrotBlueprint.main()
