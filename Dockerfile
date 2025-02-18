FROM python:3.10

# Build argument and environment variable for runtime port (default: 8000)
ARG PORT=8000
ENV PORT=${PORT}

# Install system-level build dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    libopenblas-dev \
    liblapack-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all project files into the container
COPY . .

# Upgrade pip for best compatibility
RUN pip install --upgrade pip

# Install BLIS explicitly without PEP517 support (to avoid build issues)
RUN pip install --no-cache-dir --no-use-pep517 blis==1.2.0

# Install the project along with its dependencies declared in [project]
# This uses your Hatchling build backend as specified in pyproject.toml
RUN pip install .

# Expose the specified port
EXPOSE ${PORT}

# Use shell form to allow environment variable substitution:
# if SWAPFILE_PATH is defined, create a swap file, then run Django migrations and start the server.
CMD if [ -n "$SWAPFILE_PATH" ]; then \
      mkdir -p "$(dirname "$SWAPFILE_PATH")" && \
      fallocate -l 768M "$SWAPFILE_PATH" && \
      chmod 600 "$SWAPFILE_PATH" && \
      mkswap "$SWAPFILE_PATH" && \
      swapon "$SWAPFILE_PATH"; \
    fi && \
    python manage.py migrate && \
    python manage.py runserver 0.0.0.0:$PORT
