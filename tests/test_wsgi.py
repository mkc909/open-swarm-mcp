import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swarm.settings")

def test_wsgi_application():
    assert callable(get_wsgi_application()), "WSGI application is not callable"
