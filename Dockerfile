# Use an Astral uv image with Python 3.13
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install necessary packages
RUN apt-get update && apt-get install -y \
    cargo \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy uvx alongside uv
COPY --from=ghcr.io/astral-sh/uv:latest /uvx /bin/

# Set working directory inside the container
WORKDIR /app

# Copy project files
COPY . .

# Set environment variables
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/app/.venv/bin:$PATH"
ENV POETRY_VERSION=1.8.2

# Install dependencies using uv
RUN uv pip install poetry==$POETRY_VERSION
RUN poetry config virtualenvs.create false && \
    poetry install --all-extras --no-interaction --no-ansi && \
    poetry install --with dev --no-interaction --no-ansi

# Download the `all-MiniLM-L6-v2` model
RUN python -c "from fastembed.embedding import FlagEmbedding; FlagEmbedding('sentence-transformers/all-MiniLM-L6-v2');"

# Ensure the entry point is installed as a script
RUN poetry install --all-extras --no-interaction --no-ansi

# Expose the application port
EXPOSE 8000

# Use shell form to allow environment variable substitution
CMD if [ -n "$SWAPFILE_PATH" ]; then \
      mkdir -p "$(dirname "$SWAPFILE_PATH")" && \
      fallocate -l 768M "$SWAPFILE_PATH" && \
      chmod 600 "$SWAPFILE_PATH" && \
      mkswap "$SWAPFILE_PATH" && \
      swapon "$SWAPFILE_PATH"; \
    fi && \
    uv run manage.py migrate && \
    uv run manage.py runserver 0.0.0.0:$PORT
