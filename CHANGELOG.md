# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

## [1.1.0] — 2026-04-19

### Añadido
- Módulo `logger.py`: logger estructurado con `LOG_LEVEL` env var y timestamps UTC
- Módulo `stats.py`: estadísticas de backups (count, tamaño total/promedio, oldest/newest, slots_used)
- Comando `stats` en CLI con flags `--output json|table`
- Flag `--output json|table` en comandos `list` y `rotate`
- Flag `--verbose` / `-v` para habilitar DEBUG logging desde CLI
- Configuración `PG_DUMP_TIMEOUT` (default 300s) — **fix crítico**: pg_dump ya no puede colgar indefinidamente
- Validación de `BACKUP_RETENTION` inválido (no numérico → fallback a 7, cero → 1)
- Validación de `DB_PORT` fuera de rango y `PG_DUMP_TIMEOUT` < 10s en `config.validate()`
- Reintentos automáticos en `TelegramNotifier.send()` (configurable, default 2 reintentos con backoff)
- Dockerfile multi-stage con usuario no-root (`appuser`) y `HEALTHCHECK`
- CI con GitHub Actions (Python 3.10 / 3.11 / 3.12)
- `pyproject.toml` con versión 1.1.0
- `LICENSE` MIT
- `setup.sh` para instalación rápida
- `examples/run_backup.sh` con casos de uso reales
- `ARCHITECTURE.md` con decisiones de diseño
- Makefile expandido: `make dev`, `make docker`, `make stats`, `make clean`, `make help`

### Corregido
- `datetime.utcnow()` deprecado → `datetime.now(timezone.utc)`
- `subprocess.run()` sin timeout podía colgar indefinidamente con BD no disponible
- `int(BACKUP_RETENTION)` fallaba silenciosamente con valores no numéricos

### Mejorado
- 21 → 70 tests (+49): cobertura de timeout, retry Telegram, stats, validación config, table output

## [1.0.0] — 2026-04-14

### Añadido
- Backup PostgreSQL con `pg_dump` comprimido en gzip
- Rotación automática por política de retención
- Notificación Telegram en éxito y fallo
- Comandos CLI: `backup`, `list`, `rotate`
- Dockerfile con volumen `/backups`
- 21 tests con pytest
