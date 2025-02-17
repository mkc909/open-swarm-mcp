# Build stage for NeMo Guardrails
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS nemo-builder

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

# Copy NeMo Guardrails pyproject.toml and poetry.lock
COPY ./NeMo-pyproject.toml ./poetry.lock ./

# Set environment variables
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/app/.venv/bin:$PATH"

# Install NeMo Guardrails dependencies using uv
RUN uv pip install --pyproject pyproject.toml

# Download the `all-MiniLM-L6-v2` model
RUN python -c "from fastembed.embedding import FlagEmbedding; FlagEmbedding('sentence-transformers/all-MiniLM-L6-v2');"

# Final stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Copy uvx alongside uv
COPY --from=ghcr.io/astral-sh/uv:latest /uvx /bin/

# Copy NeMo Guardrails environment from the builder stage
COPY --from=nemo-builder /app/.venv /app/.venv
COPY --from=nemo-builder /root/.cache /root/.cache

# Set working directory inside the container
WORKDIR /app

# Copy project files
COPY . .

# Set environment variables
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/app/.venv/bin:$PATH"

# Install Django app dependencies using uv
RUN uv sync

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
