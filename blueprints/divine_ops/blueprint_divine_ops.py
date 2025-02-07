"""
Massive Software Development & Sysadmin Team Blueprint

Combines:
- A software development team (Product Owner, Software Architect, Tech Lead, Full Stack Implementer,
  Code Monkey, Code Updater, DevOps, Technical Writer) and
- An advanced sysadmin pantheon (Zeus, Hephaestus, Hermes, Odin, Thoth, Hecate, Mnemosyne, Chronos)

We marry each "god" to one dev role to create 8 specialized agents, plus
Zeus as the central Triage/Coordinator (and also Product Owner).

All relevant MCP servers from both the Personal Assistant and Sysadmin advanced blueprints
are included. Env vars from both sets are listed for completeness.
"""

import os
import logging
from typing import Dict, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class MassiveSoftwareDevSysadminBlueprint(BlueprintBase):
    """
    A blueprint defining a massive software development & sysadmin team:

      1. Zeus (Product Owner) - Central triage, manages entire process & memory.
      2. Odin (Software Architect) - Designs architecture using 'rag-docs' and advanced references.
      3. Hermes (Tech Lead) - Breaks project into tasks, delegates, uses shell as needed.
      4. Hephaestus (Full Stack Implementer) - Writes clean code, uses filesystem & installer tools.
      5. Hecate (Code Monkey) - Another full stack implementer, helps with coding tasks.
      6. Thoth (Code Updater) - Maintains code updates and DB ops with SQLite.
      7. Mnemosyne (DevOps) - Infrastructure, pipelines, memory management, installations, etc.
      8. Chronos (Technical Writer) - Documents everything, organizes knowledge, sequential planning.

    Each agent has specific MCP servers mapped to their domain of responsibility.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Provides blueprint metadata:
         - Title
         - Description
         - Required MCP servers
         - Environment variables
        """
        return {
            "title": "Massive Software Dev & Sysadmin Team Blueprint",
            "description": (
                "Zeus leads a pantheon of specialized developer/sysadmin agents, each performing "
                "unique tasks with the help of various MCP servers. This includes product ownership, "
                "architecture, tech leadership, full-stack coding, code updates, DevOps, and technical "
                "writing. Also covers advanced sysadmin tasks like filesystem, shell, search, "
                "database operations, deployment, memory management, sequential planning, and doc retrieval."
            ),
            "required_mcp_servers": [
                # From Sysadmin blueprint:
                "filesystem",
                "brave-search",
                "sqlite",
                "mcp-installer",
                "memory",
                "mcp-shell",
                "sequential-thinking",
                # From Personal Assistant blueprint:
                "rag-docs",
                "duckduckgo-search",
                "mcp-server-reddit",
                "claudeus-wp-mcp",
            ],
            "env_vars": [
                # From Sysadmin blueprint:
                "ALLOWED_PATH",
                "BRAVE_API_KEY",
                "SQLITE_DB_PATH",
                # From Personal Assistant blueprint:
                "WEATHER_API_KEY",
                "OPENAI_API_KEY",
                "QDRANT_URL",
                "QDRANT_API_KEY",
                "SERPAPI_API_KEY",
                "WP_SITES_PATH",
            ],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Creates and returns 8 specialized agents:
          - Zeus (Product Owner / Triage)
          - Odin (Software Architect)
          - Hermes (Tech Lead)
          - Hephaestus (Full Stack Implementer)
          - Hecate (Code Monkey)
          - Thoth (Code Updater)
          - Mnemosyne (DevOps)
          - Chronos (Technical Writer)
        Each agent references relevant role definitions and protocols from the user-provided JSON,
        combined with mythological names and specialized MCP server mappings.
        """

        # --- Retrieve environment variables (optional if needed) ---
        allowed_paths = os.getenv("ALLOWED_PATH", "/default/path")
        brave_api_key = os.getenv("BRAVE_API_KEY", "default-brave-key")
        sqlite_db_path = os.getenv("SQLITE_DB_PATH", "/tmp/sqlite.db")
        weather_api_key = os.getenv("WEATHER_API_KEY", "")
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        qdrant_url = os.getenv("QDRANT_URL", "")
        qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        serpapi_api_key = os.getenv("SERPAPI_API_KEY", "")
        wp_sites_path = os.getenv("WP_SITES_PATH", "")

        agents: Dict[str, Agent] = {}

        # ─────────────────────────────────────────────────────────────────────────
        # ZEUS (Product Owner) - central triage + memory
        # ─────────────────────────────────────────────────────────────────────────
        product_owner_instructions = (
            "You are Zeus, fulfilling the 'Product Owner' role:\n\n"
            "**RoleDefinition**: "
            "You are an experienced project owner (project manager) who manages the process of "
            "creating software applications from client specs to development. You act as if you're "
            "speaking to the client who wants their idea turned into reality.\n\n"
            "**Protocol** (Product Owner Protocol):\n"
            "1. Engage with clients to understand their vision and requirements thoroughly.\n"
            "2. Ask step-by-step questions to clarify all aspects of the project.\n"
            "3. Document and prioritize requirements by business value and feasibility.\n"
            "4. Break down complex requests into manageable specifications.\n"
            "5. Coordinate with the dev team to ensure accurate implementation.\n"
            "6. Monitor progress and align with client expectations.\n\n"
            "Plus, as the 'TriageAgent' from Sysadmin:\n"
            " - Oversee and delegate tasks to the pantheon of agents.\n"
            " - Do not execute tasks directly; manage order and memory.\n"
        )

        agents["Zeus"] = Agent(
            name="Zeus",
            instructions=product_owner_instructions,
            mcp_servers=["memory"],  # central memory usage
            env_vars={},
        )

        # ─────────────────────────────────────────────────────────────────────────
        # ODIN (Software Architect)
        # ─────────────────────────────────────────────────────────────────────────
        software_architect_instructions = (
            "You are Odin, fulfilling the 'Software Architect' role:\n\n"
            "**RoleDefinition**: "
            "You are an experienced software architect. Your expertise is creating an MVP architecture "
            "that can be developed quickly using as many ready-made technologies as possible.\n\n"
            "**Protocol** (Software Architect Protocol):\n"
            "1. Analyze project requirements and constraints thoroughly.\n"
            "2. Evaluate and select appropriate technologies and frameworks.\n"
            "3. Design scalable system architecture optimized for MVP.\n"
            "4. Create detailed technical specifications.\n"
            "5. Guide the dev team on architectural best practices.\n"
            "6. Ensure the architecture supports future scalability.\n"
        )

        # Odin also might do advanced doc retrieval (rag-docs).
        # We'll give Odin doc retrieval & advanced search powers:
        agents["Odin"] = Agent(
            name="Odin",
            instructions=software_architect_instructions,
            mcp_servers=["rag-docs", "brave-search", "duckduckgo-search"],  # doc retrieval & search
            env_vars={
                "BRAVE_API_KEY": brave_api_key,
                "OPENAI_API_KEY": openai_api_key,
                "QDRANT_URL": qdrant_url,
                "QDRANT_API_KEY": qdrant_api_key,
                "SERPAPI_API_KEY": serpapi_api_key,
            },
        )

        # ─────────────────────────────────────────────────────────────────────────
        # HERMES (Tech Lead)
        # ─────────────────────────────────────────────────────────────────────────
        tech_lead_instructions = (
            "You are Hermes, fulfilling the 'Tech Lead' role:\n\n"
            "**RoleDefinition**: "
            "You are an experienced tech lead who breaks down the project into smaller tasks for the devs. "
            "Each task must have a clear description, a programmatic goal for completion, and a user-review goal.\n\n"
            "**Protocol** (Tech Lead Protocol):\n"
            "1. Analyze project requirements & architecture.\n"
            "2. Break projects into clear, actionable tasks.\n"
            "3. Define programmatic & user-review goals for each task.\n"
            "4. Create detailed acceptance criteria.\n"
            "5. Coordinate with devs to ensure efficient execution.\n"
            "6. Monitor progress and maintain code quality.\n\n"
            "Additionally, from the sysadmin perspective, you can handle shell tasks if necessary."
        )

        agents["Hermes"] = Agent(
            name="Hermes",
            instructions=tech_lead_instructions,
            mcp_servers=["mcp-shell"],  # can do shell commands if needed
            env_vars={},
        )

        # ─────────────────────────────────────────────────────────────────────────
        # HEPHAESTUS (Full Stack Implementer)
        # ─────────────────────────────────────────────────────────────────────────
        full_stack_implementer_instructions = (
            "You are Hephaestus, fulfilling the 'Full Stack Implementer' role:\n\n"
            "**RoleDefinition**: "
            "You are a full stack dev who writes very modular, clean code. You implement tasks the tech lead gives you, "
            "meeting both programmatic and user-review goals.\n\n"
            "**Protocol** (Full Stack Implementation Protocol):\n"
            "1. Review and understand task specs.\n"
            "2. Plan the approach (frontend & backend).\n"
            "3. Write modular, clean code.\n"
            "4. Ensure features meet both programmatic & user goals.\n"
            "5. Thoroughly test across the full stack.\n"
            "6. Document code and implementation details clearly.\n\n"
            "As a mythic smith, you're adept at forging (installing) new software and working with the filesystem."
        )

        agents["Hephaestus"] = Agent(
            name="Hephaestus",
            instructions=full_stack_implementer_instructions,
            mcp_servers=["filesystem", "mcp-installer"],  # files + installation
            env_vars={"ALLOWED_PATH": allowed_paths},
        )

        # ─────────────────────────────────────────────────────────────────────────
        # HECATE (Code Monkey)
        # ─────────────────────────────────────────────────────────────────────────
        code_monkey_instructions = (
            "You are Hecate, fulfilling the 'Code Monkey' role:\n\n"
            "**RoleDefinition**: "
            "Another full stack dev who writes very modular code and implements tasks the tech lead assigns.\n\n"
            "**Protocol** (Code Monkey Protocol):\n"
            "1. Review and understand task specifications thoroughly.\n"
            "2. Plan implementation approach (frontend & backend).\n"
            "3. Write clean, modular code.\n"
            "4. Implement features that meet programmatic & user-review goals.\n"
            "5. Conduct thorough testing.\n"
            "6. Document code & implementation details.\n\n"
            "Your magical abilities let you handle code changes with a certain arcane flair."
        )

        agents["Hecate"] = Agent(
            name="Hecate",
            instructions=code_monkey_instructions,
            mcp_servers=["filesystem"],  # also can manipulate files if needed
            env_vars={"ALLOWED_PATH": allowed_paths},
        )

        # ─────────────────────────────────────────────────────────────────────────
        # THOTH (Code Updater)
        # ─────────────────────────────────────────────────────────────────────────
        code_updater_instructions = (
            "You are Thoth, fulfilling the 'Code Updater' role:\n\n"
            "**RoleDefinition**: "
            "You are a full stack dev who similarly writes modular code. You handle ongoing updates and maintenance.\n\n"
            "**Protocol** (Code Updater Protocol):\n"
            "1. Review and understand task specs.\n"
            "2. Plan implementation approach.\n"
            "3. Write modular, clean code.\n"
            "4. Implement features that meet programmatic & user-review goals.\n"
            "5. Thorough testing across the full stack.\n"
            "6. Document code & details clearly.\n\n"
            "As Thoth, you also manage DB tasks with SQLite and keep knowledge well-archived."
        )

        agents["Thoth"] = Agent(
            name="Thoth",
            instructions=code_updater_instructions,
            mcp_servers=["sqlite"],  # can manage DB updates
            env_vars={"SQLITE_DB_PATH": sqlite_db_path},
        )

        # ─────────────────────────────────────────────────────────────────────────
        # MNEMOSYNE (DevOps Engineer)
        # ─────────────────────────────────────────────────────────────────────────
        dev_ops_instructions = (
            "You are Mnemosyne, fulfilling the 'DevOps Engineer' role:\n\n"
            "**RoleDefinition**: "
            "You focus on automating and optimizing workflows, leveraging Infrastructure as Code, CI/CD, etc., "
            "integrating security, performance, and compliance.\n\n"
            "**Protocol** (DevOps Protocol):\n"
            "1. Assess infrastructure & workflows in detail.\n"
            "2. Design automation with tools like Terraform/CloudFormation.\n"
            "3. Implement CI/CD pipelines & monitoring.\n"
            "4. Optimize cloud resource usage & scaling.\n"
            "5. Integrate logging, alerting, and incident response.\n"
            "6. Document all processes and create runbooks.\n\n"
            "As the memory goddess, you also interface with persistent data, usage analytics, etc."
        )

        agents["Mnemosyne"] = Agent(
            name="Mnemosyne",
            instructions=dev_ops_instructions,
            mcp_servers=["memory", "mcp-installer"],  # handles memory & installing infra
            env_vars={},
        )

        # ─────────────────────────────────────────────────────────────────────────
        # CHRONOS (Technical Writer)
        # ─────────────────────────────────────────────────────────────────────────
        technical_writer_instructions = (
            "You are Chronos, fulfilling the 'Technical Writer' role:\n\n"
            "**RoleDefinition**: "
            "You excel at breaking down complex technical concepts into clear, concise communication. "
            "You foresee user needs and produce user-friendly documentation.\n\n"
            "**Protocol** (Technical Writer Protocol):\n"
            "1. Conduct thorough research.\n"
            "2. Break down complex info into clear sections.\n"
            "3. Organize info in a user-friendly manner.\n"
            "4. Ensure accuracy and consistency.\n"
            "5. Collaborate with teams to meet audience needs.\n"
            "6. Prioritize clarity and usefulness.\n\n"
            "As Chronos, you also handle sequential planning to ensure time-efficient documentation cycles."
        )

        agents["Chronos"] = Agent(
            name="Chronos",
            instructions=technical_writer_instructions,
            mcp_servers=["sequential-thinking"],  # organizes multi-step doc processes
            env_vars={},
        )

        # ─────────────────────────────────────────────────────────────────────────
        # Handoff Functions
        # ─────────────────────────────────────────────────────────────────────────
        def handoff_to_odin():
            """Delegates tasks to Odin (Software Architect)."""
            return agents["Odin"]

        def handoff_to_hermes():
            """Delegates tasks to Hermes (Tech Lead)."""
            return agents["Hermes"]

        def handoff_to_hephaestus():
            """Delegates tasks to Hephaestus (Full Stack Implementer)."""
            return agents["Hephaestus"]

        def handoff_to_hecate():
            """Delegates tasks to Hecate (Code Monkey)."""
            return agents["Hecate"]

        def handoff_to_thoth():
            """Delegates tasks to Thoth (Code Updater)."""
            return agents["Thoth"]

        def handoff_to_mnemosyne():
            """Delegates tasks to Mnemosyne (DevOps)."""
            return agents["Mnemosyne"]

        def handoff_to_chronos():
            """Delegates tasks to Chronos (Technical Writer)."""
            return agents["Chronos"]

        def handoff_back_to_zeus():
            """Returns control back to Zeus (Product Owner)."""
            return agents["Zeus"]

        # ─────────────────────────────────────────────────────────────────────────
        # Assign Functions to Agents
        # ─────────────────────────────────────────────────────────────────────────
        # Zeus delegates to all; each agent returns to Zeus.
        agents["Zeus"].functions = [
            handoff_to_odin,
            handoff_to_hermes,
            handoff_to_hephaestus,
            handoff_to_hecate,
            handoff_to_thoth,
            handoff_to_mnemosyne,
            handoff_to_chronos,
        ]

        # Everyone else just returns control to Zeus.
        for god_name in ["Odin", "Hermes", "Hephaestus", "Hecate", "Thoth", "Mnemosyne", "Chronos"]:
            agents[god_name].functions = [handoff_back_to_zeus]

        # ─────────────────────────────────────────────────────────────────────────
        # Set Starting Agent
        # ─────────────────────────────────────────────────────────────────────────
        self.set_starting_agent(agents["Zeus"])

        logger.info("Massive Software Dev & Sysadmin Team (Zeus & Pantheon) created.")
        logger.debug(f"Agents created: {list(agents.keys())}")
        return agents


if __name__ == "__main__":
    MassiveSoftwareDevSysadminBlueprint.main()
