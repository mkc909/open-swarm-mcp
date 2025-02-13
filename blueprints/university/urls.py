from django.urls import path
from rest_framework.routers import DefaultRouter
from blueprints.university.views import (
    TeachingUnitViewSet,
    TopicViewSet,
    LearningObjectiveViewSet,
    SubtopicViewSet,
    CourseViewSet,
    StudentViewSet,
    EnrollmentViewSet,
    AssessmentItemViewSet
)

router = DefaultRouter()
router.register(r'v1/teaching_units', TeachingUnitViewSet, basename='teachingunit')
router.register(r'v1/topics', TopicViewSet, basename='topic')
router.register(r'v1/learning_objectives', LearningObjectiveViewSet, basename='learningobjective')
router.register(r'v1/subtopics', SubtopicViewSet, basename='subtopic')
router.register(r'v1/courses', CourseViewSet, basename='course')
router.register(r'v1/students', StudentViewSet, basename='student')
router.register(r'v1/enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'v1/assessment_items', AssessmentItemViewSet, basename='assessmentitem')

urlpatterns = router.urls