#!/usr/bin/env python3
import os
import glob
import subprocess

def main():
    blueprint_dir = "blueprints"
    # Iterate over each subdirectory in the blueprints directory
    for entry in os.listdir(blueprint_dir):
        full_dir = os.path.join(blueprint_dir, entry)
        if os.path.isdir(full_dir):
            # Find a file matching blueprint_*.py in the directory
            files = glob.glob(os.path.join(full_dir, "blueprint_*.py"))
            if files:
                blueprint_file = files[0]
                output_name = entry  # Use the directory name as the executable name
                print(f"Building executable for {blueprint_file} as {output_name}")
                # Build a standalone executable using PyInstaller
                command = [
                    "pyinstaller",
                    "--onefile",
                    "--name", output_name,
                    "--add-data", "blueprints:blueprints",
                    "--add-data", "nemo_guardrails/default_config.yml:nemoguardrails/rails/llm",
                    "--add-data", "nemo_guardrails/default_config_v2.yml:nemoguardrails/rails/llm",
                    "--runtime-hook", "swarm_cli_hook.py",
                    blueprint_file
                ]
                # Run the PyInstaller command with updated PYTHONPATH and set SWARM_CLI for CLI mode
                env = os.environ.copy()
                env["PYTHONPATH"] = os.getcwd()
                subprocess.run(command, check=True, env=env)
                print(f"Executable for {output_name} built successfully.")

if __name__ == "__main__":
    main()