#!/usr/bin/env python3
import argparse
import importlib.util
import os
import sys
import subprocess
import shutil
import json

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
    source_path = os.path.normpath(source_path)
    if not os.path.exists(source_path):
        print("Error: source file/directory does not exist:", source_path)
        sys.exit(1)
    
    # Determine how to handle the blueprint source.
    if os.path.isdir(source_path):
        # For directory source, infer blueprint name from directory if not provided.
        if not blueprint_name:
            blueprint_name = os.path.basename(os.path.normpath(source_path))
        # Recursively copy the entire directory to the managed blueprints directory.
        target_dir = os.path.join(MANAGED_DIR, blueprint_name)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir, exist_ok=True)
        for root, dirs, files in os.walk(source_path):
            rel_path = os.path.relpath(root, source_path)
            dest_root = os.path.join(target_dir, rel_path) if rel_path != '.' else target_dir
            os.makedirs(dest_root, exist_ok=True)
            for file in files:
                shutil.copy2(os.path.join(root, file), os.path.join(dest_root, file))
        print("DEBUG: Source directory contents:", os.listdir(source_path))
        print("DEBUG: Target directory contents after copy:", os.listdir(target_dir))
        print(f"Blueprint '{blueprint_name}' added successfully to {target_dir}.")
        return
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
                    "  install : Install a blueprint as a CLI utility.\n"
                    "  migrate : Apply Django database migrations.\n"
                    "  config  : Manage swarm configuration (LLM and MCP servers).",
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
    
    parser_config = subparsers.add_parser("config", help="Manage swarm configuration (LLM and MCP servers).")
    parser_config.add_argument("action", choices=["add", "list", "remove"], help="Action to perform on configuration")
    parser_config.add_argument("--section", required=True, choices=["llm", "mcpServers"], help="Configuration section to manage")
    parser_config.add_argument("--name", help="Name of the configuration entry (required for add and remove)")
    parser_config.add_argument("--entry", help="JSON string for configuration entry (required for add)")
    parser_config.add_argument("--config", default="~/.swarm/swarm_config.json", help="Path to configuration file")
    
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
                f.write('{\n    "llm": {},\n    "mcpServers": {}\n}\n')
            print("Default config file created at:", config_path)
        run_blueprint(args.name)
    elif args.command == "install":
        install_blueprint(args.name, args.wrapper_dir)
    elif args.command == "migrate":
        try:
            subprocess.run(["python", "manage.py", "migrate"], check=True)
            print("Migrations applied successfully.")
        except subprocess.CalledProcessError as e:
            print("Error applying migrations:", e)
            sys.exit(1)
    elif args.command == "config":
        config_path = os.path.expanduser(args.config)
        # Load config; if not exists, create a default configuration
        if not os.path.exists(config_path):
            default_conf = {"llm": {}, "mcpServers": {}}
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(default_conf, f, indent=4)
            print("Default config file created at:", config_path)
            config = default_conf
        else:
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                print("Error: Invalid configuration file.")
                sys.exit(1)
        section = args.section
        if args.action == "list":
            entries = config.get(section, {})
            if entries:
                print(f"Entries in {section}:")
                for key, value in entries.items():
                    print(f" - {key}: {json.dumps(value, indent=4)}")
            else:
                print(f"No entries found in {section}.")
        elif args.action == "add":
            if not args.name or not args.entry:
                print("Error: --name and --entry are required for adding an entry.")
                sys.exit(1)
            try:
                entry_data = json.loads(args.entry)
            except json.JSONDecodeError:
                print("Error: --entry must be a valid JSON string.")
                sys.exit(1)
            config.setdefault(section, {})[args.name] = entry_data
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
            print(f"Entry '{args.name}' added to {section} in configuration.")
        elif args.action == "remove":
            if not args.name:
                print("Error: --name is required for removing an entry.")
                sys.exit(1)
            if args.name in config.get(section, {}):
                del config[section][args.name]
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)
                print(f"Entry '{args.name}' removed from {section} in configuration.")
            else:
                print(f"Error: Entry '{args.name}' not found in {section}.")
                sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()