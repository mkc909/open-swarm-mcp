from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from typing import List, Callable, Union, Optional, Dict, Any

# Third-party imports
from pydantic import BaseModel

# AgentFunction = Callable[[], Union[str, "Agent", dict]]
AgentFunction = Callable[..., Union[str, "Agent", dict]]

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

class Tool:
    def __init__(
        self,
        name: str,
        func: Callable,
        description: str = "",
        input_schema: Optional[Dict[str, Any]] = None,
        dynamic: bool = False,
    ):
        """
        Initialize a Tool object.

        :param name: Name of the tool.
        :param func: The callable associated with this tool.
        :param description: A brief description of the tool.
        :param input_schema: Schema defining the inputs the tool accepts.
        :param dynamic: Whether this tool is dynamically generated.
        """
        self.name = name
        self.func = func
        self.description = description
        self.input_schema = input_schema or {}
        self.dynamic = dynamic

    def __call__(self, *args, **kwargs):
        """
        Make the Tool instance callable.
        """
        return self.func(*args, **kwargs)
