# Use an Astral uv image with Python 3.13
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set working directory inside the container
WORKDIR /app

# Copy project files (exclude .env via .dockerignore)
COPY . .

# Set environment variables to prioritise using the uv environment
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies using uv and create the environment
RUN uv venv .venv && uv sync

# Expose the application port (default 8000, configurable via $PORT)
EXPOSE 8000

# Use shell form to allow environment variable substitution
CMD uv run manage.py runserver 0.0.0.0:$PORT
