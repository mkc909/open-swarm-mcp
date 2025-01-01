# Open Swarm MCP

<img src="assets/images/openswarm-project-image.jpg" alt="Project Logo" width="512"/>

Open Swarm MCP is a modular, Python-based framework that seamlessly integrates **OpenAI Swarm** with **Message Context Protocol (MCP)** for multi-agent orchestration. Designed for both **CLI** and **REST** usage, it provides a structured approach to configuring agents, tools, and environment variables via its **Blueprint** standard. This ensures adaptability and scalability for diverse use cases—from educational demos to enterprise-grade solutions.

---

## Table of Contents
- [Key Features](#key-features)
- [Blueprints](#blueprints)
  - [University Support Example](#university-support-example)
- [Operational Modes](#operational-modes)
- [Configuration & Metadata](#configuration--metadata)
- [Installation](#installation)
- [Running with UV and Python](#running-with-uv-and-python)
- [Deploying with Docker](#deploying-with-docker)
  - [Deploy with Docker Compose (Recommended)](#deploy-with-docker-compose-recommended)
  - [Deploy Without Docker Compose (Image Pending Docker Registry)](#deploy-without-docker-compose-image-pending-docker-registry)
- [Progress Tracker](#progress-tracker)
- [Further Documentation](#further-documentation)
- [License](#license)

---

## Key Features

1. **CLI & REST Support**  
   - Includes a setup wizard for quick initialisation.  
   - Provides flexible modes to run agents from the command line or via a Django-powered REST interface.
   - Offers interactive webpages for each blueprint via `/<blueprint_name>/`.  

2. **MCP Server Integrations**  
   - Agents can utilise external tools provided by MCP servers.  
   - Facilitates secure, configurable connections to services like filesystems, databases, or web search.

3. **Blueprint Standard**  
   - Each blueprint encapsulates logic for one or more Swarm agents, along with any MCP server tool requirements.  
   - Integrates `.env` secrets and `.json` configuration for robust environment handling.

4. **OpenAI API Compatibility + Agent Sender**  
   - Exposes an endpoint at `/v1/chat/completions` that is functionally similar to the OpenAI Chat Completions API.
   - Includes a **mandatory** `sender` field in agent responses.  
     - This field identifies which Swarm agent provided the response and must be preserved in the conversation history for proper handoffs between agents.
     - While the framework is compatible with OpenAI-like API clients, it assumes the client application maintains the `sender` field and, ideally, displays it in the user interface.
     - **Note:** Most OpenAI API-compatible applications will ignore the `sender` field by default and not display the agent name. Custom UI or logic is required to utilise and present this information.

---

## Blueprints

A **Blueprint** is a Python module that wraps:

- **Agent Logic**: Defines how each agent in the Swarm processes user messages, whether it calls tools, and how it decides to hand off to other agents.
- **MCP Server Tools**: Specifies which external tool servers (e.g. a read-only SQLite database) the agents may invoke.
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

---

## Operational Modes

1. **CLI Mode**  
   - Offers an interactive command-line interface to experiment with agent behaviours.  
   - Includes a setup wizard to guide basic configuration.  
   - Allows running specific blueprints directly from the CLI.

2. **REST Mode**  
   - Exposes endpoints compatible with OpenAI-like interfaces:
     - `POST /v1/chat/completions` for inference (supports an optional `sender` field).
     - `GET /v1/models` to list enabled blueprints.
     - `/admin` portal (Django admin) to manage application settings
   - Provides interactive blueprint webpages at `/<blueprint_name>/` (e.g. /university/):
     - Each page allows users to interact directly with the blueprint, submit queries, and view responses.
   - Ideal for integrating with front-end clients, external automation scripts, or exploring specific blueprints in a user-friendly format.

---

## Configuration & Metadata

Open Swarm MCP relies on **environment variables** and a **JSON config** to manage agent-specific parameters, LLM provider details, and references to MCP servers:

- **`.env` Files**: Store sensitive values like API keys (e.g., `BRAVE_API_KEY`) or database paths.  
- **JSON Config (`mcp_server_config.json`)**: Lists the MCP servers to use and other key-value pairs (e.g., `"allowed_paths"` for filesystem access).

Each **Blueprint** exposes a `metadata` property which declares:
- **`title`**: A brief description of the blueprint.
- **`description`**: A longer description of the blueprint.
- **`required_mcp_servers`**: An array of MCP servers needed by the blueprint.  
- **`config`**: Runtime configuration keys that are stored in the JSON file and updated via the CLI wizard.  
- **`env_vars`**: Required environment variables validated before the blueprint runs.

During the setup wizard or at runtime, the framework reads the **`metadata`** from each blueprint and ensures:
1. All required environment variables are set in `.env`.
2. Config items (like `"allowed_paths"`) are present or updated in the JSON file.
3. MCP servers needed by the blueprint (`"required_mcp_servers"`) are registered in `mcp_server_config.json`.

This approach provides a clean, modular way to organise agent logic, external tool references, and custom settings across different blueprints.

---

## Installation

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/matthewhand/open-swarm-mcp.git
   cd open-swarm-mcp
   ```
2. **Install Dependencies**  
   ```bash
   # using uv, get it here => https://docs.astral.sh/uv/
   uv python install
   uv venv
   source .venv/bin/activate
   uv sync
   ```
3. **Setup Environment**  
   - Copy `.env.example` to `.env` and populate it with your API keys (e.g., `OPENAI_API_KEY`).
   - (Optional) Edit `mcp_server_config.json` (in `src/open_swarm_mcp`) to add additional MCP servers or change LLM provider details (e.g., replace `'gpt-4o'` with `'o1-mini'`, or override `api_base` to use a local LLM provider like [Ollama](https://github.com/jmorganca/ollama)).

---

## Running with UV and Python

```bash
# Option A - Setup wizard, list and choose blueprints
uv run src/open_swarm_mcp/main.py 

# Option B - Setup wizard then run specific blueprint
uv run src/open_swarm_mcp/main.py --blueprint university

# Option C - Run specific blueprint (no setup wizard) 
uv run blueprints/university/blueprint_university.py

# Option D - Launch HTTP REST endpoint
uv run manage.py runserver 0.0.0.0:8000

# After launching the REST endpoint, open a browser and visit:
# - http://localhost:8000/<blueprint_name>/ (e.g., http://localhost:8000/university/)
# This will load an interactive webpage to test the blueprint functionality.

# Option E - Launch HTTP REST endpoint using Docker (port 8000 if $PORT not set in .env)
docker compose up -d
```

---

## Deploying with Docker

### Deploy with Docker Compose (Recommended)

1. **Download the Compose File**  
   You can quickly fetch the pre-configured `docker-compose.yaml` file:
   ```bash
   wget https://raw.githubusercontent.com/matthewhand/open-swarm-mcp/refs/heads/main/docker-compose.yaml
   ```

2. **Update the Environment File**  
   Make sure your `.env` file includes the following keys:
   - **`OPENAI_API_KEY`** (mandatory) for LLM inference.
   - Optionally update the `api_base` configuration in `mcp_server_config.json` if you plan to use a local LLM provider like Ollama:
     ```json
     {
       "api_base": "http://host.docker.internal:11434/v1"
     }
     ```

3. **Start the Container**  
   Run the following command to build and start the service in the background:
   ```bash
   docker compose up -d
   ```
   This:
   - Builds the image if needed.
   - Reads port settings and environment variables from `.env`.
   - Exposes the application on `8000` (unless overridden via `$PORT`).

4. **Access the Service**  
   Open [http://localhost:8000](http://localhost:8000) in your browser to interact with Open Swarm MCP.

### Deploy Without Docker Compose (Image Pending Docker Registry)

1. **Pull the Prebuilt Image**  
   *(Coming soon: official image on Docker Hub or GitHub Container Registry.)*

2. **Run the Container**  
   After the image is published:
   ```bash
   docker run \
     --env-file .env \
     -p 8000:8000 \
     open-swarm-mcp:latest
   ```

3. **Update `.env`**  
   Ensure at least `OPENAI_API_KEY` is set. Or, modify `mcp_server_config.json` to point to a local LLM instead of an OpenAI endpoint.

4. **Access the Service**  
   Navigate to [http://localhost:8000](http://localhost:8000).

---

## Progress Tracker

Below is the current development progress, reflecting professional stewardship of feature requests and deliverables:

- [ ] **CLI Mode**
  - [x] Setup Wizard  
  - [ ] Blueprint Runner  

- [ ] **Django REST**
  - [x] Inference via `/v1/chat/completions`  
  - [x] Blueprints listed via `/v1/models`  
  - [ ] Application management via `/admin`  

- [ ] **Docker**
  - [x] Dockerfile and docker-compose.yaml
  - [ ] Publish to docker registry

- [ ] **Standalone Example Blueprints**
  - [x] Filesystem utility example  
  - [x] Path-e-tech game example  
  - [ ] University example  

- [ ] **Example MCP Servers**
  - [x] filesystem  
  - [ ] web search  
  - [ ] database  

---

## Further Documentation

For more technical details on the design, including sequence diagrams and advanced usage, refer to the [DEVELOPMENT.md](./DEVELOPMENT.md) file in this repository.

---

## License

Open Swarm MCP is provided under the MIT License. Refer to the [LICENSE](LICENSE) file for full details.

---

*(Developed with a focus on extensibility, professional agent orchestration, and user-friendly deployment. Feedback and contributions are always welcome.)*
