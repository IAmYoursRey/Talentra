# =============================================================
# TALENTRA.ID Backend Production Dockerfile
# Multi-stage, non-root user, lean runtime container
# =============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime image
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/talentra/.local/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Run as non-root user
RUN groupadd -g 1001 talentra && \
    useradd -u 1001 -g talentra -m -s /bin/bash talentra

COPY --from=builder --chown=talentra:talentra /root/.local /home/talentra/.local
COPY --chown=talentra:talentra app/ /app/app/
COPY --chown=talentra:talentra alembic/ /app/alembic/
COPY --chown=talentra:talentra alembic.ini /app/alembic.ini

USER talentra

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
