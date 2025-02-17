import os
os.environ.setdefault('ENABLE_API_AUTH', 'false')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swarm.settings')
import django
django.setup()
from django.test import TestCase, Client

class AssessmentItemIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create prerequisites: teaching unit, course, student, enrollment
        response = self.client.post('/v1/university/teaching-units/',
            data={'code': 'ASMT101', 'name': 'Assessment Teaching Unit', 'teaching_prompt': 'TP'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

        response = self.client.post('/v1/university/courses/',
            data={
                'name': 'Assessment Course',
                'code': 'ASMTC',
                'coordinator': 'Coordinator',
                'teaching_units': [1],
                'teaching_prompt': 'Course prompt'
            },
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

        response = self.client.post('/v1/university/students/',
            data={'name': 'Assessment Student', 'gpa': '4.0', 'status': 'active'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

        response = self.client.post('/v1/university/enrollments/',
            data={'student': 1, 'course': 1, 'status': 'enrolled'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_create_and_get_assessment_item(self):
        # Create an assessment item
        response = self.client.post('/v1/university/assessment-items/',
            data={
                'enrollment': 1,
                'title': 'Integration Test Assessment',
                'status': 'pending',
                'due_date': '2025-03-01T09:00:00Z',
                'weight': '20.00'
            },
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Retrieve assessment items
        response = self.client.get('/v1/university/assessment-items/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Integration Test Assessment', response.content.decode())