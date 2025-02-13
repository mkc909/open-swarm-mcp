from rest_framework import serializers
from .models import ChatMessage, TeachingUnit, Topic, LearningObjective, Subtopic, Course, Student, Enrollment, AssessmentItem, ChatConversation

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'

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

class CourseSerializer(serializers.ModelSerializer):
    enrolled_students = serializers.IntegerField(read_only=True)
    average_gpa = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

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

class ChatConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatConversation
        fields = '__all__'