"""Estadísticas de backups almacenados."""
from datetime import datetime
from pathlib import Path


def get_stats(config) -> dict:
    """Retorna estadísticas del directorio de backups."""
    backup_dir = Path(config.backup_dir)
    pattern = f"{config.db_name}_*.sql.gz"

    files = sorted(backup_dir.glob(pattern))
    if not files:
        return {
            'count': 0,
            'total_size_mb': 0.0,
            'oldest': None,
            'newest': None,
            'retention_policy': config.backup_retention,
            'backups': []
        }

    sizes = [f.stat().st_size for f in files]
    mtimes = [f.stat().st_mtime for f in files]

    return {
        'count': len(files),
        'total_size_mb': round(sum(sizes) / (1024 * 1024), 2),
        'avg_size_mb': round(sum(sizes) / len(sizes) / (1024 * 1024), 2),
        'oldest': datetime.fromtimestamp(min(mtimes)).isoformat(),
        'newest': datetime.fromtimestamp(max(mtimes)).isoformat(),
        'retention_policy': config.backup_retention,
        'slots_used': f"{len(files)}/{config.backup_retention}",
        'backups': [
            {
                'name': f.name,
                'size_mb': round(f.stat().st_size / (1024 * 1024), 2),
                'mtime': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in reversed(files)
        ]
    }
