# SQLite and Search Example

This example demonstrates how to use Open Swarm MCP with an SQLite database and Brave Search integration. It highlights the dynamic tool registration and interaction capabilities provided by Open Swarm MCP.

---

## Overview

### Features:
1. **SQLite Database Queries**:
   - Connect to a local SQLite database.
   - Perform SQL operations (retrieve, update, delete, and insert data).
   - Display query results in a formatted table.

2. **Internet Search**:
   - Perform web searches using Brave Search.
   - Retrieve and display search results.
   - Filter results by relevance, date, or source.

---

## Configuration

The `mcp_server_config.json` file defines the system prompt, LLM settings, and MCP server configurations. This file is provided in this folder as an example. Make sure to customize it to your environment and needs.

---

## Usage

### Step 1: Prepare the Configuration File

Ensure `mcp_server_config.json` is updated with valid credentials and paths:
- Replace `your-brave-api-key` with your Brave API key.
- Verify the SQLite database file path in the `sqlite` configuration.

### Step 2: Run the Example

Run the application using the configuration file:

```bash
uv run ../../src/open_swarm_mcp/main.py --config mcp_server_config.json
