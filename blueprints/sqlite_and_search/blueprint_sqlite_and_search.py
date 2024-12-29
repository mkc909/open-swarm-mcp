# blueprints/sqlite_and_search/blueprint_sqlite_and_search.py

"""
SQLite and Search Integration Blueprint

This blueprint integrates SQLite database querying with search capabilities via MCP servers.
It includes a Triage Agent that delegates tasks to a WebResearchAgent and a DatabaseAgent.
"""

import json
import os
import asyncio
import logging
from typing import Dict, Any, Optional

from swarm import Agent, Swarm
from swarm.repl import run_demo_loop
from open_swarm_mcp.blueprint_base import BlueprintBase
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from concurrent.futures import ThreadPoolExecutor
import sys
import traceback

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for extensive logging
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

CONFIG_FILE = 'mcp_server_config.json'  # Path to MCP server configuration file

def load_server_config(config_file: str = CONFIG_FILE) -> dict:
    """
    Load server configuration from the specified JSON config file.

    Args:
        config_file (str): Path to the MCP server configuration file.

    Returns:
        dict: Parsed server configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the config file contains invalid JSON.
        Exception: For any other unexpected errors.
    """
    logger.debug(f"Attempting to load server configuration from {config_file}.")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded server configuration from {config_file}.")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {config_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading {config_file}: {e}")
            raise
    else:
        logger.error(f"Config file {config_file} does not exist.")
        raise FileNotFoundError(f"Could not find config file {config_file}")

def create_server_parameters(server_config: dict, server_name: str) -> StdioServerParameters:
    """
    Create server parameters for a specific MCP server based on the configuration.

    Args:
        server_config (dict): The loaded MCP server configuration.
        server_name (str): The name of the MCP server.

    Returns:
        StdioServerParameters: The parameters for the MCP server.

    Raises:
        ValueError: If the server name is not found in the configuration.
    """
    logger.debug(f"Creating server parameters for '{server_name}'.")
    if server_name not in server_config.get("mcpServers", {}):
        logger.error(f"Server '{server_name}' not found in the configuration.")
        raise ValueError(f"Server '{server_name}' not found in the configuration.")

    config = server_config["mcpServers"][server_name]
    server_parameter = StdioServerParameters(
        command=config.get("command"),
        args=config.get("args", []),
        env={**config.get("env", {}), "PATH": os.getenv("PATH", "")}
    )
    logger.debug(f"Initial server parameters for '{server_name}': {server_parameter}")

    # Replace environment variable placeholders with actual values
    for key, value in server_parameter.env.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            substituted_value = os.getenv(var_name)
            if substituted_value:
                server_parameter.env[key] = substituted_value
                logger.debug(f"Substituted environment variable for '{key}': {substituted_value}")
            else:
                logger.warning(f"Environment variable '{var_name}' is not set. Using empty string for '{key}'.")
                server_parameter.env[key] = ""

    logger.info(f"Final server parameters for '{server_name}': {server_parameter}")
    logger.debug(f"After substitution, BRAVE_API_KEY for '{server_name}': {server_parameter.env.get('BRAVE_API_KEY')}")
    return server_parameter

