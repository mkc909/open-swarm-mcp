FROM python:3.11-slim

# Build-time argument for runtime port (default: 8000)
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

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install BLIS explicitly (do not disable PEP 517 processing)
RUN pip install --no-cache-dir blis==1.2.0

# Install the project along with its dependencies using the build backend defined in pyproject.toml
RUN pip install .

# Expose the specified port
EXPOSE ${PORT}

# If SWAPFILE_PATH is defined, create a swap file, then run Django migrations and start the server.
CMD if [ -n "$SWAPFILE_PATH" ]; then \
      mkdir -p "$(dirname "$SWAPFILE_PATH")" && \
      fallocate -l 768M "$SWAPFILE_PATH" && \
      chmod 600 "$SWAPFILE_PATH" && \
      mkswap "$SWAPFILE_PATH" && \
      swapon "$SWAPFILE_PATH"; \
    fi && \
    python manage.py migrate && \
    python manage.py runserver 0.0.0.0:$PORT
