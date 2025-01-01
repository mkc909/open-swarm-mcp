# tests/conftest.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables immediately upon importing conftest.py
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
