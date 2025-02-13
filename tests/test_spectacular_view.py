import json
from django.test import TestCase
from rest_framework.test import APIRequestFactory  # type: ignore
from swarm.models import TeachingUnit
from swarm.views import SpectacularAPIView


class SpectacularAPIViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    # def test_get_schema(self):
    #     request = self.factory.get('/schema/')
    #     view = SpectacularAPIView.as_view()
    #     response = view(request)
    #     response.render()
    #     self.assertEqual(response.status_code, 200)
    #     try:
    #         content = response.content.decode()
    #         data = json.loads(content)
    #         self.assertIsInstance(data, dict)
    #     except Exception as e:
    #         self.fail(f"Response content is not valid JSON. Error: {e}. Content: {response.content.decode()}")

    def test_post_not_allowed(self):
        request = self.factory.post('/schema/', {})
        view = SpectacularAPIView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 405)

    def test_exclude_from_schema(self):
        self.assertTrue(hasattr(SpectacularAPIView, 'exclude_from_schema'))
        self.assertTrue(SpectacularAPIView.exclude_from_schema)

    def test_options(self):
        request = self.factory.options('/schema/')
        view = SpectacularAPIView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)