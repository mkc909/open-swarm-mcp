from rest_framework import serializers
from blueprints.university.models import (
    TeachingUnit, Topic, LearningObjective, Subtopic, Course, Student, Enrollment, AssessmentItem
)

class TeachingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachingUnit
        fields = ['id', 'code', 'name', 'teaching_prompt']

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'

class LearningObjectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningObjective
        fields = '__all__'

class SubtopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtopic
        fields = '__all__'

from blueprints.university.models import TeachingUnit
class CourseSerializer(serializers.ModelSerializer):
    enrolled_students = serializers.IntegerField(read_only=True)
    average_gpa = serializers.FloatField(read_only=True)
    teaching_units = serializers.PrimaryKeyRelatedField(queryset=TeachingUnit.objects.all(), many=True)
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'code', 'coordinator', 'teaching_prompt', 'teaching_units', 'enrolled_students', 'average_gpa']
    
    def create(self, validated_data):
        teaching_units = validated_data.pop('teaching_units', [])
        course = Course.objects.create(**validated_data)
        course.teaching_units.set(teaching_units)
        return course
class StudentSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    class Meta:
        model = Student
        fields = ("id", "name", "gpa", "status", "courses")
    def get_courses(self, obj):
        # Use the through relationship via enrollments; explicitly iterate to avoid ORM lookup issues.
        if hasattr(obj, 'enrollments'):
            return [enrollment.course.id for enrollment in obj.enrollments.all()]
        return []

class EnrollmentSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    teaching_unit = serializers.PrimaryKeyRelatedField(queryset=TeachingUnit.objects.all())
    class Meta:
        model = Enrollment
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy()
        if 'course' in data:
            data['teaching_unit'] = data.pop('course')
        return super().to_internal_value(data)

class AssessmentItemSerializer(serializers.ModelSerializer):
    formatted_weight = serializers.CharField(read_only=True)
    is_late_submission = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AssessmentItem
        fields = '__all__'