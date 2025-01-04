from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from typing import List, Callable, Union, Optional, Dict, Any

# Third-party imports
from pydantic import BaseModel

AgentFunction = Callable[[], Union[str, "Agent", dict]]


class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o"
    instructions: Union[str, Callable[[], str]] = "You are a helpful agent."
    functions: List[AgentFunction] = []
    tool_choice: str = None
    parallel_tool_calls: bool = True
    mcp_servers: Optional[List[str]] = None  # List of MCP server names
    env_vars: Optional[Dict[str, str]] = None  # Environment variables required

class Response(BaseModel):
    messages: List = []
    agent: Optional[Agent] = None
    context_variables: dict = {}


class Result(BaseModel):
    """
    Encapsulates the possible return values for an agent function.

    Attributes:
        value (str): The result value as a string.
        agent (Agent): The agent instance, if applicable.
        context_variables (dict): A dictionary of context variables.
    """

    value: str = ""
    agent: Optional[Agent] = None
    context_variables: dict = {}

class Tool(BaseModel):
    """
    Represents a generic tool that can be invoked by agents.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of the tool's functionality.
        func (Callable[..., Any]): The function to execute the tool.
        input_schema (Optional[Dict[str, Any]]): JSON schema defining the tool's input parameters.
    """
    name: str
    description: str
    func: Callable[..., Any]  # Requires `Any` from `typing`
    input_schema: Optional[Dict[str, Any]] = None
