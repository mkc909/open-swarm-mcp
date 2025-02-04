# Use an Astral uv image with Python 3.13
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install Node.js and npm
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
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
RUN uv venv .venv && uv sync

# Expose the application port (default 8000, configurable via $PORT)
EXPOSE 8000

# Enable a 512MB swapfile if LOW_VRAM_MODE is set
# TODO custom filepath
RUN if [ "$LOW_VRAM_MODE" = "1" ]; then \
      mkdir -p /mnt/sqlite_data && \
      fallocate -l 512M /mnt/sqlite_data/swapfile && \
      chmod 600 /mnt/sqlite_data/swapfile && \
      mkswap /mnt/sqlite_data/swapfile && \
      echo "/mnt/sqlite_data/swapfile none swap sw 0 0" >> /etc/fstab; \
    fi

# Use shell form to allow environment variable substitution
CMD uv run manage.py migrate && uv run manage.py runserver 0.0.0.0:$PORT
