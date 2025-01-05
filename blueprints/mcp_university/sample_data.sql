-- blueprints/university/sample_data.sql

-- =====================================================
-- University Support System Sample Data
-- =====================================================

-- -----------------------------------------------------
-- Table: courses
-- Description: Contains detailed information about university courses.
-- -----------------------------------------------------

INSERT INTO courses (course_name, description, discipline) VALUES
('Introduction to Data Science', 
 'An introductory course that covers the fundamentals of data analysis, statistical methods, and machine learning techniques. Students will learn to manipulate and visualize data using Python and R.', 
 'Data Science'),

('Advanced Machine Learning', 
 'A comprehensive exploration of advanced machine learning algorithms, including deep learning, reinforcement learning, and natural language processing. Emphasis on practical applications and real-world problem solving.', 
 'Data Science'),

('Database Systems', 
 'This course delves into the design, implementation, and management of relational databases. Topics include SQL, normalization, indexing, transactions, and database security.', 
 'Computer Science'),

('Operating Systems', 
 'Study the principles and design of modern operating systems. Topics include process management, memory management, file systems, and concurrency.', 
 'Computer Science'),

('Calculus I', 
 'An introduction to differential and integral calculus. Topics include limits, derivatives, integrals, and the Fundamental Theorem of Calculus.', 
 'Mathematics'),

('Linear Algebra', 
 'Covers vector spaces, linear transformations, matrices, determinants, eigenvalues, and eigenvectors. Applications to engineering, physics, and computer science.', 
 'Mathematics'),

('Introduction to Psychology', 
 'Explores the basics of human behavior and mental processes. Topics include perception, cognition, emotion, development, and social interactions.', 
 'Psychology'),

('Creative Writing Workshop', 
 'A hands-on course designed to enhance creative writing skills. Students will engage in writing exercises, peer reviews, and study of various literary genres.', 
 'Arts'),

('Modern Art History', 
 'Examines the development of modern art from the late 19th century to the present. Focus on major movements, influential artists, and cultural impacts.', 
 'Arts'),

('Principles of Economics', 
 'Introduces microeconomic and macroeconomic principles. Topics include supply and demand, market structures, fiscal policy, and economic indicators.', 
 'Economics'),

('Business Statistics', 
 'Applies statistical methods to business problems. Topics include probability distributions, hypothesis testing, regression analysis, and decision-making under uncertainty.', 
 'Business'),

('Marketing Management', 
 'Covers the fundamentals of marketing strategy, consumer behavior, branding, and digital marketing. Emphasis on practical applications and case studies.', 
 'Business'),

('Environmental Science', 
 'Studies the interactions between humans and the environment. Topics include ecosystems, biodiversity, climate change, and sustainable practices.', 
 'Environmental Studies'),

('Introduction to Sociology', 
 'Explores the structure of societies, social relationships, and institutions. Topics include culture, socialization, stratification, and social change.', 
 'Sociology'),

('Human Anatomy', 
 'An in-depth study of the human body’s structure and function. Topics include organ systems, tissues, and cellular biology.', 
 'Biology'),

('Genetics', 
 'Covers the principles of heredity, gene expression, genetic variation, and molecular genetics. Applications in medicine, agriculture, and biotechnology.', 
 'Biology'),

('Philosophy of Science', 
 'Examines the philosophical foundations and implications of scientific inquiry. Topics include scientific method, theory confirmation, and the nature of scientific knowledge.', 
 'Philosophy'),

('Ethics in Technology', 
 'Discusses ethical issues arising from technological advancements. Topics include data privacy, artificial intelligence, and the societal impacts of emerging technologies.', 
 'Philosophy'),

('Creative Problem Solving', 
 'Enhances creative thinking and problem-solving skills through various methodologies and exercises. Emphasis on innovation and practical applications.', 
 'Engineering'),

('Robotics Engineering', 
 'Introduces the fundamentals of robotics, including mechanics, electronics, programming, and control systems. Hands-on projects to build and program robots.', 
 'Engineering'),

('Artificial Intelligence', 
 'Covers the basics of artificial intelligence, including search algorithms, knowledge representation, machine learning, and AI ethics.', 
 'Computer Science'),

