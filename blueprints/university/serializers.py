from rest_framework import serializers
from blueprints.university.models import (
    TeachingUnit, Topic, LearningObjective, Subtopic, Course, Student, Enrollment, AssessmentItem
)

class TeachingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachingUnit
        fields = '__all__'

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
        fields = '__all__'
    
    def create(self, validated_data):
        teaching_units = validated_data.pop('teaching_units', [])
        course = Course.objects.create(**validated_data)
        from blueprints.university.models import TeachingUnit
        for unit in teaching_units:
            # If 'unit' is not an instance (i.e., an integer), fetch the TeachingUnit instance.
            if not hasattr(unit, 'pk'):
                unit_instance = TeachingUnit.objects.get(pk=unit)
                course.teaching_units.add(unit_instance)
            else:
                course.teaching_units.add(unit)
        return course
class StudentSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    class Meta:
        model = Student
        fields = ("id", "name", "gpa", "status", "courses")
    def get_courses(self, obj):
        # Use the through relationship via enrollments instead of direct courses field
        if hasattr(obj, 'enrollments'):
            return list(obj.enrollments.values_list("course__id", flat=True))
        return []

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'

class AssessmentItemSerializer(serializers.ModelSerializer):
    formatted_weight = serializers.CharField(read_only=True)
    is_late_submission = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AssessmentItem
        fields = '__all__'