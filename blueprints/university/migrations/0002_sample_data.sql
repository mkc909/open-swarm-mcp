-- Sample Data Migration for blueprints_university
-- Inserting sample data into TeachingUnit
INSERT INTO blueprints_university_teachingunit (id, code, name, teaching_prompt) VALUES
(1, 'MTH101', 'Mathematics 101', 'Basic math principles'),
(2, 'PHY101', 'Physics 101', 'Introduction to physics');

-- Inserting sample data into Topic
INSERT INTO blueprints_university_topic (id, teaching_unit_id, name, teaching_prompt) VALUES
(1, 1, 'Algebra', 'Fundamental algebra concepts'),
(2, 1, 'Calculus', 'Introduction to derivatives and integrals');

-- Inserting sample data into LearningObjective
INSERT INTO blueprints_university_learningobjective (id, topic_id, description) VALUES
(1, 1, 'Understand linear equations'),
(2, 2, 'Gain basic understanding of derivatives');

-- Inserting sample data into Subtopic
INSERT INTO blueprints_university_subtopic (id, topic_id, name, teaching_prompt) VALUES
(1, 1, 'Linear Equations', 'Solving linear equations');

-- Inserting sample data into Course
INSERT INTO blueprints_university_course (id, name, code, coordinator, teaching_prompt) VALUES
(1, 'Bachelor of Science in Mathematics', 'BSMATH', 'Dr. Euler', 'Core course for mathematics degree');

-- Inserting sample data into Course-TeachingUnits M2M table
INSERT INTO blueprints_university_course_teaching_units (id, course_id, teachingunit_id) VALUES
(1, 1, 1);

-- Inserting sample data into Student
INSERT INTO blueprints_university_student (id, name, gpa, status) VALUES
(1, 'Alice', 3.50, 'active'),
(2, 'Bob', 3.80, 'active');

-- Inserting sample data into Enrollment
INSERT INTO blueprints_university_enrollment (id, student_id, course_id, enrollment_date, status) VALUES
(1, 1, 1, '2025-02-01', 'enrolled'),
(2, 2, 1, '2025-02-01', 'enrolled');

-- Inserting sample data into AssessmentItem
INSERT INTO blueprints_university_assessmentitem (id, enrollment_id, title, status, due_date, weight, submission_date) VALUES
(1, 1, 'Midterm Exam', 'pending', '2025-03-01 10:00:00', 20.00, NULL),
(2, 2, 'Midterm Exam', 'pending', '2025-03-01 10:00:00', 20.00, NULL);