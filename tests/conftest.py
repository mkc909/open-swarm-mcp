import os
import uuid

# Set up a unique test database for each test suite run.
os.environ["UNIT_TESTING"] = "true"
os.environ["SQLITE_DB_PATH"] = f"./swarm-django-{uuid.uuid4().hex}.db"