class SQLiteSearchBlueprint(BlueprintBase):
    """
    SQLite and Search Integration Blueprint Implementation.
    Includes Triage, Web Research, and Database Agents.
    """

    def __init__(self):
        """
        Initialize the SQLiteSearchBlueprint with required metadata, MCP sessions, and agents.
        """
        self._metadata = {
            "title": "SQLite and Search Integration",
            "description": "Integrates SQLite database querying with search capabilities via MCP servers.",
            "required_mcp_servers": ["sqlite", "brave-search"],
            "env_vars": ["SQLITE_DB_PATH", "BRAVE_API_KEY"]
        }
        self.client = Swarm()
        self.mcp_sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.executor = ThreadPoolExecutor(max_workers=10)  # Adjust number of workers as needed
        logger.debug("Initialized SQLiteSearch Blueprint with Swarm.")

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Retrieve the blueprint's metadata.

        Returns:
            Dict[str, Any]: Metadata information.
        """
        return self._metadata

    def validate_env_vars(self) -> None:
        """
        Validate that required environment variables are set and that the SQLite database file exists.

        Raises:
            ValueError: If any required environment variable is missing or the SQLite database file does not exist.
        """
        logger.debug("Validating required environment variables.")
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        brave_api_key = os.getenv("BRAVE_API_KEY")

        if not sqlite_db_path:
            logger.error("Environment variable SQLITE_DB_PATH is not set.")
            raise ValueError("Environment variable SQLITE_DB_PATH is not set.")

        if not os.path.exists(sqlite_db_path):
            logger.error(f"SQLite database file does not exist at: {sqlite_db_path}")
            raise ValueError(f"SQLite database file does not exist at: {sqlite_db_path}")

        if not brave_api_key:
            logger.error("Environment variable BRAVE_API_KEY is not set.")
            raise ValueError("Environment variable BRAVE_API_KEY is not set.")

        logger.info("Validated SQLITE_DB_PATH and BRAVE_API_KEY environment variables.")
        logger.debug(f"SQLITE_DB_PATH: {sqlite_db_path}")
        logger.debug(f"BRAVE_API_KEY: {'***'}")  # Masking the actual API key in logs for security

    async def connect_to_mcp_servers(self):
        """
        Connect to the required MCP servers using configurations.

        Raises:
            Exception: If connecting to any MCP server fails.
        """
        logger.debug("Connecting to MCP servers.")
        try:
            server_config = load_server_config()
        except Exception as e:
            logger.error(f"Failed to load server configuration: {e}")
            raise

        required_servers = self._metadata["required_mcp_servers"]
        logger.debug(f"Required MCP servers: {required_servers}")

        for server_name in required_servers:
            try:
                server_params = create_server_parameters(server_config, server_name)
            except Exception as e:
                logger.error(f"Error creating server parameters for '{server_name}': {e}")
                raise

            # Enter the MCP client context
            try:
                logger.debug(f"Attempting to connect to MCP server '{server_name}'.")
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                read_stream, write_stream = stdio_transport
                logger.debug(f"Stdio transport for '{server_name}': {stdio_transport}")

                mcp_session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
                await mcp_session.initialize()
                self.mcp_sessions[server_name] = mcp_session
                logger.info(f"Connected to MCP server '{server_name}'.")
            except Exception as e:
                logger.error(f"Failed to connect to MCP server '{server_name}': {e}")
                traceback.print_exc()
                raise

    def create_agent(self) -> Dict[str, Agent]:
        """
        Create and configure the Triage, Web Research, and Database Agents with synchronous wrappers.

        Returns:
            Dict[str, Agent]: A dictionary containing all created agents.
        """
        logger.debug("Creating agents.")

        # Define Triage Agent
        triage_agent = Agent(
            name="TriageAgent",
            instructions="""You can delegate tasks to the WebResearchAgent or the DatabaseAgent.
