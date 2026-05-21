# =============================================================================
# AI多Agent教材编写系统 - 生产环境 Dockerfile
# Multi-stage build: builder → runner
# =============================================================================

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_IGNORE_INSTALLED=0

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --prefix=/install \
    -r pyproject.toml

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PYTHONPATH=/app \
    PYTHONFAULTHANDLER=0 \
    PYTHONHASHSEED=random \
    PYTHONOPTIMIZE=2

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean -y

RUN groupadd --system --gid 1001 textbook && \
    useradd --system --uid 1001 --gid textbook --shell /bin/bash --create-home textbook

WORKDIR /app

RUN mkdir -p /app/src /app/config /app/scripts /app/static /app/templates && \
    chown -R textbook:textbook /app

COPY --from=builder /install /usr/local
COPY --chown=textbook:textbook pyproject.toml conftest.py .env.example .env* ./

COPY --chown=textbook:textbook src/ ./src/
COPY --chown=textbook:textbook scripts/ ./scripts/
COPY --chown=textbook:textbook config/ ./config/

RUN chmod +x /app/scripts/*.sh 2>/dev/null || true && \
    chmod 755 /app/scripts/healthcheck.sh 2>/dev/null || true

USER textbook:1001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/scripts/healthcheck.sh || exit 1

VOLUME ["/app/static", "/app/data"]

ENTRYPOINT ["/app/scripts/start.sh"]