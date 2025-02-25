#!/usr/bin/env python3
import argparse
import importlib.util
import os
import sys
import subprocess
import shutil
import json
import PyInstaller.__main__

def resolve_env_vars(data):
    if isinstance(data, dict):
        return {k: resolve_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_env_vars(item) for item in data]
    elif isinstance(data, str):
        return os.path.expandvars(data)
    else:
        return data

MANAGED_DIR = os.path.expanduser("~/.swarm/blueprints")
BIN_DIR = os.path.expanduser("~/.swarm/bin")

def ensure_managed_dir():
    if not os.path.exists(MANAGED_DIR):
        os.makedirs(MANAGED_DIR, exist_ok=True)
    if not os.path.exists(BIN_DIR):
        os.makedirs(BIN_DIR, exist_ok=True)

def add_blueprint(source_path, blueprint_name=None):
    source_path = os.path.normpath(source_path)
    if not os.path.exists(source_path):
        print("Error: source file/directory does not exist:", source_path)
        sys.exit(1)
    if os.path.isdir(source_path):
        if not blueprint_name:
            blueprint_name = os.path.basename(os.path.normpath(source_path))
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
        print(f"Blueprint '{blueprint_name}' added successfully to {target_dir}.")
    else:
        blueprint_file = source_path
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
    target_dir = os.path.join(MANAGED_DIR, blueprint_name)
    if os.path.exists(target_dir) and os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
        print(f"Blueprint '{blueprint_name}' deleted successfully.")
    else:
        print(f"Error: Blueprint '{blueprint_name}' does not exist.")
        sys.exit(1)

def run_blueprint(blueprint_name):
    target_dir = os.path.join(MANAGED_DIR, blueprint_name)
    blueprint_file = os.path.join(target_dir, f"blueprint_{blueprint_name}.py")
    if not os.path.exists(blueprint_file):
        print(f"Error: Blueprint file not found for '{blueprint_name}'. Install it using 'swarm-cli add <path>'.")
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

def install_blueprint(blueprint_name):
    target_dir = os.path.join(MANAGED_DIR, blueprint_name)
    blueprint_file = os.path.join(target_dir, f"blueprint_{blueprint_name}.py")
    if not os.path.exists(blueprint_file):
        print(f"Error: Blueprint '{blueprint_name}' is not registered. Add it using 'swarm-cli add <path>'.")
        sys.exit(1)
    cli_name = blueprint_name  # Use blueprint_name as default cli_name for simplicity
    try:
        PyInstaller.__main__.run([
            blueprint_file,
            "--onefile",
            "--name", cli_name,
            "--distpath", BIN_DIR,
            "--workpath", os.path.join(target_dir, "build"),
            "--specpath", target_dir
        ])
    except KeyboardInterrupt:
        print("Installation aborted by user request.")
        sys.exit(1)
    print(f"Blueprint '{blueprint_name}' installed as CLI utility '{cli_name}' at: {os.path.join(BIN_DIR, cli_name)}")

def uninstall_blueprint(blueprint_name, blueprint_only=False, wrapper_only=False):
    target_dir = os.path.join(MANAGED_DIR, blueprint_name)
    blueprint_file = os.path.join(target_dir, f"blueprint_{blueprint_name}.py")
    cli_name = blueprint_name  # Default to blueprint_name for uninstall
    cli_path = os.path.join(BIN_DIR, cli_name)
    removed = False
    
    if not blueprint_only and not wrapper_only:  # Remove both by default
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
            print(f"Blueprint '{blueprint_name}' removed from {MANAGED_DIR}.")
            removed = True
        if os.path.exists(cli_path):
            os.remove(cli_path)
            print(f"Wrapper '{cli_name}' removed from {BIN_DIR}.")
            removed = True
    elif blueprint_only:
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
            print(f"Blueprint '{blueprint_name}' removed from {MANAGED_DIR}.")
            removed = True
    elif wrapper_only:
        if os.path.exists(cli_path):
            os.remove(cli_path)
            print(f"Wrapper '{cli_name}' removed from {BIN_DIR}.")
            removed = True
    
    if not removed:
        print(f"Error: Nothing to uninstall for '{blueprint_name}' with specified options.")
        sys.exit(1)

def main():
    os.environ.pop("SWARM_BLUEPRINTS", None)
    parser = argparse.ArgumentParser(
        description="Swarm CLI Launcher\n\nSubcommands:\n"
                    "  add     : Add a blueprint to the managed directory.\n"
                    "  list    : List registered blueprints.\n"
                    "  delete  : Delete a registered blueprint.\n"
                    "  run     : Run a blueprint by name.\n"
                    "  install : Install a blueprint as a CLI utility with PyInstaller.\n"
                    "  uninstall : Uninstall a blueprint and/or its CLI wrapper.\n"
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
    
    parser_install = subparsers.add_parser("install", help="Install a blueprint as a CLI utility with PyInstaller.")
    parser_install.add_argument("name", help="Blueprint name to install as a CLI utility.")
    
    parser_uninstall = subparsers.add_parser("uninstall", help="Uninstall a blueprint and/or its CLI wrapper.")
    parser_uninstall.add_argument("name", help="Blueprint name to uninstall.")
    parser_uninstall.add_argument("--blueprint-only", action="store_true", help="Remove only the blueprint directory.")
    parser_uninstall.add_argument("--wrapper-only", action="store_true", help="Remove only the CLI wrapper.")
    
    parser_migrate = subparsers.add_parser("migrate", help="Apply Django database migrations.")
    
    parser_config = subparsers.add_parser("config", help="Manage swarm configuration (LLM and MCP servers).")
    parser_config.add_argument("action", choices=["add", "list", "remove"], help="Action to perform on configuration")
    parser_config.add_argument("--section", required=True, choices=["llm", "mcpServers"], help="Configuration section to manage")
    parser_config.add_argument("--name", help="Name of the configuration entry (required for add and remove)")
    parser_config.add_argument("--json", help="JSON string for configuration entry (required for add)")
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
            default_config = {"llm": {}, "mcpServers": {}}
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            print("Default config file created at:", config_path)
        run_blueprint(args.name)
    elif args.command == "install":
        install_blueprint(args.name)
    elif args.command == "uninstall":
        uninstall_blueprint(args.name, args.blueprint_only, args.wrapper_only)
    elif args.command == "migrate":
        try:
            subprocess.run(["python", "manage.py", "migrate"], check=True)
            print("Migrations applied successfully.")
        except subprocess.CalledProcessError as e:
            print("Error applying migrations:", e)
            sys.exit(1)
    elif args.command == "config":
        config_path = os.path.expanduser(args.config)
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
            if args.section == "mcpServers" and not args.name:
                if not args.json:
                    print("Error: --json is required for adding an mcpServers block when --name is omitted.")
                    sys.exit(1)
                try:
                    update_data = json.loads(args.json)
                except json.JSONDecodeError:
                    print("Error: --json must be a valid JSON string.")
                    sys.exit(1)
                if "mcpServers" not in update_data:
                    print("Error: JSON block must contain 'mcpServers' key for merging.")
                    sys.exit(1)
                config.setdefault("mcpServers", {})
                config["mcpServers"].update(update_data["mcpServers"])
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)
                print("MCP servers updated in configuration.")
            else:
                if not args.name or not args.json:
                    print("Error: --name and --json are required for adding an entry.")
                    sys.exit(1)
                try:
                    entry_data = json.loads(args.json)
                except json.JSONDecodeError:
                    print("Error: --json must be a valid JSON string.")
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
