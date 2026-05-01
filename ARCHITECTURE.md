# Architecture

## Decisiones de diseño

### Por qué script Python y no un servicio

`db-backup-notifier` está diseñado para ejecutarse como **cron job puntual**, no como servidor permanente. Esto reduce la superficie de ataque (sin puerto abierto), simplifica el deploy (solo `cron + python3`) y garantiza que el proceso termina cuando el backup termina.

### Estructura de módulos

```
backup.py       — Entry point + lógica de backup/rotación/listado
config.py       — Carga de env vars con valores por defecto y validación
notifier.py     — Envío Telegram con reintentos y backoff
logger.py       — Logger estructurado con timestamps UTC configurado desde LOG_LEVEL
stats.py        — Cálculo de estadísticas del directorio de backups
tests/          — Tests unitarios con mocks (sin acceso real a DB/Telegram)
```

### Por qué `pg_dump` en lugar de `pg_basebackup`

`pg_dump` produce un dump SQL portátil (legible, restaurable en cualquier versión compatible), mientras que `pg_basebackup` hace copia binaria del cluster completo. Para bases de datos individuales (el caso de uso principal), `pg_dump` es más apropiado y produce archivos más pequeños.

### Por qué gzip en lugar de zstd/bzip2

`gzip` es universalmente disponible sin dependencias adicionales. La diferencia de compresión vs. zstd no justifica agregar una dependencia del sistema operativo que puede no estar disponible en todos los entornos.

Desde `v1.1.1`, el dump se escribe primero a un archivo temporal local y luego se comprime por chunks. Esto evita retener todo el SQL en memoria, a costa de usar espacio temporal adicional durante la ejecución.

### Por qué SQLite no aplica aquí

Este servicio no persiste estado propio — los backups son el estado. No necesita base de datos propia.

### Por qué reintentos en Telegram y no en pg_dump

Un timeout de pg_dump generalmente indica un problema real (DB no disponible, red caída). Reintentar el dump consumiría tiempo y disco innecesariamente. En cambio, las notificaciones Telegram pueden fallar por rate limits o problemas de red transitorios, por lo que 2 reintentos son apropiados.

### Flujo de ejecución

```
backup.py main
  → Config.validate()       # fail fast si hay configuración inválida
  → run_backup()
      → subprocess.run(pg_dump, stdout=tempfile, timeout=PG_DUMP_TIMEOUT)
      → _compress_to_gzip(tempfile, backup_path)
      → rotate_backups()
      → TelegramNotifier.send()   # con reintentos
```

### Variables de entorno críticas

| Variable | Impacto si falta |
|---|---|
| `DB_NAME` | Error fatal — no se puede ejecutar |
| `DB_USER` | Error fatal — no se puede ejecutar |
| `DB_PASSWORD` | pg_dump puede fallar si la DB requiere auth |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Backups funcionan, sin notificación |

### Roadmap

- Soporte para múltiples bases de datos en un solo run (`DB_NAMES=db1,db2`)
- Subida a S3/GCS como destino adicional (`BACKUP_DEST=s3://bucket/path`)
- Restauración guiada (`python3 backup.py restore --file backup.sql.gz`)
- Verificación de integridad del backup (`pg_restore --list`) tras la creación
