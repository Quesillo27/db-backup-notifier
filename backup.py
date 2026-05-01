#!/usr/bin/env python3
"""DB Backup Notifier — Hace backup de PostgreSQL y notifica via Telegram."""

import gzip
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from config import Config
from logger import get_logger
from notifier import TelegramNotifier
from stats import get_stats

logger = get_logger('backup')
_COPY_CHUNK_SIZE = 1024 * 1024


def _compress_to_gzip(source_path: Path, destination_path: Path) -> None:
    """Comprime un dump SQL temporal a gzip en chunks para evitar picos de memoria."""
    with source_path.open('rb') as source_file, gzip.open(destination_path, 'wb') as gz_file:
        while chunk := source_file.read(_COPY_CHUNK_SIZE):
            gz_file.write(chunk)


def run_backup(config: Config, notifier: TelegramNotifier) -> bool:
    """Ejecuta el backup de la base de datos. Retorna True si exitoso."""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    db_name = config.db_name
    backup_filename = f"{db_name}_{timestamp}.sql.gz"
    backup_path = Path(config.backup_dir) / backup_filename
    raw_backup_path = None

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

        raw_backup_fd, raw_backup_name = tempfile.mkstemp(
            prefix=f"{db_name}_{timestamp}_",
            suffix='.sql',
            dir=config.backup_dir
        )
        os.close(raw_backup_fd)
        raw_backup_path = Path(raw_backup_name)

        with raw_backup_path.open('wb') as raw_backup_file:
            result = subprocess.run(
                cmd,
                stdout=raw_backup_file,
                stderr=subprocess.PIPE,
                env=env,
                timeout=config.pg_dump_timeout
            )

        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='replace')
            raise RuntimeError(f"pg_dump falló (exit {result.returncode}): {error_msg}")

        if raw_backup_path.stat().st_size == 0:
            raise RuntimeError('pg_dump generó un backup vacío')

        _compress_to_gzip(raw_backup_path, backup_path)

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

    except subprocess.TimeoutExpired:
        error_str = f"pg_dump excedió el tiempo límite de {config.pg_dump_timeout}s"
        logger.error(error_str)
        if backup_path.exists():
            backup_path.unlink()
        _notify_failure(notifier, db_name, config.db_host, error_str)
        return False

    except Exception as e:
        error_str = str(e)
        logger.error(f"Backup FALLIDO: {error_str}")
        if backup_path.exists():
            backup_path.unlink()
        _notify_failure(notifier, db_name, config.db_host, error_str)
        return False
    finally:
        if raw_backup_path and raw_backup_path.exists():
            raw_backup_path.unlink()


def _notify_failure(notifier: TelegramNotifier, db_name: str, db_host: str, error: str) -> None:
    msg = (
        f"❌ *Backup FALLIDO*\n"
        f"• DB: `{db_name}`\n"
        f"• Error: `{error[:200]}`\n"
        f"• Servidor: `{db_host}`"
    )
    notifier.send(msg)


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


def list_backups(config: Config, output_format: str = 'json') -> list:
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


def _print_list_table(backups: list) -> None:
    if not backups:
        print("No hay backups disponibles.")
        return
    header = f"{'Nombre':<45} {'Tamaño (MB)':>12} {'Fecha':>25}"
    print(header)
    print('-' * len(header))
    for b in backups:
        print(f"{b['name']:<45} {b['size_mb']:>12.2f} {b['mtime']:>25}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='PostgreSQL Backup Notifier')
    parser.add_argument('action', nargs='?', default='backup',
                        choices=['backup', 'list', 'rotate', 'stats'],
                        help='Acción a realizar (default: backup)')
    parser.add_argument('--output', '-o', choices=['json', 'table'], default='json',
                        help='Formato de salida para list/stats (default: json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Mostrar output detallado')
    args = parser.parse_args()

    if args.verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'

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
        if args.output == 'table':
            _print_list_table(backups)
        else:
            print(json.dumps(backups, indent=2))

    elif args.action == 'rotate':
        removed = rotate_backups(config)
        if args.output == 'json':
            print(json.dumps({'removed': removed}))
        else:
            print(f"Rotados {removed} backups viejos")

    elif args.action == 'stats':
        data = get_stats(config)
        if args.output == 'table':
            print(f"Backups: {data['count']} / {data['retention_policy']}")
            print(f"Tamaño total: {data['total_size_mb']:.2f} MB")
            if data['count']:
                print(f"Tamaño promedio: {data['avg_size_mb']:.2f} MB")
                print(f"Más antiguo: {data['oldest']}")
                print(f"Más reciente: {data['newest']}")
        else:
            print(json.dumps(data, indent=2))
