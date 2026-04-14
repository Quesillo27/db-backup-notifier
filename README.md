# db-backup-notifier

![Python](https://img.shields.io/badge/python-3.11-blue) ![PostgreSQL](https://img.shields.io/badge/postgresql-client-336791) ![License](https://img.shields.io/badge/license-MIT-green)

Script Python que hace backups automáticos de PostgreSQL, los comprime con gzip, rota los archivos antiguos según política de retención, y notifica el resultado via Telegram. Diseñado para ejecutarse como cron job en VPS.

## Instalación en 3 comandos

```bash
git clone https://github.com/Quesillo27/db-backup-notifier
cd db-backup-notifier
pip install -r requirements.txt
```

## Uso

```bash
# Ejecutar backup completo
python backup.py backup

# Listar backups existentes
python backup.py list

# Solo rotar (eliminar backups viejos)
python backup.py rotate
```

## Ejemplo

```bash
# Configurar variables de entorno
export DB_HOST=localhost DB_USER=postgres DB_PASSWORD=secret DB_NAME=mydb
export BACKUP_DIR=/var/backups/pg BACKUP_RETENTION=7
export TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy

# Ejecutar backup
python backup.py backup
# → 2026-04-14 06:00:00 [INFO] Iniciando backup: mydb → /var/backups/pg/mydb_20260414_060000.sql.gz
# → 2026-04-14 06:00:05 [INFO] Backup completado: mydb_20260414_060000.sql.gz (12.45 MB)

# Listar backups guardados
python backup.py list
# → [{"name": "mydb_20260414_060000.sql.gz", "size_mb": 12.45, ...}]
```

## API / Comandos disponibles

| Comando | Descripción |
|---|---|
| `python backup.py backup` | Ejecuta backup completo + rotación + notificación |
| `python backup.py list` | Lista backups existentes en JSON |
| `python backup.py rotate` | Solo elimina backups fuera de retención |
| `make backup` | Alias de `python backup.py backup` |
| `make list` | Alias de `python backup.py list` |
| `make test` | Corre los tests con pytest |

## Cron job recomendado

```cron
# Backup diario a las 03:00 UTC
0 3 * * * cd /opt/db-backup-notifier && python backup.py backup >> /var/log/db-backup.log 2>&1
```

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `DB_HOST` | `localhost` | Host del servidor PostgreSQL |
| `DB_PORT` | `5432` | Puerto PostgreSQL |
| `DB_USER` | `postgres` | Usuario de la base de datos |
| `DB_PASSWORD` | `` | Contraseña (requerida para autenticación) |
| `DB_NAME` | `mydb` | Nombre de la base de datos a respaldar |
| `BACKUP_DIR` | `/backups` | Directorio donde se guardan los backups |
| `BACKUP_RETENTION` | `7` | Número de backups a conservar |
| `TELEGRAM_BOT_TOKEN` | `` | Token del bot de Telegram (opcional) |
| `TELEGRAM_CHAT_ID` | `` | Chat ID de Telegram (opcional) |
| `NOTIFY_ON_SUCCESS` | `true` | Notificar también cuando el backup es exitoso |

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

## Contribuir

PRs bienvenidos. Corre `make test` antes de enviar.
