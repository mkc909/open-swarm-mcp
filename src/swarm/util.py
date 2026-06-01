import inspect
from datetime import datetime
from .types import Tool  # <-- Adjust import as needed if 'Tool' is in a different location

def merge_fields(target, source):
    for key, value in source.items():
        if isinstance(value, str):
            target[key] += value
        elif value is not None and isinstance(value, dict):
            merge_fields(target[key], value)

def merge_chunk(final_response: dict, delta: dict) -> None:
    delta.pop("role", None)
    merge_fields(final_response, delta)

    tool_calls = delta.get("tool_calls")
    if tool_calls and len(tool_calls) > 0:
        index = tool_calls[0].pop("index")
        merge_fields(final_response["tool_calls"][index], tool_calls[0])

def function_to_json(func) -> dict:
    """
    Converts either:
      - a Python callable (non-Tool) to a JSON-serializable function schema by reflecting on signature
      - a Tool instance, using the Tool's input_schema (if provided by the MCP server)

    Returns a dictionary representing the function signature in JSON format for OpenAI.
    """
    # 1) If it's an instance of Tool, use the Tool's name/description/schema
    if isinstance(func, Tool):
        name = func.name
        description = func.description or ""
        # The tool’s input_schema might be something like:
        # {
        #   "type": "object",
        #   "properties": { ... },
        #   "required": [ ... ]
        # }
        tool_schema = func.input_schema or {}

        final_type = tool_schema.get("type", "object")
        final_properties = tool_schema.get("properties", {})
        final_required = tool_schema.get("required", [])

        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": final_type,
                    "properties": final_properties,
                    "required": final_required,
                },
            },
        }

    # 2) Otherwise, do reflection-based logic for a normal Python callable
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    # Derive name, docstring, and param-based schema
    name = getattr(func, "__name__", "unnamed_function")
    description = func.__doc__ or ""

    parameters = {}
    required = []
    for param in signature.parameters.values():
        # Determine JSON type from type_map, default to "string"
        ann = param.annotation if param.annotation != inspect._empty else str
        param_type = type_map.get(ann, "string")
        parameters[param.name] = {"type": param_type}

        if param.default == inspect._empty:
            required.append(param.name)

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }
