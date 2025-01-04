from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)


from typing import List, Callable, Union, Optional, Dict, Any
from pydantic import BaseModel


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
    func: Callable[..., Any]
    input_schema: Optional[Dict[str, Any]] = None


class AgentFunction(BaseModel):
    """
    Represents a function that an agent can perform, wrapping a Tool.

    Attributes:
        name (str): The name of the function.
        description (str): A brief description of the function.
        func (Callable[..., Any]): The callable associated with the function.
        input_schema (Optional[Dict[str, Any]]): JSON schema defining the input parameters.
    """
    name: str
    description: str
    func: Callable[..., Any]
    input_schema: Optional[Dict[str, Any]] = None


class Agent(BaseModel):
    """
    Represents an agent within the Swarm framework.

    Attributes:
        name (str): The name of the agent.
        model (str): The model used by the agent (default: "gpt-4o").
        instructions (Union[str, Callable[[Dict[str, Any]], str]]): Instructions or prompt for the agent.
        functions (List[AgentFunction]): List of callable functions or tools.
        tool_choice (Optional[str]): Tool choice logic.
        parallel_tool_calls (bool): Whether the agent can make parallel tool calls.
        mcp_servers (Optional[List[str]]): MCP servers mapped to this agent.
        env_vars (Optional[Dict[str, str]]): Environment variables required for the agent.
    """
    name: str = "Agent"
    model: str = "gpt-4o"
    instructions: Union[str, Callable[[Dict[str, Any]], str]] = "You are a helpful agent."
    functions: List[AgentFunction] = []
    tool_choice: Optional[str] = None
    parallel_tool_calls: bool = True
    mcp_servers: Optional[List[str]] = None  # List of MCP server names
    env_vars: Optional[Dict[str, str]] = None  # Environment variables required


class Response(BaseModel):
    """
    Represents a response from the Swarm framework.

    Attributes:
        messages (List[Dict[str, Any]]): A list of message dictionaries.
        agent (Optional[Agent]): The agent responsible for the response.
        context_variables (Dict[str, Any]): Additional context variables.
    """
    messages: List[Dict[str, Any]] = []
    agent: Optional[Agent] = None
    context_variables: Dict[str, Any] = {}


class Result(BaseModel):
    """
    Encapsulates the possible return values for an agent function.

    Attributes:
        value (str): The result value as a string.
        agent (Optional[Agent]): The agent instance, if applicable.
        context_variables (Dict[str, Any]): A dictionary of context variables.
    """
    value: str = ""
    agent: Optional[Agent] = None
    context_variables: Dict[str, Any] = {}
