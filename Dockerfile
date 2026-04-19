# ── Build stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY backup.py config.py notifier.py logger.py stats.py ./

# Directorio de backups persistente
VOLUME ["/backups"]

RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
    CMD python3 -c "from config import Config; c = Config(); errors = c.validate(); exit(1 if errors else 0)"

CMD ["python3", "backup.py", "backup"]
