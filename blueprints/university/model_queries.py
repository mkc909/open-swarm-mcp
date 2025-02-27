import logging
import json
from typing import Dict, Any, List, Optional
import django
from django.db.models import Q

from blueprints.university.models import Course, Student, TeachingUnit, Topic, LearningObjective, Subtopic, Enrollment, AssessmentItem

# Configure logging with detailed debug information for troubleshooting
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

def search_courses(query: str) -> List[Dict[str, Any]]:
    """
    Query the Course model with a meticulous search process, logging every detail of the query,
    result set, and potential failures to ensure comprehensive tracking and auditing, using Django ORM.
    """
    logger.debug(f"Searching courses with query: {query}")
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str, raising type safety error")
        raise ValueError("Query must be a string, ensuring strict type safety across the system")
    if not query:
        logger.warning("Empty query provided for course search, returning an empty result set")
        return []

    try:
        qs = Course.objects.filter(
            Q(name__icontains=query) | Q(code__icontains=query) | Q(coordinator__icontains=query)
        )
        results = list(qs.values("code", "name", "coordinator"))
        logger.debug(f"Course search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error searching courses for query '{query}': {str(e)}", exc_info=True)
        raise

def search_students(query: str) -> List[Dict[str, Any]]:
    """
    Query the Student model with a detailed search process, logging operations and potential failures.
    """
    logger.debug(f"Searching students with query: {query}")
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str, raising type safety error")
        raise ValueError("Query must be a string, ensuring strict type enforcement")
    if not query:
        logger.warning("Empty query provided for student search, returning an empty result set")
        return []

    try:
        qs = Student.objects.filter(Q(name__icontains=query))
        results = list(qs.values("name", "gpa", "status"))
        logger.debug(f"Student search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error searching students for query '{query}': {str(e)}", exc_info=True)
        raise

def search_teaching_units(query: Optional[str]) -> List[Dict[str, Any]]:
    """
    Query the TeachingUnit model, allowing None to search for units with undefined (NULL) channel_id.
    Logs every operation and potential failure for comprehensive auditing, using Django ORM.
    """
    logger.debug(f"Searching teaching units with query: {query}")
    if query is not None and not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str or None, raising type safety error")
        raise ValueError("Query must be a string or None, ensuring strict type safety")
    
    try:
        if query is None:
            logger.debug("Query is None, searching for teaching units with NULL channel_id")
            qs = TeachingUnit.objects.filter(channel_id__isnull=True)
        elif not query:
            logger.warning("Empty query provided for teaching unit search, returning an empty result set")
            return []
        else:
            logger.debug(f"Performing standard search with query: {query}")
            qs = TeachingUnit.objects.filter(Q(code__icontains=query) | Q(name__icontains=query))

        results = list(qs.values("code", "name", "channel_id", "teaching_prompt", "id"))
        logger.debug(f"Teaching unit search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error searching teaching units for query '{query}': {str(e)}", exc_info=True)
        raise

def search_topics(query: str) -> List[Dict[str, Any]]:
    """
    Query the Topic model with a detailed search process, logging operations and potential failures.
    """
    logger.debug(f"Searching topics with query: {query}")
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str, raising type safety error")
        raise ValueError("Query must be a string, ensuring strict type enforcement")
    if not query:
        logger.warning("Empty query provided for topic search, returning an empty result set")
        return []

    try:
        qs = Topic.objects.filter(Q(name__icontains=query))
        results = list(qs.values("name"))
        logger.debug(f"Topic search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error searching topics for query '{query}': {str(e)}", exc_info=True)
        raise

def search_learning_objectives(query: str) -> List[Dict[str, Any]]:
    """
    Query the LearningObjective model with a meticulous search process, logging operations and failures.
    """
    logger.debug(f"Searching learning objectives with query: {query}")
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str, raising type safety error")
        raise ValueError("Query must be a string, ensuring strict type safety")
    if not query:
        logger.warning("Empty query provided for learning objective search, returning an empty result set")
        return []

    try:
        qs = LearningObjective.objects.filter(Q(description__icontains=query))
        results = list(qs.values("description"))
        logger.debug(f"Learning objective search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error searching learning objectives for query '{query}': {str(e)}", exc_info=True)
        raise

