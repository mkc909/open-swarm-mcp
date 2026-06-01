# Open Swarm User Guide

This guide provides detailed, user-focused instructions for using Open Swarm, including how to manage blueprints, configure the system with swarm-cli, and interact with the swarm-api.

---

## Swarm CLI Overview

The **swarm-cli** is the primary command-line tool for managing blueprints and configuration settings. It allows you to:

- **Manage Blueprints:**  
  Add, list, delete, run, and install blueprints. Blueprints are Python modules that encapsulate agent logic and tool connections.

- **Manage Configuration:**  
  - **Configuration File:** By default, configurations are stored in `~/.swarm/swarm_config.json`. On first execution, if the file is not found, a default configuration is created:
    ```json
    {
        "llm": {
            "default": {
                "provider": "openai",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "api_key": "${OPENAI_API_KEY}"
            }
        },
        "mcpServers": {}
    }
    ```
    *Note:* Only environment variable placeholders (e.g., `${OPENAI_API_KEY}`) are recorded. You must set the corresponding environment variables for the system to work correctly.

  - **Adding New Configurations:**  
    You can add new configuration entries using the following commands:
    - Adding an LLM configuration:
      ```
      swarm-cli config add --section llm --name deepseek-r1-distill-llama-70b --json '{"provider": "openai", "model": "deepseek-r1-distill-llama-70b", "base_url": "https://api.groq.com/openai/v1", "api_key": "${GROQ_API_KEY}"}' --config ~/.swarm/swarm_config.json
      ```
    - Adding a configuration for a reasoning model:
      ```
      swarm-cli config add --section llm --name reason --json '{"provider": "openai", "model": "o3-mini", "base_url": "https://api.openai.com/v1", "api_key": "${OPENAI_API_KEY}", "reasoning_effort": "high"}' --config ~/.swarm/swarm_config.json
      ```

  - **Merging MCP Server Configurations:**  
    For MCP servers, you can merge a multiline JSON block into the existing `mcpServers` section. For example:
      ```
      swarm-cli config add --section mcpServers --json '{
          "mcpServers": {
              "mcp-doc-forge": {
                  "command": "npx",
                  "args": ["-y", "@cablate/mcp-doc-forge"]
              }
          }
      }' --config ~/.swarm/swarm_config.json
      ```
    When merging, do not provide a `--name` parameter; the JSON block must include the `"mcpServers"` key.

## Swarm API Overview

The **swarm-api** component provides an HTTP REST service enabling programmatic interactions with Open Swarm:

- **Endpoints:**
  - **`/v1/models`** – Lists available blueprints treated as models for an OpenAI API-compatible client.
  - **`/v1/chat/completion`** (or `/v1/chat/completions`) – Processes chat completion requests.
  
- **Usage:**  
  These endpoints allow external applications to interact seamlessly with Open Swarm. For example:
  ```bash
  curl -X POST http://localhost:8000/v1/chat/completion \
       -H "Content-Type: application/json" \
       -d '{"model": "university", "messages": [{"role": "user", "content": "What courses should I take?"}]}'
  ```

- **Service Options:**  
  The REST API service supports command-line arguments for setting the port, running as a daemon, and restricting published blueprints via the `SWARM_BLUEPRINTS` environment variable.

## Additional Notes

- **Environment Variables:**  
  Ensure that you provide valid values for variables such as `OPENAI_API_KEY`, `GROQ_API_KEY`, etc. The configuration file records environment variable placeholders, so the corresponding environment variables must be set for the system to function correctly.

- **Troubleshooting:**  
  If you experience issues with blueprint loading or configuration, verify that the configuration file (`~/.swarm/swarm_config.json`) contains the correct JSON structure and that all required environment variables are properly defined.

---

This guide is intended to assist both new and experienced users in configuring and using Open Swarm effectively. For more detailed configuration information and advanced usage, please refer to the DEVELOPMENT.md file.

---

## Swarm CLI and Swarm API

This section details how to use the **swarm-cli** and **swarm-api** utilities. They are essential tools for administration and integration in the Open Swarm framework.

### Swarm CLI

The **swarm-cli** utility is a command-line tool that manages blueprints and configuration settings for your Open Swarm deployment. It supports managing configurations for both language models (LLM) and MCP servers.

#### Default Configuration Creation

On first execution of a blueprint, if no configuration file is found at the default location (`~/.swarm/swarm_config.json`), a simple default configuration is automatically created. This default uses the OpenAI GPT-4o settings:
```json
{
    "llm": {
        "default": {
            "provider": "openai",
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1",
            "api_key": "${OPENAI_API_KEY}"
        }
    },
    "mcpServers": {}
}
```
*Note:* The default configuration only records the environment variable placeholder `${OPENAI_API_KEY}`. The user must supply a valid `OPENAI_API_KEY` (and other required keys) through their environment variables.

#### Configuring Additional LLM Providers

Users can augment the LLM configuration by adding new entries. For example, to add an alternative provider:
```json
{
    "deepseek-r1-distill-llama-70b": {
        "provider": "openai",
        "model": "deepseek-r1-distill-llama-70b",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": "${GROQ_API_KEY}"
    }
}
```
Or to add a reasoning model (that may be referenced as the `reason` model in blueprint code):
```json
{
    "reason": {
        "provider": "openai",
        "model": "o3-mini",
        "base_url": "https://api.openai.com/v1",
        "api_key": "${OPENAI_API_KEY}",
        "reasoning_effort": "high"
    }
}
```
Use the command:
```
swarm-cli config add --section llm --name <entry_name> --json '<json_blob>' --config ~/.swarm/swarm_config.json
```

#### Configuring MCP Servers

The **swarm-cli** utility also supports MCP server configurations. You can merge a multiline JSON block into the existing `mcpServers` section. For instance, to add an MCP server without environment variables:
```json
{
    "mcp-npx-fetch": {
        "command": "npx",
        "args": [
            "-y",
            "@tokenizin/mcp-npx-fetch"
        ]
    }
}
```
To merge an entire MCP servers block:
```json
{
    "mcpServers": {
        "mcp-doc-forge": {
            "command": "npx",
            "args": [
                "-y",
                "@cablate/mcp-doc-forge"
            ]
        }
    }
}
```
For MCP servers with environment variables, for example:
```json
{
    "brave-search": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
            "BRAVE_API_KEY": "${BRAVE_API_KEY}"
        }
    },
```    

When the environment variable is referenced as a command argument, best practice is to explicitly list in the `env` section for runtime validation:
```json
    "filesystem": {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-filesystem",
            "${ALLOWED_PATH}"
        ],
        "env": {
            "ALLOWED_PATH": "${ALLOWED_PATH}"
        }
    }
}
```
When adding an MCP servers block, run:
```
swarm-cli config add --section mcpServers --json '<multiline_json_block>' --config ~/.swarm/swarm_config.json
```
*Note:* When merging MCP server blocks, do not provide a `--name` parameter; the JSON block must include the `"mcpServers"` key.

### Swarm API

The **swarm-api** component offers programmatic access to Open Swarm functionalities. It enables external applications to interact with blueprints and internal services via RESTful endpoints. For example, you can perform chat completions and list available blueprints using endpoints that mimic the OpenAI Chat Completions API. Detailed API documentation is provided separately.
