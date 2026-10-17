FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=2.1.1
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

# Configure Poetry to not create virtualenvs in container
RUN poetry config virtualenvs.create false

# Copy dependency manifests
COPY pyproject.toml poetry.lock ./

# Install runtime dependencies only
RUN poetry install --no-root --without dev,test --no-interaction --no-ansi

# Final lightweight stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime utilities (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create unprivileged application user
RUN groupadd -r appgroup && useradd -r -g appgroup -s /bin/false appuser

# Copy application source code and migrations
COPY app/ ./app
COPY migrations/ ./migrations
COPY alembic.ini ./

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
