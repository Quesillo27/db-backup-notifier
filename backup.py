#!/usr/bin/env python3
"""DB Backup Notifier — Hace backup de PostgreSQL y notifica via Telegram."""

import gzip
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config import Config
from notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def run_backup(config: Config, notifier: TelegramNotifier) -> bool:
    """Ejecuta el backup de la base de datos. Retorna True si exitoso."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_name = config.db_name
    backup_filename = f"{db_name}_{timestamp}.sql.gz"
    backup_path = Path(config.backup_dir) / backup_filename

    # Crear directorio de backups si no existe
    Path(config.backup_dir).mkdir(parents=True, exist_ok=True)

    logger.info(f"Iniciando backup: {db_name} → {backup_path}")

    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = config.db_password

        cmd = [
            'pg_dump',
            '-h', config.db_host,
            '-p', str(config.db_port),
            '-U', config.db_user,
            '-d', db_name,
            '--no-password',
            '-Fp',
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='replace')
            raise RuntimeError(f"pg_dump falló (exit {result.returncode}): {error_msg}")

        with gzip.open(backup_path, 'wb') as gz_file:
            gz_file.write(result.stdout)

        size_mb = backup_path.stat().st_size / (1024 * 1024)
        logger.info(f"Backup completado: {backup_filename} ({size_mb:.2f} MB)")

        rotated = rotate_backups(config)

        if config.notify_on_success:
            msg = (
                f"✅ *Backup exitoso*\n"
                f"• DB: `{db_name}`\n"
                f"• Archivo: `{backup_filename}`\n"
                f"• Tamaño: {size_mb:.2f} MB\n"
                f"• Backups eliminados (rotación): {rotated}"
            )
            notifier.send(msg)

        return True

    except Exception as e:
        error_str = str(e)
        logger.error(f"Backup FALLIDO: {error_str}")

        if backup_path.exists():
            backup_path.unlink()

        msg = (
            f"❌ *Backup FALLIDO*\n"
            f"• DB: `{db_name}`\n"
            f"• Error: `{error_str[:200]}`\n"
            f"• Servidor: `{config.db_host}`"
        )
        notifier.send(msg)

        return False


def rotate_backups(config: Config) -> int:
    """Elimina backups viejos, conservando los últimos N. Retorna cuántos eliminó."""
    backup_dir = Path(config.backup_dir)
    db_name = config.db_name
    keep = config.backup_retention

    pattern = f"{db_name}_*.sql.gz"
    backups = sorted(backup_dir.glob(pattern))

    to_remove = backups[:-keep] if len(backups) > keep else []

    for old_backup in to_remove:
        logger.info(f"Rotando: {old_backup.name}")
        old_backup.unlink()

    return len(to_remove)


def list_backups(config: Config) -> list:
    """Retorna lista de backups existentes con metadata."""
    backup_dir = Path(config.backup_dir)
    db_name = config.db_name
    pattern = f"{db_name}_*.sql.gz"

    backups = []
    for f in sorted(backup_dir.glob(pattern), reverse=True):
        size_mb = f.stat().st_size / (1024 * 1024)
        backups.append({
            'name': f.name,
            'path': str(f),
            'size_mb': round(size_mb, 2),
            'mtime': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    return backups


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='PostgreSQL Backup Notifier')
    parser.add_argument('action', nargs='?', default='backup',
                        choices=['backup', 'list', 'rotate'],
                        help='Acción a realizar (default: backup)')
    args = parser.parse_args()

    config = Config()
    errors = config.validate()
    if errors:
        for err in errors:
            logger.error(f"Config: {err}")
        sys.exit(1)

    notifier = TelegramNotifier(config)

    if args.action == 'backup':
        success = run_backup(config, notifier)
        sys.exit(0 if success else 1)
    elif args.action == 'list':
        backups = list_backups(config)
        print(json.dumps(backups, indent=2))
    elif args.action == 'rotate':
        removed = rotate_backups(config)
        print(f"Rotados {removed} backups viejos")
