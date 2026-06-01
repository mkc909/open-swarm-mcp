from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeachingUnitViewSet,
    TopicViewSet,
    LearningObjectiveViewSet,
    SubtopicViewSet,
    CourseViewSet,
    StudentViewSet,
    EnrollmentViewSet,
    AssessmentItemViewSet,
)

router = DefaultRouter()
router.register(r'teaching-units', TeachingUnitViewSet, basename='teaching-units')
router.register(r'topics', TopicViewSet, basename='topics')
router.register(r'learning-objectives', LearningObjectiveViewSet, basename='learning-objectives')
router.register(r'subtopics', SubtopicViewSet, basename='subtopics')
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'students', StudentViewSet, basename='students')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollments')
router.register(r'assessment-items', AssessmentItemViewSet, basename='assessment-items')

urlpatterns = [
    path('', include(router.urls)),
]