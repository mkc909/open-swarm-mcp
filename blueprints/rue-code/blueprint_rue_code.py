"""
Rue-Code: Automated Development Team Blueprint

This blueprint sets up an automated task-oriented coding assistant team with specialized agents for coordination, code development, system architecture, and unit testing/git management.

This blueprint now includes full implementations of core functions from the previous Roo-Code project.
"""

import os
import re
import logging
import subprocess
from typing import Dict, Any, List

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

# Full Implementations of Core Functions from Roo-Code

def execute_command(command: str) -> None:
    """
    Executes a CLI command and logs its output.
    """
    try:
        logger.debug(f"Executing command: {command}")
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.debug(f"Command output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")

def read_file(path: str) -> str:
    """
    Reads the content of a file located at 'path'.
    """
    try:
        logger.debug(f"Reading file at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"Error reading file at {path}: {e}")
        return ""

def write_to_file(path: str, content: str) -> None:
    """
    Writes 'content' to a file at 'path'. Overwrites any existing content.
    """
    try:
        logger.debug(f"Writing to file at: {path}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug("Write successful.")
    except Exception as e:
        logger.error(f"Error writing to file at {path}: {e}")

def write_md_file(path: str, content: str) -> None:
    """
    Writes 'content' to a Markdown file at 'path'. Only allows writing to files ending with '.md'.
    """
    if not path.endswith(".md"):
        logger.error(f"Architect can only write to Markdown files (*.md): {path}")
        return
    write_to_file(path, content)

def apply_diff(path: str, search: str, replace: str) -> None:
    """
    Applies a simple diff by replacing occurrences of 'search' with 'replace' in the file at 'path'.
    """
    try:
        logger.debug(f"Applying diff in file at: {path}")
        original = read_file(path)
        if not original:
            logger.error("Original content empty; diff not applied.")
            return
        updated = original.replace(search, replace)
        write_to_file(path, updated)
        logger.debug("Diff applied successfully.")
    except Exception as e:
        logger.error(f"Error applying diff in file at {path}: {e}")

def search_files(directory: str, pattern: str) -> List[str]:
    """
    Searches for files in 'directory' whose contents match the regex 'pattern'.
    Returns a list of file paths that contain a match.
    """
    matches = []
    regex = re.compile(pattern)
    logger.debug(f"Searching for pattern: {pattern} in directory: {directory}")
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if regex.search(content):
                    matches.append(file_path)
                    logger.debug(f"Match found in: {file_path}")
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
    return matches

def list_files(directory: str) -> List[str]:
    """
    Lists all file paths (relative to 'directory') recursively.
    """
    file_list = []
    logger.debug(f"Listing files in directory: {directory}")
    for root, dirs, files in os.walk(directory):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), directory)
            file_list.append(relative_path)
    return file_list

def run_test_command(command: str) -> None:
    """
    Runs a test command, limited to 'npm test' and 'uv run pytest'.
    """
    allowed_commands = ["npm test", "uv run pytest"]
    if command.strip() in allowed_commands:
        execute_command(command)
    else:
        logger.error("UnitTestingGit is limited to 'npm test' and 'uv run pytest' commands.")

# Map of tool names to their implementations
TOOLS = {
    "execute_command": execute_command,
    "read_file": read_file,
    "write_to_file": write_to_file,       # Full write for Code agent.
    "write_md_file": write_md_file,         # Restricted write for Architect.
    "apply_diff": apply_diff,
    "search_files": search_files,
    "list_files": list_files,
    "run_test_command": run_test_command,   # Limited test command runner for UnitTestingGit.
}


