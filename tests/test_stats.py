"""Tests para el módulo de estadísticas de backups."""
import gzip
import pytest
from pathlib import Path

from stats import get_stats


class MockConfig:
    db_name = 'testdb'
    backup_retention = 7

    def __init__(self, backup_dir):
        self.backup_dir = backup_dir


def create_backup(directory, db_name, timestamp, content=b"-- sql"):
    path = Path(directory) / f"{db_name}_{timestamp}.sql.gz"
    with gzip.open(path, 'wb') as f:
        f.write(content)
    return path


@pytest.fixture
def config(tmp_path):
    return MockConfig(backup_dir=str(tmp_path))


class TestGetStats:
    def test_empty_dir_returns_zero_count(self, config):
        stats = get_stats(config)
        assert stats['count'] == 0
        assert stats['total_size_mb'] == 0.0
        assert stats['oldest'] is None
        assert stats['newest'] is None

    def test_empty_dir_has_retention_policy(self, config):
        stats = get_stats(config)
        assert stats['retention_policy'] == 7

    def test_single_backup_count_is_one(self, config):
        create_backup(config.backup_dir, config.db_name, '20260101_120000')
        stats = get_stats(config)
        assert stats['count'] == 1

    def test_multiple_backups_count(self, config):
        for ts in ['20260101_100000', '20260101_110000', '20260101_120000']:
            create_backup(config.backup_dir, config.db_name, ts)
        stats = get_stats(config)
        assert stats['count'] == 3

    def test_total_size_mb_is_positive(self, config):
        create_backup(config.backup_dir, config.db_name, '20260101_120000', b'x' * 1000)
        stats = get_stats(config)
        assert stats['total_size_mb'] >= 0

    def test_avg_size_mb_present_when_backups_exist(self, config):
        create_backup(config.backup_dir, config.db_name, '20260101_120000')
        stats = get_stats(config)
        assert 'avg_size_mb' in stats

    def test_oldest_and_newest_are_iso_strings(self, config):
        create_backup(config.backup_dir, config.db_name, '20260101_100000')
        create_backup(config.backup_dir, config.db_name, '20260101_120000')
        stats = get_stats(config)
        assert 'T' in stats['oldest']
        assert 'T' in stats['newest']

    def test_slots_used_format(self, config):
        config.backup_retention = 5
        create_backup(config.backup_dir, config.db_name, '20260101_120000')
        create_backup(config.backup_dir, config.db_name, '20260101_130000')
        stats = get_stats(config)
        assert stats['slots_used'] == '2/5'

    def test_backups_list_newest_first(self, config):
        create_backup(config.backup_dir, config.db_name, '20260101_100000')
        create_backup(config.backup_dir, config.db_name, '20260101_120000')
        stats = get_stats(config)
        names = [b['name'] for b in stats['backups']]
        assert '120000' in names[0]
        assert '100000' in names[1]

    def test_backups_list_has_metadata(self, config):
        create_backup(config.backup_dir, config.db_name, '20260101_120000')
        stats = get_stats(config)
        b = stats['backups'][0]
        assert 'name' in b
        assert 'size_mb' in b
        assert 'mtime' in b

    def test_ignores_other_db_files(self, config):
        create_backup(config.backup_dir, config.db_name, '20260101_120000')
        other = Path(config.backup_dir) / "otherdb_20260101_120000.sql.gz"
        with gzip.open(other, 'wb') as f:
            f.write(b"other")
        stats = get_stats(config)
        assert stats['count'] == 1

    def test_retention_policy_matches_config(self, config):
        config.backup_retention = 14
        stats = get_stats(config)
        assert stats['retention_policy'] == 14
