"""
Interactive CLI shell for dynamic commands.
"""

from swarm.extensions.cli.utils.discover_commands import discover_commands
import os

COMMANDS_DIR = os.path.join(os.path.dirname(__file__), "commands")

def interactive_shell():
    """Launch an interactive CLI shell."""
    commands = discover_commands(COMMANDS_DIR)

    print("Welcome to the Swarm CLI Interactive Shell!")
    print("Type 'help' to see available commands, or 'exit' to quit.")

    while True:
        try:
            user_input = input("swarm> ").strip()
            if user_input == "exit":
                print("Exiting CLI shell.")
                break
            elif user_input == "help":
                show_help(commands)
            elif user_input in commands:
                command = commands[user_input]["execute"]
                if command:
                    command()
                else:
                    print(f"Command '{user_input}' is not executable.")
            else:
                print(f"Unknown command: {user_input}")
        except KeyboardInterrupt:
            print("\nExiting CLI shell.")
            break

def show_help(commands):
    """Display available commands."""
    print("Available commands:")
    for cmd, metadata in commands.items():
        print(f" - {cmd}: {metadata['description']}")