Available operations include:
- Performing web research
- Querying the database
Please determine the appropriate agent based on the user's request.""",
            functions=[
                self.sync_delegate_task
            ],
            parallel_tool_calls=True
        )
        logger.info("Created TriageAgent.")

        # Define Web Research Agent
        web_research_agent = Agent(
            name="WebResearchAgent",
            instructions="""You can perform web searches using the Brave Search tool.
Available operations include:
- Performing a web search
Please ensure all searches are performed using the allowed search capabilities.""",
            functions=[
                self.sync_perform_search
            ],
            parallel_tool_calls=True
        )
        logger.info("Created WebResearchAgent.")

        # Define Database Agent
        database_agent = Agent(
            name="DatabaseAgent",
            instructions="""You can query the SQLite database.
Available operations include:
- Querying tables
- Searching records
Please ensure all database operations are optimized and secure.""",
            functions=[
                self.sync_query_table,
                self.sync_search_records
            ],
            parallel_tool_calls=True
        )
        logger.info("Created DatabaseAgent.")

        # Compile all agents into a dictionary
        agents = {
            "TriageAgent": triage_agent,
            "WebResearchAgent": web_research_agent,
            "DatabaseAgent": database_agent
        }
        logger.debug(f"Agents created: {list(agents.keys())}")
        return agents

    def get_agents(self) -> Dict[str, Agent]:
        """
        Retrieve the dictionary of agents.

        Returns:
            Dict[str, Agent]: A dictionary containing all agents.
        """
        logger.debug("Fetching agents.")
        return self.create_agent()

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        logger.debug("Executing blueprint.")
        self.validate_env_vars()

        # Run connect_to_mcp_servers in the event loop using executor
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.debug("Event loop is already running. Scheduling connect_to_mcp_servers.")
                task = asyncio.ensure_future(self.connect_to_mcp_servers())
                loop.run_until_complete(task)
            else:
                logger.debug("Event loop is not running. Running connect_to_mcp_servers with asyncio.run.")
                asyncio.run(self.connect_to_mcp_servers())
        except Exception as e:
            logger.error(f"Error during MCP server connection: {e}")
            traceback.print_exc()
            return {
                "status": "failure",
                "messages": [f"Error connecting to MCP servers: {e}"],
                "metadata": self.metadata
            }

        agents = self.create_agent()

        # Allow for message override from framework config
        default_message = {
            "role": "user",
            "content": "I need to find information about OpenAI's latest models."
        }
        messages = config.get('messages', [default_message]) if config else [default_message]
        logger.debug(f"Messages to send: {messages}")

        # Run the triage agent
        try:
            logger.debug("Running TriageAgent with messages.")
            response = self.client.run(agent=agents["TriageAgent"], messages=messages)
            logger.debug(f"TriageAgent response: {response.messages}")
        except Exception as e:
            logger.error(f"Error running TriageAgent: {e}")
            traceback.print_exc()
            return {
                "status": "failure",
                "messages": [f"Error running TriageAgent: {e}"],
                "metadata": self.metadata
            }

        return {
            "status": "success",
            "messages": response.messages,
            "metadata": self.metadata
        }

    def interactive_mode(self) -> None:
        """
        Use Swarm's REPL loop, starting with the TriageAgent.
        """
        logger.debug("Entering interactive mode.")
        try:
            # Run the asynchronous interactive mode in the executor
            logger.debug("Submitting interactive mode to executor.")
            future = self.executor.submit(asyncio.run, self._interactive_mode_async())
            future.result()
            logger.debug("Interactive mode completed.")
        except Exception as e:
            logger.error(f"Error during interactive mode: {e}")
            traceback.print_exc()
            print(f"Error during interactive mode: {e}")

    async def _interactive_mode_async(self) -> None:
        """
        Asynchronous helper for interactive_mode.
        Connects to MCP servers and starts the demo loop with the TriageAgent.
        """
        logger.debug("Starting asynchronous interactive mode.")
        await self.connect_to_mcp_servers()
        agents = self.create_agent()
        logger.debug(f"Starting demo loop with agent: {agents['TriageAgent'].name}")
        run_demo_loop(starting_agent=agents["TriageAgent"])
        logger.debug("Demo loop ended.")

    # Synchronous wrappers for asynchronous operations

    def sync_delegate_task(self, user_input: str) -> str:
        """
        Delegate the task to the appropriate agent based on user input.

        Args:
            user_input (str): The user's request.

        Returns:
            str: The agent's response.
        """
        logger.debug(f"Sync delegate_task called with user_input: {user_input}")
        try:
            # Set a timeout of 10 seconds for the delegate_task
            return self.executor.submit(
                asyncio.run,
                asyncio.wait_for(self.delegate_task(user_input), timeout=10)
            ).result()
        except asyncio.TimeoutError:
            logger.error("delegate_task timed out after 10 seconds.")
            return "Error: The request timed out while delegating the task."
        except Exception as e:
            logger.error(f"Sync delegate_task failed: {e}")
            traceback.print_exc()
            return f"Error delegating task: {e}"

    def sync_perform_search(self, query: str) -> str:
        """
        Perform a web search using the WebResearchAgent.

        Args:
            query (str): The search query.

        Returns:
            str: Search results or error message.
        """
        logger.debug(f"Sync perform_search called with query: {query}")
        try:
            # Set a timeout of 10 seconds for the perform_search
            return self.executor.submit(
                asyncio.run,
                asyncio.wait_for(self.perform_search(query), timeout=10)
            ).result()
        except asyncio.TimeoutError:
            logger.error("perform_search timed out after 10 seconds.")
            return "Error: The web search timed out."
        except Exception as e:
            logger.error(f"Sync perform_search failed: {e}")
            traceback.print_exc()
            return f"Error performing search: {e}"

    def sync_query_table(self, table_name: str) -> str:
        """
        Query all records from the specified table using the DatabaseAgent.

        Args:
            table_name (str): Name of the table to query.

        Returns:
            str: Query results or error message.
        """
        logger.debug(f"Sync query_table called with table_name: {table_name}")
        try:
            # Set a timeout of 10 seconds for the query_table
            return self.executor.submit(
                asyncio.run,
                asyncio.wait_for(self.query_table(table_name), timeout=10)
            ).result()
        except asyncio.TimeoutError:
            logger.error("query_table timed out after 10 seconds.")
            return f"Error: Querying table '{table_name}' timed out."
        except Exception as e:
            logger.error(f"Sync query_table failed: {e}")
            traceback.print_exc()
            return f"Error querying table '{table_name}': {e}"

    def sync_search_records(self, search_term: str) -> str:
        """
        Search records in the SQLite database that match the search term using the DatabaseAgent.

        Args:
            search_term (str): Term to search for in the records.

        Returns:
            str: Search results or error message.
        """
        logger.debug(f"Sync search_records called with search_term: {search_term}")
        try:
            # Set a timeout of 10 seconds for the search_records
            return self.executor.submit(
                asyncio.run,
                asyncio.wait_for(self.search_records(search_term), timeout=10)
            ).result()
        except asyncio.TimeoutError:
            logger.error("search_records timed out after 10 seconds.")
            return f"Error: Searching records with term '{search_term}' timed out."
        except Exception as e:
            logger.error(f"Sync search_records failed: {e}")
            traceback.print_exc()
            return f"Error searching records with term '{search_term}': {e}"

    # Asynchronous agent functions

    async def delegate_task(self, user_input: str) -> str:
        """
        Determine which agent to delegate the task to based on user input.

        Args:
            user_input (str): The user's request.

        Returns:
            str: The agent's response.
        """
        logger.debug(f"delegate_task called with user_input: {user_input}")
        try:
            user_input_lower = user_input.lower()
            logger.debug(f"Processed user_input_lower: {user_input_lower}")

            if any(keyword in user_input_lower for keyword in ["search", "find", "research"]):
                # Delegate to WebResearchAgent
                query = user_input  # Adjust as needed to extract the actual query
                logger.debug(f"Delegating to WebResearchAgent with query: {query}")

                # Check if 'brave-search' MCP session is active
                if "brave-search" not in self.mcp_sessions:
                    logger.error("brave-search MCP session is not active.")
                    return "WebResearchAgent is not available."

                response = await self.mcp_sessions["brave-search"].call_tool("perform_search", {"query": query})
                logger.debug(f"WebResearchAgent response: {response.content}")

                if not response.content:
                    logger.warning("WebResearchAgent returned no content.")
                    return "No results found from web research."

                results = response.content[0].text if response.content[0].text else "No results returned."
                logger.info("Delegated task to WebResearchAgent.")
                logger.debug(f"Web Research Results: {results}")
                return f"Web Research Results:\n{results}"

            elif any(keyword in user_input_lower for keyword in ["query", "find", "record"]):
                # Delegate to DatabaseAgent
                logger.debug("Delegating to DatabaseAgent.")
                if "from the" in user_input_lower:
                    # Example: "Query all records from the 'users' table."
                    try:
                        table_part = user_input_lower.split("from the")[1].strip()
                        table_name = table_part.strip("'\"").split(" ")[0]
                        logger.debug(f"Extracted table_name: {table_name}")

                        # Check if 'sqlite' MCP session is active
                        if "sqlite" not in self.mcp_sessions:
                            logger.error("sqlite MCP session is not active.")
                            return "DatabaseAgent is not available."

                        response = await self.mcp_sessions["sqlite"].call_tool("query_table", {"table_name": table_name})
                        logger.debug(f"DatabaseAgent query_table response: {response.content}")

                        if not response.content:
                            logger.warning("DatabaseAgent returned no content for query_table.")
                            return f"No records found in table '{table_name}'."

                        records = response.content[0].text if response.content[0].text else "No records found."
                        logger.info("Delegated task to DatabaseAgent for table query.")
                        logger.debug(f"Database Query Results: {records}")
                        return f"Database Query Results:\n{records}"
                    except (IndexError, ValueError) as e:
                        logger.error(f"Error parsing table name: {e}")
                        traceback.print_exc()
                        return "Please specify the table name in your query."
                elif "search for" in user_input_lower:
                    # Example: "Search for 'Alice' in the database."
                    try:
                        search_term = user_input_lower.split("search for")[1].strip().strip("'\"")
                        logger.debug(f"Extracted search_term: {search_term}")

                        # Check if 'sqlite' MCP session is active
                        if "sqlite" not in self.mcp_sessions:
                            logger.error("sqlite MCP session is not active.")
                            return "DatabaseAgent is not available."

                        response = await self.mcp_sessions["sqlite"].call_tool("search_records", {"search_term": search_term})
                        logger.debug(f"DatabaseAgent search_records response: {response.content}")

                        if not response.content:
                            logger.warning("DatabaseAgent returned no content for search_records.")
                            return f"No records found matching '{search_term}'."

                        results = response.content[0].text if response.content[0].text else "No records found."
                        if results:
                            logger.info(f"Found records matching '{search_term}'.")
                            logger.debug(f"Database Search Results: {results}")
                            return f"Database Search Results:\n{results}"
                        else:
                            logger.info(f"No records found matching '{search_term}'.")
                            logger.debug("No records found in database search.")
                            return f"No records found matching '{search_term}'."
                    except (IndexError, ValueError) as e:
                        logger.error(f"Error parsing search term: {e}")
                        traceback.print_exc()
                        return "Please specify the search term."
                else:
                    logger.warning("Unable to determine how to process the request.")
                    return "Unable to determine how to process your request. Please specify a table name or search term."
            else:
                logger.warning("Unrecognized command.")
                return "I'm sorry, I didn't understand your request. Please try again."
        except Exception as e:
            logger.error(f"Error in delegate_task: {e}")
            traceback.print_exc()
            return f"Error delegating task: {e}"

    async def perform_search(self, query: str) -> str:
        """
        Perform a web search using the Brave Search MCP server.

        Args:
            query (str): The search query.

        Returns:
            str: Search results or error message.
        """
        logger.debug(f"perform_search called with query: {query}")
        try:
            if "brave-search" not in self.mcp_sessions:
                logger.error("brave-search MCP session is not active.")
                return "WebResearchAgent is not available."

            response = await self.mcp_sessions["brave-search"].call_tool("perform_search", {"query": query})
            logger.debug(f"Brave Search response: {response.content}")

            if not response.content:
                logger.warning("Brave Search returned no content.")
                return "No results found from web research."

            results = response.content[0].text if response.content[0].text else "No results returned."
            logger.info(f"Performed web search for query: {query}")
            logger.debug(f"Search Results: {results}")
            return f"Search Results:\n{results}"
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            traceback.print_exc()
            return f"Error performing web search: {e}"

    async def query_table(self, table_name: str) -> str:
        """
        Query all records from the specified table in the SQLite database.

        Args:
            table_name (str): Name of the table to query.

        Returns:
            str: Query results or error message.
        """
        logger.debug(f"query_table called with table_name: {table_name}")
        try:
            if "sqlite" not in self.mcp_sessions:
                logger.error("sqlite MCP session is not active.")
                return "DatabaseAgent is not available."

            response = await self.mcp_sessions["sqlite"].call_tool("query_table", {"table_name": table_name})
            logger.debug(f"SQLite query_table response: {response.content}")

            if not response.content:
                logger.warning("SQLite query_table returned no content.")
                return f"No records found in table '{table_name}'."

            records = response.content[0].text if response.content[0].text else "No records found."
            logger.info(f"Queried table '{table_name}' successfully.")
            logger.debug(f"Records from '{table_name}': {records}")
            return f"Records from '{table_name}':\n{records}"
        except Exception as e:
            error_msg = f"Error querying table '{table_name}': {e}"
            logger.error(error_msg)
            traceback.print_exc()
            return error_msg

    async def search_records(self, search_term: str) -> str:
        """
        Search records in the SQLite database that match the search term.

        Args:
            search_term (str): Term to search for in the records.

        Returns:
            str: Search results or error message.
        """
        logger.debug(f"search_records called with search_term: {search_term}")
        try:
            if "sqlite" not in self.mcp_sessions:
                logger.error("sqlite MCP session is not active.")
                return "DatabaseAgent is not available."

            response = await self.mcp_sessions["sqlite"].call_tool("search_records", {"search_term": search_term})
            logger.debug(f"SQLite search_records response: {response.content}")

            if not response.content:
                logger.warning("SQLite search_records returned no content.")
                return f"No records found matching '{search_term}'."

            results = response.content[0].text if response.content[0].text else "No records found."
            if results:
                logger.info(f"Found records matching '{search_term}'.")
                logger.debug(f"Search results for '{search_term}': {results}")
                return f"Search results for '{search_term}':\n{results}"
            else:
                logger.info(f"No records found matching '{search_term}'.")
                logger.debug("No records found in database search.")
                return f"No records found matching '{search_term}'."
        except Exception as e:
            error_msg = f"Error searching records with term '{search_term}': {e}"
            logger.error(error_msg)
            traceback.print_exc()
            return error_msg

# Entry point for standalone execution
if __name__ == "__main__":
    blueprint = SQLiteSearchBlueprint()
    try:
        blueprint.interactive_mode()
    except Exception as e:
        logger.error(f"Error running SQLiteSearch Blueprint: {e}")
        traceback.print_exc()
        print(f"Error running SQLiteSearch Blueprint: {e}")
