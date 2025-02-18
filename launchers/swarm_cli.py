 #!/usr/bin/env python3
import argparse
import importlib.util
import os
import sys
import shutil

# Managed blueprints directory
MANAGED_DIR = os.path.expanduser("~/.swarm/blueprints")

def ensure_managed_dir():
    if not os.path.exists(MANAGED_DIR):
        os.makedirs(MANAGED_DIR, exist_ok=True)

def add_blueprint(source_path, blueprint_name=None):
    """
    Copy the blueprint file from the provided source_path into the managed blueprints directory.
    If blueprint_name is not provided, try to infer it from the filename by stripping a leading "blueprint_" and the .py extension.
    """
    if not os.path.exists(source_path):
        print("Error: source file/directory does not exist:", source_path)
        sys.exit(1)
    
    # Determine the blueprint file path from source.
    if os.path.isdir(source_path):
        # Look for a matching blueprint file in the directory.
        files = [f for f in os.listdir(source_path) if f.startswith("blueprint_") and f.endswith(".py")]
        if not files:
            print("Error: No blueprint file found in directory:", source_path)
            sys.exit(1)
        blueprint_file = os.path.join(source_path, files[0])
    else:
        blueprint_file = source_path

    # Infer blueprint name if not provided.
    if not blueprint_name:
        base = os.path.basename(blueprint_file)
        if base.startswith("blueprint_") and base.endswith(".py"):
            blueprint_name = base[len("blueprint_"):-3]
        else:
            blueprint_name = os.path.splitext(base)[0]
    
    target_dir = os.path.join(MANAGED_DIR, blueprint_name)
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, f"blueprint_{blueprint_name}.py")
    shutil.copy2(blueprint_file, target_file)
    print(f"Blueprint '{blueprint_name}' added successfully to {target_dir}.")

def list_blueprints():
    """List all blueprints in the managed directory."""
    ensure_managed_dir()
    entries = os.listdir(MANAGED_DIR)
    blueprints = [d for d in entries if os.path.isdir(os.path.join(MANAGED_DIR, d))]
    if blueprints:
        print("Registered blueprints:")
        for bp in blueprints:
            print(" -", bp)
    else:
        print("No blueprints registered.")

def delete_blueprint(blueprint_name):
    """Delete the blueprint directory for the given blueprint name."""
    target_dir = os.path.join(MANAGED_DIR, blueprint_name)
    if os.path.exists(target_dir) and os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
        print(f"Blueprint '{blueprint_name}' deleted successfully.")
    else:
        print(f"Error: Blueprint '{blueprint_name}' does not exist.")
        sys.exit(1)

def run_blueprint(blueprint_name):
    """Dynamically load and run the blueprint's main() from the managed directory."""
    target_dir = os.path.join(MANAGED_DIR, blueprint_name)
    blueprint_file = os.path.join(target_dir, f"blueprint_{blueprint_name}.py")
    if not os.path.exists(blueprint_file):
        print(f"Error: Blueprint file not found for '{blueprint_name}'.")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("blueprint_module", blueprint_file)
    if spec is None or spec.loader is None:
        print("Error: Failed to load blueprint module from:", blueprint_file)
        sys.exit(1)
    blueprint = importlib.util.module_from_spec(spec)
    loader = spec.loader
    src_path = os.path.join(os.getcwd(), "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    loader.exec_module(blueprint)
    if hasattr(blueprint, "main"):
        blueprint.main()
    else:
        print("Error: The blueprint does not have a main() function.")
        sys.exit(1)

def install_blueprint(blueprint_name, wrapper_dir="bin"):
    """
    Create a CLI wrapper script for the given blueprint.
    The wrapper script will be installed in the specified wrapper_dir (default: "bin").
    When executed, it runs: python <path-to-swarm_cli.py> run <blueprint_name>
    """
    target_dir = os.path.join(MANAGED_DIR, blueprint_name)
    blueprint_file = os.path.join(target_dir, f"blueprint_{blueprint_name}.py")
    if not os.path.exists(blueprint_file):
        print(f"Error: Blueprint '{blueprint_name}' is not registered.")
        sys.exit(1)
    if not os.path.exists(wrapper_dir):
        os.makedirs(wrapper_dir, exist_ok=True)
    wrapper_path = os.path.join(wrapper_dir, blueprint_name)
    cli_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "swarm_cli.py")
    content = f"""#!/usr/bin/env python3
import sys
import os
os.execvp("python", ["python", "{cli_path}", "run", "{blueprint_name}"] )
"""
    with open(wrapper_path, "w") as f:
        f.write(content)
    os.chmod(wrapper_path, 0o755)
    print(f"Blueprint '{blueprint_name}' installed as CLI utility at: {os.path.abspath(wrapper_path)}")

def main():
    os.environ.pop("SWARM_BLUEPRINTS", None)
    parser = argparse.ArgumentParser(
        description="Swarm CLI Launcher\n\nSubcommands:\n"
                    "  add     : Add a blueprint to the managed directory.\n"
                    "  list    : List registered blueprints.\n"
                    "  delete  : Delete a registered blueprint.\n"
                    "  run     : Run a blueprint by name.\n"
                    "  install : Install a blueprint as a CLI utility.",
        formatter_class=argparse.RawTextHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available subcommands")
    
    parser_add = subparsers.add_parser("add", help="Add a blueprint from a file or directory.")
    parser_add.add_argument("source", help="Source blueprint file or directory.")
    parser_add.add_argument("--name", help="Optional blueprint name. If not provided, inferred from filename.")
    
    parser_list = subparsers.add_parser("list", help="List registered blueprints.")
    
    parser_delete = subparsers.add_parser("delete", help="Delete a registered blueprint by name.")
    parser_delete.add_argument("name", help="Blueprint name to delete.")
    
    parser_run = subparsers.add_parser("run", help="Run a blueprint by name.")
    parser_run.add_argument("name", help="Blueprint name to run.")
    parser_run.add_argument("--config", default="~/.swarm/swarm_config.json", help="Path to configuration file.")
    
    parser_install = subparsers.add_parser("install", help="Install a blueprint as a CLI utility.")
    parser_install.add_argument("name", help="Blueprint name to install as a CLI utility.")
    parser_install.add_argument("--wrapper-dir", default="bin", help="Directory to place the wrapper script (default: ./bin)")
    parser_migrate = subparsers.add_parser("migrate", help="Apply Django database migrations.")
    
    args = parser.parse_args()
    ensure_managed_dir()
    
    if args.command == "add":
        add_blueprint(args.source, args.name)
    elif args.command == "list":
        list_blueprints()
    elif args.command == "delete":
        delete_blueprint(args.name)
    elif args.command == "run":
        config_path = os.path.expanduser(args.config)
        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                f.write('{\n    "llm": {\n        "default": {\n            "provider": "openai",\n            "model": "gpt-4o",\n            "base_url": "https://api.openai.com/v1",\n            "api_key": "${OPENAI_API_KEY}"\n        }\n    },\n    "mcpServers": {\n        "everything": {\n            "command": "npx",\n            "args": ["-y", "@modelcontextprotocol/server-everything"],\n            "env": {}\n        }\n    }\n}\n')
            print("Default config file created at:", config_path)
        run_blueprint(args.name)
    elif args.command == "install":
        install_blueprint(args.name, args.wrapper_dir)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()