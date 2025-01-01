# Open Swarm

<img src="assets/images/openswarm-project-image.jpg" alt="Project Logo" width="512"/>

**Open Swarm** is a versatile, modular framework for building intelligent, multi-agent systems. It's meant as a **drop-in alternative** to the [OpenAI Swarm](https://github.com/openai/swarm) framework—accepting new pull requests and actively maintained with additional features for agentic workflows. 

---

## Table of Contents
- [Key Features](#key-features)
- [Blueprints](#blueprints)
- [Operational Modes](#operational-modes)
- [Configuration & Multiple LLM Providers](#configuration--multiple-llm-providers)
- [Installation](#installation)
- [Running Open Swarm](#running-open-swarm)
- [Deploying with Docker](#deploying-with-docker)
  - [Deploy with Docker Compose (Recommended)](#deploy-with-docker-compose-recommended)
  - [Deploy Standalone](#deploy-standalone)
- [Progress Tracker](#progress-tracker)
- [Further Documentation](#further-documentation)
- [License](#license)

---

## Key Features

1. **Multi-Agent Orchestration**  
   - Define multiple agents, each with unique instructions and roles.
   - Agents coordinate tasks, share context, or hand off queries between one another.

2. **Blueprint-Driven Architecture**  
   - Each **Blueprint** encapsulates logic, tool connections, and environment/config settings.
   - Encourages reusable, modular patterns for different use cases.

3. **Optional MCP or GPT Actions**  
   - Integrate with external tools (e.g., databases, web search, filesystems) through **MCP servers**.
   - (TODO) Use **GPT Actions** as an alternative for agent expansions without dedicated MCP infrastructure.

4. **CLI & REST Interface**  
   - A setup wizard helps define or update blueprint configurations.
   - Run from the command line or expose a Django-powered REST API for broader integration.
   - Interactive web pages per blueprint at `/<blueprint_name>/`.

5. **OpenAI API Compatibility**  
   - Exposes an endpoint at `/v1/chat/completions` that is functionally similar to the OpenAI Chat Completions API.
   - Includes a **mandatory** `sender` field in agent responses.  
     - This field identifies which Swarm agent provided the response and must be preserved in the conversation history for proper handoffs between agents.
     - While the framework is compatible with OpenAI-like API clients, it assumes the client application maintains the `sender` field and, ideally, displays it in the user interface.
     - **Note:** Most OpenAI API-compatible applications will ignore the `sender` field by default and not display the agent name. Custom UI or logic is required to utilise and present this information.

6. **Configurable LLM Providers**  
   - Supports multiple OpenAI-compatible providers in a single environment (e.g., `echo`, `grok`, `ollama`).
   - Allows specifying different models/providers for different agents—even within the same blueprint.
   - Use environment variable to specify default llm model provider used by blueprints, `LLM=ollama`

---

## Blueprints

A **Blueprint** is a Python module that wraps:

- **Agent Logic**: Defines how each agent in the Swarm processes user messages, whether it calls tools, and how it decides to hand off to other agents.
- **Tools**: Specifies which agents have which tools (e.g. a read-only SQLite database) the agents may invoke.
- **Environment & Configuration**: Ensures required environment variables and JSON configs are validated prior to agent execution.

Once registered, a blueprint is discoverable at runtime, allowing the system to list and load agents on demand.

### University Support Example

Consider a **University Support Blueprint** that orchestrates multiple agents to handle campus-related queries:

1. **Triage Agent**  
   - Inspects each incoming query (e.g., *“Which courses are recommended for data science?”*).  
   - Determines whether to route it to a **Course Advisor**, **Scheduling Assistant**, or a creative **Campus Culture** responder.  
   - Demonstrates handoffs by returning the specialised agent most suited to the query.  

2. **Course Advisor Agent**  
   - Relies on a read-only SQLite database (exposed as an MCP server tool) for course recommendations.  
   - Executes queries like `SELECT * FROM courses WHERE discipline='Data Science';` via a method such as `read_query()`.

3. **Scheduling Assistant Agent**  
   - Accesses a separate scheduling database to provide timetables, exam schedules, and important dates.  
   - Responds in short, factual statements, suitable for quick reference.

In practice, this blueprint:
- Bundles the agent instructions and personalities (e.g., helpful advisor, factual scheduler).  
- Requires environment variable, `OPENAI_API_KEY` for LLM inference.  
- Performs both **CLI** and **REST** interactions, so you can either run it locally or expose it as a service through `/v1/chat/completions`.

### Other Examples
Open Swarm showcases a growing library of **Blueprint** examples:

| Blueprint Name          | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Echo Blueprint**      | A straightforward agent that simply echoes user inputs—ideal for testing or as a starter template. |
| **Database and Web Blueprint** | Demonstrates MCP-based integration with an SQLite database and Brave Search, illustrating how to combine data retrieval with real-time web queries. |
| **Filesystem Blueprint** | Provides agents that can interact with local file directories (read/write operations) through a **filesystem** MCP server. |
| **Weather Blueprint**   | Fetches current weather and forecasts via external APIs (e.g., OpenWeatherMap), showing how environment variables and requests-based calls can be integrated. |

---

## Operational Modes

1. **CLI Mode**  
   - Run `uv run src/swarm/main.py --wizard` to configure blueprints interactively.  
   - Execute specific blueprint files (e.g., `uv run blueprints/university/blueprint_university.py`).  
   - Great for local testing, debugging, and iterative development.

2. **REST Mode**  
   - Launch Django with `uv run manage.py runserver 0.0.0.0:8000`.  
   - Access endpoints:
     - `POST /v1/chat/completions`: Chat-style agent interactions (OpenAI-compatible).
     - `GET /v1/models`: Lists available blueprints.
     - `http://localhost:8000/<blueprint_name>/`: Interactive, web-based blueprint tester.
   - (TODO) Optionally integrate with Django Admin at `/admin`.

---

## Configuration & Multiple LLM Providers

Open Swarm uses:
- **`.env`** files for API keys or critical environment variables (e.g., `OPENAI_API_KEY`).  
- **`mcp_server_config.json`** (or custom JSON) for advanced settings:
  - **`llm_providers`**: Define multiple OpenAI-compatible endpoints (e.g., `openai`, `grok`, `ollama`).
  - **`mcp_servers`**: Tools/services that agents can call.
  - **`gpt_actions`**: (TODO) More tools/services that agents can call.

Different agents in a single blueprint can reference different LLM providers. For example:
```json
{
  "llm_providers": {
    "openai": {
      "provider": "openai",
      "model": "gpt-4",
      "base_url": "https://api.openai.com/v1",
      "api_key": "${OPENAI_API_KEY}"
    },
    "grok": {
      "provider": "openai",
      "model": "grok-2-1212",
      "base_url": "https://api.x.ai/v1",
      "api_key": "${XAI_API_KEY}"
    }
  }
}
```
These references let you quickly switch providers based on environment or agent specificity.

---

## Installation

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/matthewhand/open-swarm.git
   cd open-swarm
   ```
2. **Install Dependencies**  
   ```bash
   # Get 'uv' here => https://docs.astral.sh/uv/
   uv python install
   uv venv
   source .venv/bin/activate
   uv sync
   ```
3. **Environment Setup**  
   - Copy `.env.example` to `.env` and fill in sensitive details (`OPENAI_API_KEY`, etc.).
   - *(Optional)* Update `mcp_server_config.json` to add or modify LLM providers, MCP servers, etc.

---

## Running Open Swarm

```bash
# Option A - Run the CLI wizard (setup / blueprint runner)
uv run src/swarm/main.py

# Option B - Execute a specific blueprint in CLI mode
uv run blueprints/echo/blueprint_default.py

# Option C - Start the REST API on port 8000
uv run manage.py runserver 0.0.0.0:8000

# After launching the REST endpoint, open a browser and visit:
# - http://localhost:8000/<blueprint_name>/ (e.g., http://localhost:8000/university/)
# This will load an interactive webpage to test the blueprint functionality.

# Alternatively use the completions endpoint directly with cURL:
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"echo","messages":[{"role":"user","content":"Hello!"}]}'
```

---

## Deploying with Docker

### Deploy with Docker Compose (Recommended)

1. **Obtain `docker-compose.yaml`**  
   ```bash
   wget https://raw.githubusercontent.com/matthewhand/open-swarm/refs/heads/main/docker-compose.yaml
   ```
2. **Configure `.env` & (Optional) `mcp_server_config.json`**  
   - Ensure `.env` has `OPENAI_API_KEY`.  
   - Adjust `mcp_server_config.json` if you want to use local LLM endpoints or different providers. 
   ```

3. **Start the Service**  
   ```bash
   docker compose up -d
   ```
   This:
   - Builds the image if needed.
   - Reads port settings and environment variables from `.env`.
   - Exposes the application on `8000` (unless overridden via `$PORT`).

4. **Access**  
   - Visit [http://localhost:8000](http://localhost:8000) for the interactive blueprint pages.

### Deploy Standalone (TODO) 

```bash
docker run \
  --env-file .env \
  -p 8000:8000 \
  open-swarm:latest
```
*(An official Docker image is planned for registry release.)*

---

## Diagram: Backend HTTP Service Overview

Below is a simplified diagram illustrating how the **Open Swarm** HTTP service can function as a backend for any OpenAI API-compatible client or tool. The service lists configured **Blueprints** via `/v1/models` and performs inference through the `/v1/chat/completions` endpoint. Internally, it can call out to any configured **OpenAI-compatible LLM provider** (OpenAI, Grok, Ollama, etc.) and optionally run **GPT Actions** or **MCP servers** (like database, filesystem, or weather integrations).

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │        OpenAI-Compatible Client Tools (AnythingLLM, LibreChat)      │
 │                           or Open-WebUI, etc.                       │
 └────────────┬────────────────────────────────────────────────────────┘
              |                             
              |   (HTTP: /v1/chat/completions, /v1/models, etc.)
              ▼                             
 ┌─────────────────────────────────────────────────────────────────────┐
 │                 Open Swarm REST API Service (Django)                │
 │        (Exposes /v1/models, /v1/chat/completions, /admin)           │
 └─────────────────────────────────────────────────────────────────────┘
                   |                          |                
       (Mandatory) |                          | MCP Servers    
       GPT Actions |                          | (filesystem,    
       or Python   |                          | database, etc.)           
       Functions   ▼                          ▼                
       ┌────────────────────────┐         ┌────────────────────────┐
       │OpenAI-Compatible LLMs  │         │ External APIs/Services │
       │ (OpenAI, Grok, Ollama) │         │ (Weather, Database, ..)│
       └────────────────────────┘         └────────────────────────┘
```

---

## Progress Tracker

- **CLI Mode**  
  - [x] Setup Wizard  
  - [x] Blueprint Runner  

- **REST Mode**  
  - [x] Inference via `/v1/chat/completions`  
  - [x] Blueprints listed via `/v1/models`  
  - [ ] Application management via `/admin`  

- **Multiple LLM Providers**  
  - [x] Switch providers per environment  
  - [ ] Assign different providers/models per agent in one blueprint  

- **Docker**  
  - [x] Dockerfile and docker-compose.yaml  
  - [ ] Publish to Docker Registry  

- **PyPI Publishing**  
  - [ ] Publish Python module to PyPI  

- **Example Blueprints**  
  - [x] `echo`
  - [x] `database_and_web` (SQLite & Brave Search)  
  - [x] `filesystem`  
  - [x] `university`  
  - [x] `weather`  

- **Define all components under 'swarm'**  
  - [ ] Refactor code

---

## Further Documentation

For advanced usage, sequence diagrams, or in-depth tooling examples, see [DEVELOPMENT.md](./DEVELOPMENT.md). Additional expansions and best practices for agent orchestration, LLM provider swapping, and more can be found in that document.

---

## License

Open Swarm is provided under the MIT License. Refer to the [LICENSE](LICENSE) file for full details.
