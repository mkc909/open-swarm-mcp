# Handles configuration management workflows (e.g., LLM, MCP servers)

from swarm.extensions.config.config_loader import (
    load_server_config,
    save_server_config,
)

def add_llm(model_name, api_key):
    """Add a new LLM configuration."""
    config = load_server_config()
    if "llms" not in config:
        config["llms"] = {}
    config["llms"][model_name] = {"api_key": api_key}
    save_server_config(config)
    print(f"Added LLM '{model_name}' to configuration.")
