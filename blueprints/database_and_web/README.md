# Database and Web Integration Example

This blueprint demonstrates the integration of two distinct agents within Open Swarm MCP:
- **SQLiteAgent**: For database queries and operations.
- **BraveAgent**: For web search capabilities.

It highlights how multiple agents can operate with different tools and collaboratively solve user requests dynamically.  

---

## Key Highlights

1. **Agent Collaboration**:
   - The `TriageAgent` intelligently delegates tasks to the appropriate agent based on the user's request.
   - Responses from agents are seamlessly integrated.

2. **MCP Server Tools**:
   - The blueprint leverages MCP server tools like `sqlite` and `brave-search` for execution.
   - Demonstrates dynamic tool registration and communication via MCP protocols.

3. **SQLiteAgent**:
   - Handles database operations such as querying and searching records.
   - Relies on the `sqlite` MCP server.

4. **BraveAgent**:
   - Performs web searches using the Brave Search MCP server.
   - Filters and retrieves relevant results dynamically.

This example serves as a demonstration of how to design a blueprint integrating multiple agents with distinct toolsets.
