#!/usr/bin/env bash
# Ejemplos de uso de db-backup-notifier

# ── Configuración básica ──────────────────────────────────────────────────────
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=mysecret
export DB_NAME=mydb
export BACKUP_DIR=/var/backups/pg
export BACKUP_RETENTION=7
export TELEGRAM_BOT_TOKEN=123456:ABCdef...
export TELEGRAM_CHAT_ID=987654321
export NOTIFY_ON_SUCCESS=true
export PG_DUMP_TIMEOUT=300
export LOG_LEVEL=INFO

# ── Ejecutar backup completo ──────────────────────────────────────────────────
echo "=== Backup completo ==="
python3 backup.py backup

# ── Listar backups en formato tabla ──────────────────────────────────────────
echo ""
echo "=== Backups existentes (tabla) ==="
python3 backup.py list --output table

# ── Listar backups en JSON (útil para scripts) ────────────────────────────────
echo ""
echo "=== Backups en JSON ==="
python3 backup.py list --output json

# ── Ver estadísticas ──────────────────────────────────────────────────────────
echo ""
echo "=== Estadísticas ==="
python3 backup.py stats --output table

# ── Solo rotar (sin backup) ───────────────────────────────────────────────────
echo ""
echo "=== Rotación ==="
python3 backup.py rotate --output table

# ── Con verbose para debugging ────────────────────────────────────────────────
echo ""
echo "=== Backup verbose ==="
python3 backup.py backup --verbose

# ── Docker (cron diario a las 03:00 UTC) ─────────────────────────────────────
: <<'DOCKER_EXAMPLE'
docker run --rm \
  -e DB_HOST=myhost \
  -e DB_USER=myuser \
  -e DB_PASSWORD=mypass \
  -e DB_NAME=mydb \
  -e TELEGRAM_BOT_TOKEN=xxx \
  -e TELEGRAM_CHAT_ID=yyy \
  -v /var/backups/pg:/backups \
  db-backup-notifier
DOCKER_EXAMPLE
