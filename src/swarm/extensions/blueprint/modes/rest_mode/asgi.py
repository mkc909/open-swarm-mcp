# src/swarm/asgi.py

import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.asgi import get_asgi_application

# Define the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / '.env')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swarm.settings')

application = get_asgi_application()
