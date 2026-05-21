# =============================================================================
# AI多Agent教材编写系统 - 生产环境 Dockerfile
# =============================================================================

FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.11-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1001 textbook && \
    useradd --system --uid 1001 --gid textbook --shell /bin/bash --create-home textbook

WORKDIR /app

RUN mkdir -p /app/src /app/config /app/scripts && chown -R textbook:textbook /app

COPY --from=builder /install /usr/local
COPY --chown=textbook:textbook pyproject.toml conftest.py .env.example .env* ./
COPY --chown=textbook:textbook src/ ./src/
COPY --chown=textbook:textbook scripts/ ./scripts/
COPY --chown=textbook:textbook config/ ./config/

USER textbook:1001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -sf http://localhost:8000/healthz || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]