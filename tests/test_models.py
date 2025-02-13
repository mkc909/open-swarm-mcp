import pytest
import uuid
from django.utils import timezone
from swarm.models import ChatConversation, ChatMessage

@pytest.mark.django_db
def test_create_chat_conversation():
    """Ensure a new ChatConversation can be created with a UUID."""
    conversation = ChatConversation.objects.create(conversation_id=uuid.uuid4())
    assert isinstance(conversation.conversation_id, uuid.UUID)
    assert ChatConversation.objects.count() == 1

@pytest.mark.django_db
def test_add_message_to_conversation():
    """Verify that ChatMessage can be linked to a conversation."""
    conversation = ChatConversation.objects.create(conversation_id=uuid.uuid4())
    message = ChatMessage.objects.create(
        conversation=conversation,
        sender="user",
        content="Hello, world!"
    )
    assert message in conversation.messages.all()
    assert ChatMessage.objects.count() == 1

@pytest.mark.django_db
def test_message_ordering():
    """Ensure messages are ordered correctly by timestamp."""
    conversation = ChatConversation.objects.create(conversation_id=uuid.uuid4())
    ChatMessage.objects.create(conversation=conversation, sender="user", content="First")
    ChatMessage.objects.create(conversation=conversation, sender="assistant", content="Second")

    messages = list(conversation.messages.all().order_by("timestamp"))
    assert messages[0].content == "First"
    assert messages[1].content == "Second"

@pytest.mark.django_db
def test_retrieve_chat_history():
    """Fetch conversation history and verify its integrity."""
    conversation = ChatConversation.objects.create(conversation_id=uuid.uuid4())
    ChatMessage.objects.create(conversation=conversation, sender="user", content="Message 1")
    ChatMessage.objects.create(conversation=conversation, sender="assistant", content="Message 2")

    retrieved_conversation = ChatConversation.objects.get(conversation_id=conversation.conversation_id)
    messages = retrieved_conversation.messages.all()
    
    assert len(messages) == 2
    assert messages[0].sender == "user"
    assert messages[1].sender == "assistant"

@pytest.mark.django_db
def test_cascade_delete_conversation():
    """Ensure deleting a conversation deletes all related messages."""
    conversation = ChatConversation.objects.create(conversation_id=uuid.uuid4())
    ChatMessage.objects.create(conversation=conversation, sender="user", content="Hello")

    assert ChatMessage.objects.count() == 1
    conversation.delete()
    assert ChatMessage.objects.count() == 0  # Messages should be deleted with the conversation

@ pytest.mark.django_db
def test_course_average_gpa_and_enrolled_students():
    from decimal import Decimal
    from swarm.models import Course, Student, Enrollment

    course = Course.objects.create(
        code="CS101",
        name="Introduction to Computer Science",
        coordinator="Dr. Smith"
    )
    student1 = Student.objects.create(name="Alice", gpa=Decimal('3.50'), status="active")
    student2 = Student.objects.create(name="Bob", gpa=Decimal('4.00'), status="active")
    Enrollment.objects.create(student=student1, course=course)
    Enrollment.objects.create(student=student2, course=course)
    assert course.enrolled_students == 2
    # Calculate expected average GPA: (3.50 + 4.00) / 2 = 3.75
    assert float(course.average_gpa) == pytest.approx(3.75, rel=1e-2)

@pytest.mark.django_db
def test_filter_students():
   from decimal import Decimal
   from swarm.models import TeachingUnit, Course, Student, Enrollment, filter_students

   # Setup teaching unit and course
   tu = TeachingUnit.objects.create(code="TU101", name="Test Unit")
   course = Course.objects.create(code="C101", name="Test Course", coordinator="Test Coordinator")
   course.teaching_units.add(tu)

   # Create students
   student1 = Student.objects.create(name="Alice", gpa=Decimal('3.0'), status="active")
   student2 = Student.objects.create(name="Bob", gpa=Decimal('3.5'), status="idle")
   student3 = Student.objects.create(name="Charlie", gpa=Decimal('3.3'), status="active")
   
   # Enroll all students in the course
   Enrollment.objects.create(student=student1, course=course)
   Enrollment.objects.create(student=student2, course=course)
   Enrollment.objects.create(student=student3, course=course)

   # Filter by name (case insensitive)
   res = filter_students(name="alice")
   assert list(res) == [student1]

   # Filter by status "active"
   res = filter_students(status="active")
   assert set(res) == {student1, student3}

   # Filter by teaching unit code
   res = filter_students(unit_codes=["TU101"])
   assert set(res) == {student1, student2, student3}

   # Combined filter: name contains "a" and status "active"
   res = filter_students(name="a", status="active")
   assert set(res) == {student1, student3}

@pytest.mark.django_db
def test_assessment_item_properties():
    """Test the properties of AssessmentItem: is_late_submission and formatted_weight."""
    from decimal import Decimal
    from datetime import timedelta
    now = timezone.now()
    from swarm.models import Course, Student, Enrollment, AssessmentItem

    course = Course.objects.create(code="TEST101", name="Test Course", coordinator="Dr. Test")
    student = Student.objects.create(name="Test Student", gpa=Decimal('3.00'), status="active")
    enrollment = Enrollment.objects.create(student=student, course=course)

    assessment_late = AssessmentItem.objects.create(
         enrollment=enrollment,
         title="Late Assessment",
         status="completed",
         due_date=now + timedelta(days=1),
         weight=Decimal('20.00'),
         submission_date=now + timedelta(days=2)
    )

    assessment_on_time = AssessmentItem.objects.create(
         enrollment=enrollment,
         title="On Time Assessment",
         status="completed",
         due_date=now + timedelta(days=1),
         weight=Decimal('10.50'),
         submission_date=now + timedelta(hours=12)
    )
    
    assert assessment_late.is_late_submission is True
    assert assessment_on_time.is_late_submission is False
    assert assessment_late.formatted_weight == "20.00%"
    assert assessment_on_time.formatted_weight == "10.50%"
