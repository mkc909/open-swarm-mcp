# syntax=docker/dockerfile:experimental

# NeMo Guardrails build stage
FROM python:3.10 AS nemo-builder

# Install git and gcc/g++ for annoy
RUN apt-get update && apt-get install -y git gcc g++ git

WORKDIR /app
RUN git clone https://github.com/NVIDIA/NeMo-Guardrails/ && cp -pvr NeMo-Guardrails /nemoguardrails 
WORKDIR /nemoguardrails

# Set POETRY_VERSION and NEMO_VERSION environment variables
ENV POETRY_VERSION=1.8.2
ARG NEMO_VERSION=0.11.0

RUN if [ "$(uname -m)" = "x86_64" ]; then \
  export ANNOY_COMPILER_ARGS="-D_CRT_SECURE_NO_WARNINGS,-DANNOYLIB_MULTITHREADED_BUILD,-march=x86-64"; \
  fi

# Install Poetry
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

# Copy project files
RUN poetry config virtualenvs.create false && \
    poetry install --all-extras --no-interaction --no-ansi && \
    poetry install --with dev --no-interaction --no-ansi

# Run app.py when the container launches
WORKDIR /nemoguardrails

# Download the `all-MiniLM-L6-v2` model
RUN python -c "from fastembed.embedding import FlagEmbedding; FlagEmbedding('sentence-transformers/all-MiniLM-L6-v2');"

#RUN nemoguardrails --help
# Ensure the entry point is installed as a script
RUN poetry install --all-extras --no-interaction --no-ansi

# Final stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Copy uvx alongside uv
#COPY --from=ghcr.io/astral-sh/uv:latest /uvx /bin/

# Copy NeMo Guardrails files from the builder stage
COPY --from=nemo-builder /nemoguardrails /app/nemoguardrails
COPY --from=nemo-builder /root/.cache /root/.cache

# Set working directory inside the container
WORKDIR /app

# Copy project files
COPY . .

# Set environment variables
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/app/nemoguardrails/bin:$PATH"
ENV PYTHONPATH="/app/nemoguardrails:$PYTHONPATH"

# Update pyproject.toml with the specific NeMo Guardrails version
#ARG NEMO_VERSION=0.11.0
#RUN sed -i "s/nemoguardrails>=0.11.0/nemoguardrails==${NEMO_VERSION}/g" pyproject.toml

# TODO optimise
# Install git and gcc/g++ for annoy
RUN apt-get update && apt-get install -y gcc g++ git cargo

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