('Data Structures and Algorithms', 
 'Explores essential data structures and algorithms for efficient problem solving. Topics include trees, graphs, sorting, searching, and algorithm complexity.', 
 'Computer Science'),

('Digital Signal Processing', 
 'Studies the processing of digital signals for applications in communications, audio, and image processing. Topics include Fourier transforms, filtering, and signal analysis.', 
 'Electrical Engineering'),

('Circuit Analysis', 
 'Introduces the principles of electrical circuits, including Ohm’s Law, Kirchhoff’s Laws, and circuit theorems. Practical applications in designing and analyzing circuits.', 
 'Electrical Engineering'),

('Thermodynamics', 
 'Covers the laws of thermodynamics, energy transfer, and the principles governing heat engines and refrigerators. Applications in engineering and physical sciences.', 
 'Physics'),

('Quantum Mechanics', 
 'An advanced course on the principles of quantum mechanics. Topics include wave functions, uncertainty principle, and quantum states.', 
 'Physics'),

('Astrophysics', 
 'Explores the physics of celestial objects and phenomena. Topics include stellar evolution, black holes, and cosmology.', 
 'Physics'),

('Microeconomics', 
 'Focuses on the behavior of individuals and firms in making decisions regarding the allocation of scarce resources. Topics include consumer theory, production theory, and market structures.', 
 'Economics'),

('Macroeconomics', 
 'Examines the performance, structure, and behaviour of the entire economy. Topics include GDP, unemployment, inflation, and monetary and fiscal policy.', 
 'Economics'),

('Financial Accounting', 
 'Introduces the principles of financial accounting, including the preparation and interpretation of financial statements.', 
 'Business'),

('Managerial Accounting', 
 'Focuses on accounting practices used for internal decision-making, including budgeting, forecasting, and performance evaluation.', 
 'Business'),

('Organisational Behaviour', 
 'Studies how individuals and groups behave within organisations. Topics include motivation, leadership, team dynamics, and organisational culture.', 
 'Business'),

('Human Resource Management', 
 'Covers the principles and practices of managing human resources in organisations. Topics include recruitment, training, performance management, and labour relations.', 
 'Business'),

('Public Speaking', 
 'Develops effective public speaking and presentation skills. Emphasis on speech writing, delivery techniques, and audience engagement.', 
 'Communication'),

('Interpersonal Communication', 
 'Explores the dynamics of interpersonal interactions. Topics include verbal and non-verbal communication, conflict resolution, and relationship building.', 
 'Communication'),

('Journalism', 
 'Introduces the principles of journalism, including news reporting, investigative journalism, and media ethics. Practical exercises in writing and reporting.', 
 'Communication'),

('Media Studies', 
 'Examines the role of media in society. Topics include media theory, digital media, and the impact of media on culture and politics.', 
 'Communication'),

('Introduction to Law', 
 'Provides an overview of the legal system, including the sources of law, legal reasoning, and basic principles of criminal and civil law.', 
 'Law'),

('Constitutional Law', 
 'Studies the structure and function of government as defined by the constitution. Topics include separation of powers, federalism, and individual rights.', 
 'Law'),

('International Relations', 
 'Explores the relationships between nations, including diplomacy, conflict, trade, and international organisations.', 
 'Political Science'),

('Political Theory', 
 'Examines the philosophical foundations of politics. Topics include justice, equality, democracy, and the role of the state.', 
 'Political Science'),

('Urban Planning', 
 'Introduces the principles of urban planning and development. Topics include land use, transportation planning, and sustainable city design.', 
 'Urban Studies'),

('Environmental Policy', 
 'Covers the development and implementation of policies aimed at managing environmental resources and addressing ecological issues.', 
 'Environmental Studies');

-- -----------------------------------------------------
-- Table: schedules
-- Description: Contains scheduling information for courses.
-- -----------------------------------------------------