class RueCodeBlueprint(BlueprintBase):
    """
    Rue-Code Blueprint for automated development tasks.

    Agents:
      - Coordinator: Central agent managing task delegation with persistent memory.
      - Code: Responsible for coding (full write allowed); Other agents available: Architect (design, web search, writes Markdown), UnitTestingGit (runs tests: 'npm test' or 'uv run pytest').
      - Architect: Provides design guidance and web search; can only write Markdown (*.md) files; Other agents available: Code (full coding), UnitTestingGit (runs tests).
      - UnitTestingGit: Runs test commands limited to 'npm test' and 'uv run pytest'; Other agents available: Code (full coding), Architect (design, Markdown writing).
    
    This blueprint implements core functions (execute_command, read_file, write_to_file, write_md_file,
    apply_diff, search_files, list_files, run_test_command) from the previous Roo-Code project.
    """
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "Rue-Code: Automated Development Team Blueprint",
            "description": (
                "An automated task-oriented coding assistant team featuring a Coordinator with persistent memory, "
                "a Code agent for full-scale development, an Architect for design support and web search (Markdown-only writing), "
                "and a UnitTestingGit agent for running tests ('npm test' and 'uv run pytest'). "
                "This blueprint integrates core functions from the previous Roo-Code project."
            ),
            "required_mcp_servers": [
                "memory",
                "brave-search"
            ],
            "env_vars": [
                "BRAVE_API_KEY"
            ],
        }

    def create_agents(self) -> Dict[str, Agent]:
        # Retrieve environment variables
        brave_api_key = os.getenv("BRAVE_API_KEY", "default-brave-key")

        agents: Dict[str, Agent] = {}

        # Coordinator: central agent responsible for delegating tasks.
        coordinator_instructions = (
            "You are the Coordinator, managing task delegation with persistent memory. "
            "Delegate tasks to Code, Architect, or UnitTestingGit. "
            "Available agents: Code (full coding), Architect (design, web search, Markdown writing), UnitTestingGit (runs tests)."
        )
        agents["Coordinator"] = Agent(
            name="Coordinator",
            instructions=coordinator_instructions,
            mcp_servers=["memory"],
            env_vars={}
        )

        # Code: full coding capability.
        code_instructions = (
            "You are the Code agent, the specialist for writing, modifying, and analyzing code with full write access. "
            "Use tools: execute_command, read_file, write_to_file, apply_diff, and list_files. "
            "Available agents: Architect (for design and Markdown writing), UnitTestingGit (for test execution)."
        )
        agents["Code"] = Agent(
            name="Code",
            instructions=code_instructions,
            mcp_servers=["memory"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
        )

        # Architect: design and web search; Markdown-only writing.
        architect_instructions = (
            "You are the Architect, providing design guidance, architectural planning, and web search capabilities via search_files. "
            "Use tools: search_files, list_files, read_file, and write_md_file (Markdown files only). "
            "Available agents: Code (for full coding), UnitTestingGit (for test execution)."
        )
        agents["Architect"] = Agent(
            name="Architect",
            instructions=architect_instructions,
            mcp_servers=["brave-search"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
        )

        # UnitTestingGit: limited to running test commands.
        unit_testing_git_instructions = (
            "You are the UnitTestingGit agent, responsible for running tests. Use tool: run_test_command which is limited to 'npm test' or 'uv run pytest'. "
            "Available agents: Code (for full coding) and Architect (for design and Markdown writing)."
        )
        agents["UnitTestingGit"] = Agent(
            name="UnitTestingGit",
            instructions=unit_testing_git_instructions,
            mcp_servers=["memory"],
            env_vars={}
        )

        # Assign tool sets to agents using object.__setattr__ to bypass pydantic restrictions

        object.__setattr__(agents["Coordinator"], "tools", {})
        object.__setattr__(agents["Code"], "tools", {
            "execute_command": TOOLS["execute_command"],
            "read_file": TOOLS["read_file"],
            "write_to_file": TOOLS["write_to_file"],
            "apply_diff": TOOLS["apply_diff"],
            "list_files": TOOLS["list_files"],
        })
        object.__setattr__(agents["Architect"], "tools", {
            "search_files": TOOLS["search_files"],
            "list_files": TOOLS["list_files"],
            "read_file": TOOLS["read_file"],
            "write_md_file": TOOLS["write_md_file"],
        })
        object.__setattr__(agents["UnitTestingGit"], "tools", {
            "run_test_command": TOOLS["run_test_command"],
        })

        # Handoff Functions: Coordinator delegates tasks to specialized agents,
        # and each specialized agent returns control back to the Coordinator.
        def handoff_back_to_coordinator() -> Agent:
            return agents["Coordinator"]

        agents["Coordinator"].functions = [
            lambda: agents["Code"],
            lambda: agents["Architect"],
            lambda: agents["UnitTestingGit"]
        ]

        for agent_name in ["Code", "Architect", "UnitTestingGit"]:
            agents[agent_name].functions = [handoff_back_to_coordinator]

        self.set_starting_agent(agents["Coordinator"])
        logger.debug(f"Agents registered: {list(agents.keys())}")
        return agents


if __name__ == "__main__":
    RueCodeBlueprint.main()