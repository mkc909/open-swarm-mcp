# Use an Astral uv image with Python 3.13
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install cargo (needed for nemoguardrails)
RUN apt-get update && apt-get install -y \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Copy uvx alongside uv
COPY --from=ghcr.io/astral-sh/uv:latest /uvx /bin/

# Set working directory inside the container
WORKDIR /app

# Copy project files (exclude .env via .dockerignore)
COPY . .

# Set environment variables to prioritise using the uv environment
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies using uv and create the environment
#RUN uv venv .venv && uv sync

# Expose the application port (default 8000, configurable via $PORT)
EXPOSE 8000

# Use shell form to allow environment variable substitution
CMD if [ -n "$SWAPFILE_PATH" ]; then \
      mkdir -p "$(dirname "$SWAPFILE_PATH")" && \
      fallocate -l 512M "$SWAPFILE_PATH" && \
      chmod 600 "$SWAPFILE_PATH" && \
      mkswap "$SWAPFILE_PATH" && \
      swapon "$SWAPFILE_PATH"; \
    fi && \
    uv run manage.py migrate && \
    uv run manage.py runserver 0.0.0.0:$PORT