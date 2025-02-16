import os
from django.conf import settings
from django.test import TestCase, Client
from blueprints.university.blueprint_university import UniversitySupportBlueprint

class UniversityBlueprintIntegrationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
        settings.ROOT_URLCONF = "swarm.urls"
        dummy_config = {
            "llm": {
                "default": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "dummy"
                }
            }
        }
        blueprint = UniversitySupportBlueprint(config=dummy_config)
        blueprint.register_blueprint_urls()

    def setUp(self):
        self.client = Client()

    def test_integration_teaching_unit(self):
        response = self.client.post('/v1/university/teaching-units/',
            data={'code': 'TEST101', 'name': 'Test Unit', 'teaching_prompt': 'Test prompt'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/v1/university/teaching-units/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('TEST101', response.content.decode())

    def test_integration_topic(self):
        self.client.post('/v1/university/teaching-units/',
            data={'code': 'TEST101', 'name': 'Test Unit', 'teaching_prompt': 'Test prompt'},
            content_type='application/json')
        response = self.client.post('/v1/university/topics/',
            data={'teaching_unit': 1, 'name': 'Test Topic', 'teaching_prompt': 'Topic prompt'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/v1/university/topics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Topic', response.content.decode())

    def test_integration_learning_objective(self):
        self.client.post('/v1/university/teaching-units/',
            data={'code': 'TEST101', 'name': 'Test Unit', 'teaching_prompt': 'Test prompt'},
            content_type='application/json')
        self.client.post('/v1/university/topics/',
            data={'teaching_unit': 1, 'name': 'Test Topic', 'teaching_prompt': 'Topic prompt'},
            content_type='application/json')
        response = self.client.post('/v1/university/learning-objectives/',
            data={'topic': 1, 'description': 'Objective description'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/v1/university/learning-objectives/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Objective description', response.content.decode())

    def test_integration_subtopic(self):
        self.client.post('/v1/university/teaching-units/',
            data={'code': 'TEST101', 'name': 'Test Unit', 'teaching_prompt': 'Test prompt'},
            content_type='application/json')
        self.client.post('/v1/university/topics/',
            data={'teaching_unit': 1, 'name': 'Test Topic', 'teaching_prompt': 'Topic prompt'},
            content_type='application/json')
        response = self.client.post('/v1/university/subtopics/',
            data={'topic': 1, 'name': 'Test Subtopic', 'teaching_prompt': 'Subtopic prompt'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/v1/university/subtopics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Subtopic', response.content.decode())

    def test_integration_course(self):
        self.client.post('/v1/university/teaching-units/',
            data={'code': 'TEST101', 'name': 'Test Unit', 'teaching_prompt': 'Test prompt'},
            content_type='application/json')
        response = self.client.post('/v1/university/courses/',
            data={'name': 'Test Course', 'code': 'TSTC', 'coordinator': 'Coordinator Name', 'teaching_units': [1], 'teaching_prompt': 'Course prompt'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/v1/university/courses/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Course', response.content.decode())

    def test_integration_student(self):
        response = self.client.post('/v1/university/students/',
            data={'name': 'Test Student', 'gpa': 4.0, 'status': 'active'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/v1/university/students/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Student', response.content.decode())

    def test_integration_enrollment(self):
        self.client.post('/v1/university/teaching-units/',
            data={'code': 'TEST101', 'name': 'Test Unit', 'teaching_prompt': 'Test prompt'},
            content_type='application/json')
        self.client.post('/v1/university/courses/',
            data={'name': 'Test Course', 'code': 'TSTC', 'coordinator': 'Coordinator Name', 'teaching_units': [1], 'teaching_prompt': 'Course prompt'},
            content_type='application/json')
        self.client.post('/v1/university/students/',
            data={'name': 'Test Student', 'gpa': 4.0, 'status': 'active'},
            content_type='application/json')
        response = self.client.post('/v1/university/enrollments/',
            data={'student': 1, 'course': 1, 'status': 'enrolled'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/v1/university/enrollments/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('enrolled', response.content.decode())

    def test_integration_assessment_item(self):
        self.client.post('/v1/university/teaching-units/',
            data={'code': 'TEST101', 'name': 'Test Unit', 'teaching_prompt': 'Test prompt'},
            content_type='application/json')
        self.client.post('/v1/university/courses/',
            data={'name': 'Test Course', 'code': 'TSTC', 'coordinator': 'Coordinator', 'teaching_units': [1], 'teaching_prompt': 'Course prompt'},
            content_type='application/json')
        self.client.post('/v1/university/students/',
            data={'name': 'Test Student', 'gpa': 4.0, 'status': 'active'},
            content_type='application/json')
        self.client.post('/v1/university/enrollments/',
            data={'student': 1, 'course': 1, 'status': 'enrolled'},
            content_type='application/json')
        response = self.client.post('/v1/university/assessment-items/',
            data={'enrollment': 1, 'title': 'Test Assessment', 'status': 'pending', 'due_date': '2025-03-01T09:00:00Z', 'weight': "20.00"},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/v1/university/assessment-items/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Assessment', response.content.decode())