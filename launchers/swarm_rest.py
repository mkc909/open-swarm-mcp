#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
from os import path, listdir, makedirs
from os import path, listdir, makedirs

def main():
    parser = argparse.ArgumentParser(description="Swarm REST Launcher")
    parser.add_argument("--blueprint", required=True, help="Path to blueprint Python file (for configuration purposes)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the REST server")
    parser.add_argument("--config", default="~/.swarm/swarm_config.json", help="Configuration file path")
    args = parser.parse_args()
    blueprint_path = None
    # Process blueprint argument: allow blueprint name from managed directory.
    if path.exists(args.blueprint):
        if path.isdir(args.blueprint):
            blueprint_arg = args.blueprint
            matches = [f for f in listdir(blueprint_arg) if f.startswith("blueprint_") and f.endswith(".py")]
            if not matches:
                print("Error: No blueprint file found in directory:", blueprint_arg)
                sys.exit(1)
            blueprint_path = path.join(blueprint_arg, matches[0])
            print(f"Using blueprint file: {blueprint_path}")
        else:
            blueprint_path = args.blueprint
    else:
        managed_path = path.expanduser("~/.swarm/blueprints/" + args.blueprint)
        if path.isdir(managed_path):
            matches = [f for f in listdir(managed_path) if f.startswith("blueprint_") and f.endswith(".py")]
            if not matches:
                print("Error: No blueprint file found in managed directory:", managed_path)
                sys.exit(1)
            blueprint_path = path.join(managed_path, matches[0])
            print(f"Using managed blueprint: {blueprint_path}")
        else:
            print("Error: Blueprint not found:", args.blueprint)
            sys.exit(1)

    config_path = path.expanduser(args.config)
    if not path.exists(config_path):
        makedirs(path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            f.write("{}")
        print("Default config file created at:", config_path)
    
    # Inform user about the blueprint selection (currently for configuration/documentation)
    print("Using blueprint:", blueprint_path)
    print("Launching Django server on port 0.0.0.0:{}".format(args.port))

    # Pass through the command to manage.py to run Django's runserver
    try:
        subprocess.run(["python", "manage.py", "runserver", f"0.0.0.0:{args.port}"], check=True)
    except subprocess.CalledProcessError as e:
        print("Error launching Django server:", e)
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()