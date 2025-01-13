"""
Local version of settings.py that uses local URLs configuration
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Import all settings from the main settings file
from .settings import *

# Override ROOT_URLCONF to use our local URLs
ROOT_URLCONF = 'swarm.urls_local'

# Load environment variables from .env
load_dotenv(dotenv_path=BASE_DIR / '.env')

# Override CONFIG_PATH to use environment variable
CONFIG_PATH = Path(os.getenv('CONFIG_PATH', str(BASE_DIR / "swarm_config.json")))