def search_subtopics(query: str) -> List[Dict[str, Any]]:
    """
    Query the Subtopic model with a detailed search process, logging operations and potential failures.
    """
    logger.debug(f"Searching subtopics with query: {query}")
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str, raising type safety error")
        raise ValueError("Query must be a string, ensuring strict type enforcement")
    if not query:
        logger.warning("Empty query provided for subtopic search, returning an empty result set")
        return []

    try:
        qs = Subtopic.objects.filter(Q(name__icontains=query))
        results = list(qs.values("name"))
        logger.debug(f"Subtopic search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error searching subtopics for query '{query}': {str(e)}", exc_info=True)
        raise

def search_enrollments(query: str) -> List[Dict[str, Any]]:
    """
    Query the Enrollment model with a meticulous search process, logging operations and failures.
    """
    logger.debug(f"Searching enrollments with query: {query}")
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str, raising type safety error")
        raise ValueError("Query must be a string, ensuring strict type safety")
    if not query:
        logger.warning("Empty query provided for enrollment search, returning an empty result set")
        return []

    try:
        qs = Enrollment.objects.filter(Q(status__icontains=query))
        results = list(qs.values("status", "enrollment_date"))
        logger.debug(f"Enrollment search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error searching enrollments for query '{query}': {str(e)}", exc_info=True)
        raise

def search_assessment_items(query: str) -> List[Dict[str, Any]]:
    """
    Query the AssessmentItem model with a detailed search process, logging operations and failures.
    """
    logger.debug(f"Searching assessment items with query: {query}")
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str, raising type safety error")
        raise ValueError("Query must be a string, ensuring strict type enforcement")
    if not query:
        logger.warning("Empty query provided for assessment item search, returning an empty result set")
        return []

    try:
        qs = AssessmentItem.objects.filter(Q(title__icontains=query))
        results = list(qs.values("title", "status", "due_date"))
        logger.debug(f"Assessment item search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error searching assessment items for query '{query}': {str(e)}", exc_info=True)
        raise

def extended_comprehensive_search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Perform an extended comprehensive search across all university models, logging every detail.
    """
    logger.debug(f"Performing extended comprehensive search with query: {query}")
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str, raising type safety error")
        raise ValueError("Query must be a string, ensuring strict type safety")
    if not query:
        logger.warning("Empty query provided for extended search, returning an empty result set")
        return {
            "courses": [],
            "students": [],
            "teaching_units": [],
            "topics": [],
            "learning_objectives": [],
            "subtopics": [],
            "enrollments": [],
            "assessment_items": [],
        }

    try:
        results = {
            "courses": search_courses(query),
            "students": search_students(query),
            "teaching_units": search_teaching_units(query),
            "topics": search_topics(query),
            "learning_objectives": search_learning_objectives(query),
            "subtopics": search_subtopics(query),
            "enrollments": search_enrollments(query),
            "assessment_items": search_assessment_items(query),
        }
        logger.debug(f"Extended search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error in extended comprehensive search for query '{query}': {str(e)}", exc_info=True)
        raise

def comprehensive_search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Perform a comprehensive search across courses and students, logging every detail.
    """
    logger.debug(f"Performing comprehensive search with query: {query}")
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected str, raising type safety error")
        raise ValueError("Query must be a string, ensuring strict type enforcement")
    if not query:
        logger.warning("Empty query provided for comprehensive search, returning an empty result set")
        return {"courses": [], "students": []}

    try:
        results = {
            "courses": search_courses(query),
            "students": search_students(query)
        }
        logger.debug(f"Comprehensive search results for query '{query}': {json.dumps(results, indent=4)}")
        return results
    except Exception as e:
        logger.error(f"Error in comprehensive search for query '{query}': {str(e)}", exc_info=True)
        raise