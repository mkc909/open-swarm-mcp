import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swarm.settings')
django.setup()