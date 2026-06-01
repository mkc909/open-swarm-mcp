import os
from django.core.wsgi import get_wsgi_application
from django.test import TestCase

class WsgiTest(TestCase):
    def test_wsgi_application(self):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swarm.settings')
        application = get_wsgi_application()
        self.assertIsNotNone(application)
        self.assertEqual(os.environ['DJANGO_SETTINGS_MODULE'], 'swarm.settings')
