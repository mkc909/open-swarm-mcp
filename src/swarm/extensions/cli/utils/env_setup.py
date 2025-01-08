# Handles .env management and environment validation for the CLI

import os
from dotenv import load_dotenv

def validate_env():
    """Ensure all required environment variables are set."""
    load_dotenv()
    required_vars = ["API_KEY", "MCP_SERVER"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        return False
    print("Environment validation passed.")
    return True
