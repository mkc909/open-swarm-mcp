#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
from launchers import build_launchers

def main():
    parser = argparse.ArgumentParser(description="Swarm Install Launcher")
    parser.add_argument("blueprint", help="Path to blueprint Python file")
    parser.add_argument("--output", default=".", help="Output directory for the standalone utility")
    args = parser.parse_args()

    # Build the standalone executable using build_launchers.
    try:
        executable_path = build_launchers.build_executable(args.blueprint, args.output)
        if executable_path:
            print("Successfully created standalone utility at:", executable_path)
        else:
            print("Failed to create standalone utility.")
            sys.exit(1)
    except Exception as e:
        print("Error during installation:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()