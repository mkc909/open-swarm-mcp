import uuid
import pytest
from swarm.models import TeachingUnit, Topic, LearningObjective, Subtopic, Course, Student, Enrollment, AssessmentItem, ChatConversation, ChatMessage

@pytest.mark.django_db
def test_teaching_unit_creation():
    tu = TeachingUnit.objects.create(code="MTH101", name="Mathematics 101", teaching_prompt="Introduction to Math")
    assert tu.pk is not None
    assert str(tu) == "MTH101 - Mathematics 101"

@pytest.mark.django_db
def test_topic_and_learning_objective_creation():
    tu = TeachingUnit.objects.create(code="PHY101", name="Physics", teaching_prompt="Physics basics")
    topic = Topic.objects.create(teaching_unit=tu, name="Mechanics", teaching_prompt="Study of forces")
    lo = LearningObjective.objects.create(topic=topic, description="Understand Newton's laws")
    subtopic = Subtopic.objects.create(topic=topic, name="Kinematics", teaching_prompt="Motion study")
    assert topic.pk is not None
    assert lo.pk is not None
    assert subtopic.pk is not None

@pytest.mark.django_db
def test_course_and_enrollment():
    tu = TeachingUnit.objects.create(code="CSC101", name="Computer Science", teaching_prompt="Intro to CS")
    course = Course.objects.create(name="BSc Computer Science", code="BSC-CS", coordinator="Prof. X", teaching_prompt="Course prompt")
    course.teaching_units.add(tu)
    student = Student.objects.create(name="Alice", gpa="3.5", status="active")
    enrollment = Enrollment.objects.create(student=student, course=course, status="enrolled")
    assert enrollment.pk is not None
    # Verify that the property correctly counts enrolled students
    assert course.enrolled_students == 1

@pytest.mark.django_db
def test_assessment_item():
    tu = TeachingUnit.objects.create(code="ENG101", name="English", teaching_prompt="Basic English")
    course = Course.objects.create(name="BA English", code="BA-ENG", coordinator="Dr. Y", teaching_prompt="Course prompt")
    student = Student.objects.create(name="Bob", gpa="3.0", status="active")
    enrollment = Enrollment.objects.create(student=student, course=course, status="enrolled")
    assessment = AssessmentItem.objects.create(
        enrollment=enrollment,
        title="Midterm Exam",
        status="pending",
        due_date="2025-07-01T00:00:00Z",
        weight="25.00"
    )
    assert assessment.pk is not None
    assert assessment.formatted_weight == "25.00%"

@pytest.mark.django_db
def test_chat_conversation_and_messages():
    conversation = ChatConversation.objects.create(conversation_id=str(uuid.uuid4()))
    ChatMessage.objects.create(conversation=conversation, sender="user", content="Hello!")
    ChatMessage.objects.create(conversation=conversation, sender="assistant", content="Hi there.")
    assert conversation.messages.count() == 2
    # Test cascade delete: deleting the conversation should remove its messages
    conversation.delete()
    assert ChatMessage.objects.filter(conversation=conversation).count() == 0