INSERT INTO schedules (course_name, class_time, exam_date) VALUES
('Introduction to Data Science', 'Mon 10:00 AM - 12:00 PM', '2025-05-15'),
('Introduction to Data Science', 'Wed 10:00 AM - 12:00 PM', '2025-05-15'),
('Advanced Machine Learning', 'Tue 2:00 PM - 4:00 PM', '2025-06-20'),
('Advanced Machine Learning', 'Thu 2:00 PM - 4:00 PM', '2025-06-20'),
('Database Systems', 'Fri 1:00 PM - 3:00 PM', '2025-05-22'),
('Database Systems', 'Tue 9:00 AM - 11:00 AM', '2025-05-22'),
('Operating Systems', 'Wed 1:00 PM - 3:00 PM', '2025-06-18'),
('Operating Systems', 'Fri 9:00 AM - 11:00 AM', '2025-06-18'),
('Calculus I', 'Mon 9:00 AM - 11:00 AM', '2025-05-10'),
('Calculus I', 'Wed 9:00 AM - 11:00 AM', '2025-05-10'),
('Linear Algebra', 'Tue 11:00 AM - 1:00 PM', '2025-05-12'),
('Linear Algebra', 'Thu 11:00 AM - 1:00 PM', '2025-05-12'),
('Introduction to Psychology', 'Fri 2:00 PM - 4:00 PM', '2025-05-18'),
('Introduction to Psychology', 'Tue 2:00 PM - 4:00 PM', '2025-05-18'),
('Creative Writing Workshop', 'Mon 1:00 PM - 3:00 PM', '2025-05-25'),
('Creative Writing Workshop', 'Wed 1:00 PM - 3:00 PM', '2025-05-25'),
('Modern Art History', 'Thu 3:00 PM - 5:00 PM', '2025-06-05'),
('Modern Art History', 'Fri 3:00 PM - 5:00 PM', '2025-06-05'),
('Principles of Economics', 'Tue 10:00 AM - 12:00 PM', '2025-05-20'),
('Principles of Economics', 'Thu 10:00 AM - 12:00 PM', '2025-05-20'),
('Business Statistics', 'Mon 3:00 PM - 5:00 PM', '2025-05-28'),
('Business Statistics', 'Wed 3:00 PM - 5:00 PM', '2025-05-28'),
('Marketing Management', 'Fri 10:00 AM - 12:00 PM', '2025-06-15'),
('Marketing Management', 'Tue 1:00 PM - 3:00 PM', '2025-06-15'),
('Environmental Science', 'Thu 9:00 AM - 11:00 AM', '2025-05-30'),
('Environmental Science', 'Fri 9:00 AM - 11:00 AM', '2025-05-30'),
('Introduction to Sociology', 'Mon 11:00 AM - 1:00 PM', '2025-05-14'),
('Introduction to Sociology', 'Wed 11:00 AM - 1:00 PM', '2025-05-14'),
('Human Anatomy', 'Tue 3:00 PM - 5:00 PM', '2025-05-25'),
('Human Anatomy', 'Thu 3:00 PM - 5:00 PM', '2025-05-25'),
('Genetics', 'Fri 11:00 AM - 1:00 PM', '2025-06-10'),
('Genetics', 'Tue 11:00 AM - 1:00 PM', '2025-06-10'),
('Philosophy of Science', 'Mon 2:00 PM - 4:00 PM', '2025-05-22'),
('Philosophy of Science', 'Wed 2:00 PM - 4:00 PM', '2025-05-22'),
('Ethics in Technology', 'Thu 1:00 PM - 3:00 PM', '2025-06-12'),
('Ethics in Technology', 'Fri 1:00 PM - 3:00 PM', '2025-06-12'),
('Creative Problem Solving', 'Tue 9:00 AM - 11:00 AM', '2025-05-18'),
('Creative Problem Solving', 'Thu 9:00 AM - 11:00 AM', '2025-05-18'),
('Robotics Engineering', 'Mon 4:00 PM - 6:00 PM', '2025-06-22'),
('Robotics Engineering', 'Wed 4:00 PM - 6:00 PM', '2025-06-22'),
('Artificial Intelligence', 'Fri 4:00 PM - 6:00 PM', '2025-06-25'),
('Artificial Intelligence', 'Tue 4:00 PM - 6:00 PM', '2025-06-25'),
('Data Structures and Algorithms', 'Thu 2:00 PM - 4:00 PM', '2025-05-28'),
('Data Structures and Algorithms', 'Fri 2:00 PM - 4:00 PM', '2025-05-28'),
('Digital Signal Processing', 'Mon 5:00 PM - 7:00 PM', '2025-06-30'),
('Digital Signal Processing', 'Wed 5:00 PM - 7:00 PM', '2025-06-30'),
('Circuit Analysis', 'Tue 5:00 PM - 7:00 PM', '2025-06-02'),
('Circuit Analysis', 'Thu 5:00 PM - 7:00 PM', '2025-06-02'),
('Thermodynamics', 'Fri 5:00 PM - 7:00 PM', '2025-06-05'),
('Thermodynamics', 'Mon 5:00 PM - 7:00 PM', '2025-06-05'),
('Quantum Mechanics', 'Wed 10:00 AM - 12:00 PM', '2025-06-15'),
('Quantum Mechanics', 'Fri 10:00 AM - 12:00 PM', '2025-06-15'),
('Astrophysics', 'Tue 1:00 PM - 3:00 PM', '2025-06-18'),
('Astrophysics', 'Thu 1:00 PM - 3:00 PM', '2025-06-18'),
('Microeconomics', 'Mon 12:00 PM - 2:00 PM', '2025-05-19'),
('Microeconomics', 'Wed 12:00 PM - 2:00 PM', '2025-05-19'),
('Macroeconomics', 'Tue 12:00 PM - 2:00 PM', '2025-05-21'),
('Macroeconomics', 'Thu 12:00 PM - 2:00 PM', '2025-05-21'),
('Financial Accounting', 'Fri 3:00 PM - 5:00 PM', '2025-06-10'),
('Financial Accounting', 'Mon 3:00 PM - 5:00 PM', '2025-06-10'),
('Managerial Accounting', 'Wed 3:00 PM - 5:00 PM', '2025-06-12'),
('Managerial Accounting', 'Fri 3:00 PM - 5:00 PM', '2025-06-12'),
('Organisational Behaviour', 'Tue 4:00 PM - 6:00 PM', '2025-06-20'),
('Organisational Behaviour', 'Thu 4:00 PM - 6:00 PM', '2025-06-20'),
('Human Resource Management', 'Mon 6:00 PM - 8:00 PM', '2025-06-25'),
('Human Resource Management', 'Wed 6:00 PM - 8:00 PM', '2025-06-25'),
('Public Speaking', 'Fri 6:00 PM - 8:00 PM', '2025-06-27'),
('Public Speaking', 'Tue 6:00 PM - 8:00 PM', '2025-06-27'),
('Interpersonal Communication', 'Thu 6:00 PM - 8:00 PM', '2025-06-29'),
('Interpersonal Communication', 'Fri 6:00 PM - 8:00 PM', '2025-06-29'),
('Journalism', 'Mon 7:00 PM - 9:00 PM', '2025-07-02'),
('Journalism', 'Wed 7:00 PM - 9:00 PM', '2025-07-02'),
('Media Studies', 'Tue 7:00 PM - 9:00 PM', '2025-07-04'),
('Media Studies', 'Thu 7:00 PM - 9:00 PM', '2025-07-04'),
('Introduction to Law', 'Fri 7:00 PM - 9:00 PM', '2025-07-06'),
('Introduction to Law', 'Mon 7:00 PM - 9:00 PM', '2025-07-06'),
('Constitutional Law', 'Wed 8:00 PM - 10:00 PM', '2025-07-08'),
('Constitutional Law', 'Fri 8:00 PM - 10:00 PM', '2025-07-08'),
('International Relations', 'Tue 8:00 PM - 10:00 PM', '2025-07-10'),
('International Relations', 'Thu 8:00 PM - 10:00 PM', '2025-07-10'),
('Political Theory', 'Mon 8:00 PM - 10:00 PM', '2025-07-12'),
('Political Theory', 'Wed 8:00 PM - 10:00 PM', '2025-07-12'),
('Urban Planning', 'Fri 9:00 AM - 11:00 AM', '2025-07-14'),
('Urban Planning', 'Tue 9:00 AM - 11:00 AM', '2025-07-14'),
('Environmental Policy', 'Thu 9:00 AM - 11:00 AM', '2025-07-16'),
('Environmental Policy', 'Fri 9:00 AM - 11:00 AM', '2025-07-16');

