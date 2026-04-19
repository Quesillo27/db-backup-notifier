# db-backup-notifier

![CI](https://github.com/Quesillo27/db-backup-notifier/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![PostgreSQL](https://img.shields.io/badge/postgresql-client-336791)
![License](https://img.shields.io/badge/license-MIT-green)

Script Python que hace backups automáticos de PostgreSQL, los comprime con gzip, rota los archivos antiguos según política de retención, y notifica el resultado via Telegram. Diseñado para ejecutarse como cron job en un VPS.

## Instalación en 3 comandos

```bash
git clone https://github.com/Quesillo27/db-backup-notifier
cd db-backup-notifier
bash setup.sh          # instala deps y copia .env.example → .env
```

## Uso

```bash
# Ejecutar backup completo (pg_dump + gzip + rotación + Telegram)
python3 backup.py backup

# Listar backups (tabla o JSON)
python3 backup.py list --output table
python3 backup.py list --output json

# Ver estadísticas del directorio
python3 backup.py stats --output table

# Solo rotar sin hacer nuevo backup
python3 backup.py rotate

# Con logs detallados
python3 backup.py backup --verbose
```

## Ejemplos

```bash
# Configurar variables de entorno
export DB_HOST=localhost DB_USER=postgres DB_PASSWORD=secret DB_NAME=mydb
export BACKUP_DIR=/var/backups/pg BACKUP_RETENTION=7
export TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy

# Ejecutar backup
python3 backup.py backup
# 2026-04-19T03:00:00Z [INFO] backup — Iniciando backup: mydb → /var/backups/pg/mydb_20260419_030000.sql.gz
# 2026-04-19T03:00:05Z [INFO] backup — Backup completado: mydb_20260419_030000.sql.gz (12.45 MB)

# Ver estadísticas
python3 backup.py stats --output table
# Backups: 5 / 7
# Tamaño total: 62.25 MB
# Tamaño promedio: 12.45 MB
# Más antiguo: 2026-04-15T03:00:00
# Más reciente: 2026-04-19T03:00:00
```

## Comandos disponibles

| Comando | Descripción |
|---|---|
| `python3 backup.py backup [--verbose]` | Backup completo + rotación + notificación |
| `python3 backup.py list [--output json\|table]` | Lista backups existentes |
| `python3 backup.py stats [--output json\|table]` | Estadísticas del directorio |
| `python3 backup.py rotate [--output json\|table]` | Elimina backups fuera de retención |
| `make backup` | Alias de backup |
| `make test` | Corre los tests con pytest |
| `make docker` | Build Docker multi-stage |
| `make stats` | Stats en formato tabla |

## Cron job recomendado

```cron
# Backup diario a las 03:00 UTC
0 3 * * * cd /opt/db-backup-notifier && python3 backup.py backup >> /var/log/db-backup.log 2>&1
```

## Variables de entorno

| Variable | Default | Obligatoria | Descripción |
|---|---|---|---|
| `DB_HOST` | `localhost` | No | Host del servidor PostgreSQL |
| `DB_PORT` | `5432` | No | Puerto PostgreSQL |
| `DB_USER` | `postgres` | **Sí** | Usuario de la base de datos |
| `DB_PASSWORD` | `` | No | Contraseña (PGPASSWORD) |
| `DB_NAME` | `mydb` | **Sí** | Nombre de la base de datos |
| `BACKUP_DIR` | `/backups` | No | Directorio donde se guardan backups |
| `BACKUP_RETENTION` | `7` | No | Número de backups a conservar (mín. 1) |
| `PG_DUMP_TIMEOUT` | `300` | No | Timeout para pg_dump en segundos |
| `TELEGRAM_BOT_TOKEN` | `` | No | Token del bot Telegram |
| `TELEGRAM_CHAT_ID` | `` | No | Chat ID de Telegram |
| `NOTIFY_ON_SUCCESS` | `true` | No | Notificar en backups exitosos |
| `LOG_LEVEL` | `INFO` | No | Nivel de log: DEBUG, INFO, WARNING, ERROR |

## Docker

```bash
docker build -t db-backup-notifier .

docker run --rm \
  -e DB_HOST=myhost \
  -e DB_USER=myuser \
  -e DB_PASSWORD=mypass \
  -e DB_NAME=mydb \
  -e TELEGRAM_BOT_TOKEN=xxx \
  -e TELEGRAM_CHAT_ID=yyy \
  -v /var/backups/pg:/backups \
  db-backup-notifier
```

## Roadmap

- Soporte para múltiples bases de datos en un solo run (`DB_NAMES=db1,db2`)
- Subida a S3/GCS como destino adicional
- Comando `restore` para restauración guiada
- Verificación de integridad del backup tras la creación

## Contribuir

PRs bienvenidos. Corre `make test` antes de enviar.
