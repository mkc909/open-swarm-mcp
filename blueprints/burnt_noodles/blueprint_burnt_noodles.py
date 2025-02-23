import logging
import subprocess
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

class BurntNoodlesBlueprint(BlueprintBase):
    """Burnt Noodles - A blazing team igniting creative sparks with functions and flair."""
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "title": "Burnt Noodles",
            "description": "A sizzling team on a mission: led by Michael Toasted, with Fiona Flame and Sam Ashes igniting creativity.",
            "required_mcp_servers": [],
            "env_vars": []
        }

    def handoff_to_michael(self) -> Agent:
        """Hands off task execution to Michael Toasted.

        Returns:
            Agent: The Michael Toasted agent instance.
        """
        return self.swarm.agents["Michael Toasted"]

    def handoff_to_fiona(self) -> Agent:
        """Hands off task execution to Fiona Flame.

        Returns:
            Agent: The Fiona Flame agent instance.
        """
        return self.swarm.agents["Fiona Flame"]

    def handoff_to_sam(self) -> Agent:
        """Hands off task execution to Sam Ashes.

        Returns:
            Agent: The Sam Ashes agent instance.
        """
        return self.swarm.agents["Sam Ashes"]

    def git_status(self) -> str:
        """Executes 'git status' and returns the current repository status.

        Returns:
            str: Output of the git status command.

        Raises:
            subprocess.CalledProcessError: If the git command fails.
        """
        try:
            result = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing git status: {e.stderr}"

    def git_diff(self) -> str:
        """Executes 'git diff' and returns the differences in the working directory.

        Returns:
            str: Output of the git diff command.

        Raises:
            subprocess.CalledProcessError: If the git command fails.
        """
        try:
            result = subprocess.run(["git", "diff"], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing git diff: {e.stderr}"

    def git_add(self, file_path: str = ".") -> str:
        """Executes 'git add' to stage changes for the specified file or all changes.

        Args:
            file_path (str): The file or directory to add (defaults to '.' for all changes).

        Returns:
            str: Output of the git add command.

        Raises:
            subprocess.CalledProcessError: If the git command fails.
        """
        try:
            result = subprocess.run(["git", "add", file_path], capture_output=True, text=True, check=True)
            return result.stdout or "Files staged successfully."
        except subprocess.CalledProcessError as e:
            return f"Error executing git add: {e.stderr}"

    def git_commit(self, message: str = "Update") -> str:
        """Executes 'git commit' with a provided commit message.

        Args:
            message (str): The commit message (defaults to 'Update').

        Returns:
            str: Output of the git commit command.

        Raises:
            subprocess.CalledProcessError: If the git command fails.
        """
        try:
            result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing git commit: {e.stderr}"

    def git_push(self) -> str:
        """Executes 'git push' to push staged commits to the remote repository.

        Returns:
            str: Output of the git push command.

        Raises:
            subprocess.CalledProcessError: If the git command fails.
        """
        try:
            result = subprocess.run(["git", "push"], capture_output=True, text=True, check=True)
            return result.stdout or "Push completed successfully."
        except subprocess.CalledProcessError as e:
            return f"Error executing git push: {e.stderr}"

    def run_npm_test(self, args: str = "") -> str:
        """Executes 'npm run test' with optional arguments.

        Args:
            args (str): Additional arguments for the npm test command (default is empty).

        Returns:
            str: Output of the npm test command.

        Raises:
            subprocess.CalledProcessError: If the npm command fails.
        """
        try:
            cmd = ["npm", "run", "test"] + (args.split() if args else [])
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing npm run test: {e.stderr}"

    def run_pytest(self, args: str = "") -> str:
        """Executes 'uv run pytest' with optional arguments.

        Args:
            args (str): Additional arguments for the pytest command (default is empty).

        Returns:
            str: Output of the pytest command.

        Raises:
            subprocess.CalledProcessError: If the pytest command fails.
        """
        try:
            cmd = ["uv", "run", "pytest"] + (args.split() if args else [])
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing uv run pytest: {e.stderr}"

    def create_agents(self) -> Dict[str, Agent]:
        def create_agent(name: str, instructions: str, functions: list = []) -> Agent:
            return Agent(
                name=name,
                instructions=lambda ctx: instructions,
                functions=functions
            )
        agents = {}
        agents["Michael Toasted"] = create_agent(
            "Michael Toasted",
            "You are Michael Toasted, the resolute leader of Burnt Noodles. Oversee all operations with clarity. Be fully aware that Fiona Flame executes precise git commands (status, diff, add, commit, push) and Sam Ashes runs comprehensive tests (npm run test, uv run pytest). Delegate tasks to them as appropriate, and handle tasks beyond their scopes yourself.",
            [self.handoff_to_fiona, self.handoff_to_sam]
        )
        agents["Fiona Flame"] = create_agent(
            "Fiona Flame",
            "You are Fiona Flame, the brilliant strategist responsible for executing git commands. When processing files, produce a one-line conventional commit per file – stage and iteratively refine changes. If a git task exceeds your scope, hand off back to Michael Toasted, and delegate unit testing to Sam Ashes when needed.",
            [self.git_status, self.git_diff, self.git_add, self.git_commit, self.git_push, self.handoff_to_michael, self.handoff_to_sam]
        )
        agents["Sam Ashes"] = create_agent(
            "Sam Ashes",
            "You are Sam Ashes, the agile operative tasked with executing testing commands. Run compact tests until the first failure occurs; if all tests pass, immediately run a coverage report (e.g., 'uv run pytest --cov') and analyze the results to suggest improvements. For tasks outside testing, hand off back to Michael Toasted, or delegate to Fiona Flame if related to code changes.",
            [self.run_npm_test, self.run_pytest, self.handoff_to_michael, self.handoff_to_fiona]
        )
        self.set_starting_agent(agents["Michael Toasted"])
        logger.info("Agents created: Michael Toasted, Fiona Flame, Sam Ashes.")
        return agents

if __name__ == "__main__":
    BurntNoodlesBlueprint.main()