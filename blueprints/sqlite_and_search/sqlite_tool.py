# src/open_swarm_mcp/examples/mcp/sqlite_and_search/sqlite_tool.py

from typing import List, Dict, Any
import sqlite3
import json

class SQLiteTool:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a SQL query and returns the results as a list of dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            # Convert rows to list of dictionaries
            results = [dict(row) for row in rows]
            return results
        except sqlite3.Error as e:
            return [{"error": str(e)}]

    def get_tool_info(self) -> Dict[str, Any]:
        """
        Returns metadata about the tool.
        """
        return {
            "name": "SQLiteTool",
            "description": "A tool to execute SQL queries on a SQLite database.",
            "actions": ["execute_query"]
        }
