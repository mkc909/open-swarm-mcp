from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

# Import models from the university blueprint
from blueprints.university.models import (
    TeachingUnit,
    Topic,
    LearningObjective,
    Subtopic,
    Course,
    Student,
    Enrollment,
    AssessmentItem,
    filter_students
)
# Import serializers from the original swarm serializers module
from src.swarm.serializers import (
    TeachingUnitSerializer,
    TopicSerializer,
    LearningObjectiveSerializer,
    SubtopicSerializer,
    CourseSerializer,
    StudentSerializer,
    EnrollmentSerializer,
    AssessmentItemSerializer
)

class TeachingUnitViewSet(ModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = TeachingUnit.objects.all()
    serializer_class = TeachingUnitSerializer

class TopicViewSet(ModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

class LearningObjectiveViewSet(ModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = LearningObjective.objects.all()
    serializer_class = LearningObjectiveSerializer

class SubtopicViewSet(ModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = Subtopic.objects.all()
    serializer_class = SubtopicSerializer

class CourseViewSet(ModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

class StudentViewSet(ModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get_queryset(self):
        name = self.request.query_params.get("name")
        status = self.request.query_params.get("status")
        unit_codes = self.request.query_params.get("unit_codes")
        if unit_codes:
            unit_codes = unit_codes.split(',')
        if name or status or unit_codes:
            return filter_students(name=name, status=status, unit_codes=unit_codes)
        return super().get_queryset()

class EnrollmentViewSet(ModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

class AssessmentItemViewSet(ModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = AssessmentItem.objects.all()
    serializer_class = AssessmentItemSerializer

__all__ = [
    "TeachingUnitViewSet",
    "TopicViewSet",
    "LearningObjectiveViewSet",
    "SubtopicViewSet",
    "CourseViewSet",
    "StudentViewSet",
    "EnrollmentViewSet",
    "AssessmentItemViewSet"
]