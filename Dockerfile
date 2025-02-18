# syntax=docker/dockerfile:experimental
FROM python:3.10

# Build-time argument for port (default: 8000)
ARG PORT=8000
ENV PORT=${PORT}

# Install system dependencies required for building packages
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    libopenblas-dev \
    liblapack-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all project files into the container
COPY . .

# Install Poetry (using a specific version)
RUN pip install --no-cache-dir "poetry==1.8.2"

# Install blis explicitly without PEP517 support to avoid build issues
RUN pip install --no-cache-dir --no-use-pep517 blis==1.2.0

# Configure Poetry to install dependencies directly into the system environment
RUN poetry config virtualenvs.create false && \
    poetry install --all-extras --no-interaction --no-ansi && \
    poetry install --with dev --no-interaction --no-ansi

# Expose the specified port
EXPOSE ${PORT}

# Use shell form to allow environment variable substitution;
# if SWAPFILE_PATH is defined, create a swap file, then run Django migrations and start the server on the specified port.
CMD if [ -n "$SWAPFILE_PATH" ]; then \
      mkdir -p "$(dirname "$SWAPFILE_PATH")" && \
      fallocate -l 768M "$SWAPFILE_PATH" && \
      chmod 600 "$SWAPFILE_PATH" && \
      mkswap "$SWAPFILE_PATH" && \
      swapon "$SWAPFILE_PATH"; \
    fi && \
    python manage.py migrate && \
    python manage.py runserver 0.0.0.0:$PORT
