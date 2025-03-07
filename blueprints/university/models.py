from django.db import models
from typing import TYPE_CHECKING
from django.db.models import Avg, Count, Q

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class TeachingUnit(models.Model):
    """Represents a teaching unit (e.g., a module or subject)."""
    code = models.CharField(
        max_length=20, unique=True, help_text="Unique code for the teaching unit (e.g., MTHS120)."
    )
    name = models.CharField(
        max_length=255, help_text="Descriptive name of the teaching unit (e.g., Calculus)."
    )
    teaching_prompt = models.TextField(
        blank=True, null=True, help_text="Instructions or guidelines for teaching this unit."
    )
    channel_id = models.CharField(
        max_length=20, blank=True, null=True, unique=True, help_text="Slack channel ID associated with this teaching unit (e.g., C123456)."
    )

    class Meta:
        app_label = "blueprints_university"
        db_table = "swarm_teachingunit"
        verbose_name = "Teaching Unit"
        verbose_name_plural = "Teaching Units"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Topic(models.Model):
    """Represents a specific topic within a TeachingUnit."""
    teaching_unit = models.ForeignKey(
        TeachingUnit, related_name="topics", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, help_text="Name of the topic.")
    teaching_prompt = models.TextField(
        blank=True, null=True, help_text="Instructions or guidelines for teaching this topic."
    )

    class Meta:
        app_label = "blueprints_university"
        db_table = "swarm_topic"
        verbose_name = "Topic"
        verbose_name_plural = "Topics"

    def __str__(self):
        return self.name


class LearningObjective(models.Model):
    """Represents a specific learning objective for a Topic."""
    topic = models.ForeignKey(
        Topic, related_name="learning_objectives", on_delete=models.CASCADE
    )
    description = models.TextField(help_text="Detailed description of the learning objective.")

    class Meta:
        app_label = "blueprints_university"
        db_table = "swarm_learningobjective"
        verbose_name = "Learning Objective"
        verbose_name_plural = "Learning Objectives"

    def __str__(self):
        return self.description


class Subtopic(models.Model):
    """Represents a subtopic within a Topic."""
    topic = models.ForeignKey(
        Topic, related_name="subtopics", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, help_text="Name of the subtopic.")
    teaching_prompt = models.TextField(
        blank=True, null=True, help_text="Instructions or guidelines for teaching this subtopic."
    )

    class Meta:
        app_label = "blueprints_university"
        db_table = "swarm_subtopic"
        verbose_name = "Subtopic"
        verbose_name_plural = "Subtopics"

    def __str__(self):
        return self.name


class Course(models.Model):
    """Represents a course program."""
    name = models.CharField(max_length=255, help_text="Name of the course (e.g., Bachelor of Science).")
    code = models.CharField(
        max_length=20, unique=True, help_text="Unique code for the course (e.g., BSCI)."
    )
    coordinator = models.CharField(max_length=255, help_text="Name of the course coordinator.")
    teaching_units = models.ManyToManyField(
        TeachingUnit,
        related_name="courses",
        help_text="Teaching units included in this course."
    )
    teaching_prompt = models.TextField(
        blank=True, null=True, help_text="Instructions or guidelines for teaching this course."
    )

    class Meta:
        app_label = "blueprints_university"
        db_table = "swarm_course"
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def enrolled_students_count(self):
        """Dynamically calculates the number of enrolled students."""
        return Student.objects.filter(enrollments__teaching_unit__in=self.teaching_units.all()).distinct().count()

    @property
    def average_gpa(self):
        """Dynamically calculates the average GPA for the course."""
        students_in_course = Student.objects.filter(enrollments__teaching_unit__in=self.teaching_units.all()).distinct()
        if students_in_course.exists():
            return students_in_course.aggregate(Avg('gpa'))['gpa__avg']
        else:
            return 0.0


class Student(models.Model):
    """Represents a student."""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('idle', 'Idle'),
    )
    name = models.CharField(max_length=255, help_text="Full name of the student.")
    gpa = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.0, help_text="Grade point average of the student."
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of the student.",
    )
    teaching_units = models.ManyToManyField(
        TeachingUnit, through='Enrollment', related_name="students", help_text="Teaching Units the student is enrolled in."
    )

    class Meta:
        app_label = "blueprints_university"
        db_table = "swarm_student"
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return self.name


def filter_students(name=None, status=None, unit_codes=None):
    """
    Filters students based on name, status, and enrolled units.
    Uses AND logic for all filters.
    """
    q = Q()
    if name:
        q &= Q(name__icontains=name)
    if status and status != 'all':
        q &= Q(status=status)
    if unit_codes and 'all' not in unit_codes:
        q &= Q(enrollments__teaching_unit__code__in=unit_codes)
    return Student.objects.filter(q).distinct()


class Enrollment(models.Model):
    """
    Represents the enrollment of a student in a Teaching Unit.
    This is a through model for the many-to-many relationship between Student and TeachingUnit.
    """
    STATUS_CHOICES = (
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    teaching_unit = models.ForeignKey(TeachingUnit, on_delete=models.CASCADE, related_name="enrollments")
    enrollment_date = models.DateField(auto_now_add=True, help_text="Date the student enrolled in the course.")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='enrolled',
        help_text="Enrollment status.",
    )

    class Meta:
        app_label = "blueprints_university"
        db_table = "swarm_enrollment"
        unique_together = ('student', 'teaching_unit')
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.student.name} - {self.teaching_unit.name}"


class AssessmentItem(models.Model):
    """Represents an individual assessment item (e.g., quiz, assignment)."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )
    enrollment = models.ForeignKey(Enrollment, related_name="assessments", on_delete=models.CASCADE)
    title = models.CharField(max_length=255, help_text="Title of the assessment (e.g., 'Midterm Exam').")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Completion status of the assessment.",
    )
    due_date = models.DateTimeField(help_text="Due date and time for the assessment.")
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Weight of the assessment as a percentage (e.g., 20.00)."
    )
    submission_date = models.DateTimeField(
        blank=True, null=True, help_text="Date and time the assessment was submitted."
    )

    class Meta:
        app_label = "blueprints_university"
        db_table = "swarm_assessmentitem"
        ordering = ["due_date"]
        verbose_name = "Assessment Item"
        verbose_name_plural = "Assessment Items"

    def __str__(self):
        return self.title

    @property
    def is_late_submission(self):
        """Checks if the assessment was submitted after the due date."""
        return self.submission_date and self.submission_date > self.due_date

    @property
    def formatted_weight(self):
        """Formats the weight as a percentage string."""
        return f"{self.weight}%"
