import pytest
from src.swarm.util import function_to_json
from src.swarm.types import Tool

def test_function_to_json_callable():
    def example_function(a: int, b: str) -> None:
        pass

    result = function_to_json(example_function)
    assert result["type"] == "function"
    assert result["function"]["name"] == "example_function"
    assert result["function"]["description"] == ""
    assert result["function"]["parameters"]["type"] == "object"
    assert "a" in result["function"]["parameters"]["properties"]
    assert "b" in result["function"]["parameters"]["properties"]

def test_function_to_json_tool():
    class ExampleTool(Tool):
        def __init__(self):
            self.name = "ExampleTool"
            self.description = "This is an example tool."
            self.input_schema = {
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            }

    tool = ExampleTool()
    result = function_to_json(tool)
    assert result["type"] == "function"
    assert result["function"]["name"] == "ExampleTool"
    assert result["function"]["description"] == "This is an example tool."
    assert result["function"]["parameters"]["type"] == "object"
    assert "param1" in result["function"]["parameters"]["properties"]