from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)

from typing import List, Callable, Union, Optional, Dict
from pydantic import BaseModel

AgentFunction = Callable[[], Union[str, "Agent", dict]]


class Agent(BaseModel):
    """
    Represents an agent within the Swarm framework.

    Attributes:
        name (str): The name of the agent.
        model (str): The model used by the agent (default: "gpt-4o").
        instructions (Union[str, Callable[[], str]]): Instructions or prompt for the agent.
        functions (List[AgentFunction]): List of callable functions or tools.
        tool_choice (str): Tool choice logic (optional).
        parallel_tool_calls (bool): Whether the agent can make parallel tool calls.
        mcp_servers (Optional[List[str]]): MCP servers mapped to this agent.
        env_vars (Optional[Dict[str, str]]): Environment variables required for the agent.
    """
    name: str = "Agent"
    model: str = "gpt-4o"
    instructions: Union[str, Callable[[], str]] = "You are a helpful agent."
    functions: List[AgentFunction] = []
    tool_choice: Optional[str] = None
    parallel_tool_calls: bool = True
    mcp_servers: Optional[List[str]] = None  # List of MCP server names
    env_vars: Optional[Dict[str, str]] = None  # Environment variables required


class Response(BaseModel):
    """
    Represents a response from the Swarm framework.

    Attributes:
        messages (List): A list of message dictionaries.
        agent (Optional[Agent]): The agent responsible for the response.
        context_variables (dict): Additional context variables.
    """
    messages: List = []
    agent: Optional[Agent] = None
    context_variables: dict = {}


class Result(BaseModel):
    """
    Encapsulates the possible return values for an agent function.

    Attributes:
        value (str): The result value as a string.
        agent (Optional[Agent]): The agent instance, if applicable.
        context_variables (dict): A dictionary of context variables.
    """
    value: str = ""
    agent: Optional[Agent] = None
    context_variables: dict = {}
