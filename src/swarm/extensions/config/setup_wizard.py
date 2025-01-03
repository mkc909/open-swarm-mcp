import os
import json
from typing import Dict, Any

def run_setup_wizard(config_path: str, blueprints_metadata: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Runs the interactive setup wizard.

    Args:
        config_path (str): Path to the configuration file.
        blueprints_metadata (Dict[str, Dict[str, Any]]): Metadata for available blueprints.

    Returns:
        Dict[str, Any]: Updated configuration.
    """
    config = {}

    # Configure LLM settings
    print("Configuring LLM settings:")
    provider = input("Enter the name of the LLM provider (e.g., 'ollama', 'openai'): ").strip()
    model = input(f"Enter the model name for provider '{provider}' (e.g., 'gpt-4'): ").strip()
    temperature = float(input("Enter the temperature for the model (e.g., 0.7): ").strip())
    api_key = input("Enter the API key for the provider (optional, press Enter to skip): ").strip() or None

    config["llm"] = {
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "api_key": api_key,  # API key is optional
    }

    # Select a blueprint
    print("\nAvailable Blueprints:")
    for idx, (key, metadata) in enumerate(blueprints_metadata.items(), start=1):
        print(f"{idx}. {key}: {metadata.get('title', 'No title')} - {metadata.get('description', 'No description')}")

    while True:
        try:
            blueprint_choice = input("\nEnter the number of the blueprint to use (0 to skip): ").strip()
            if blueprint_choice.lower() in ["q", "quit", "exit"]:  # Handle exit inputs
                print("Exiting blueprint selection.")
                break

            blueprint_choice = int(blueprint_choice)
            if blueprint_choice == 0:
                print("No blueprint selected.")
                break
            elif 1 <= blueprint_choice <= len(blueprints_metadata):
                selected_blueprint_key = list(blueprints_metadata.keys())[blueprint_choice - 1]
                config["blueprint"] = selected_blueprint_key
                print(f"Selected Blueprint: {selected_blueprint_key}")
                break
            else:
                print(f"Invalid selection. Please enter a number between 0 and {len(blueprints_metadata)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    # Save configuration
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)
    print(f"Configuration saved to {config_path}.")

    return config
