"""Tests para el módulo de backup."""
import gzip
import subprocess
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from backup import rotate_backups, list_backups, run_backup, _notify_failure, _print_list_table


class MockConfig:
    db_host = 'localhost'
    db_port = 5432
    db_user = 'postgres'
    db_password = 'secret'
    db_name = 'testdb'
    backup_retention = 3
    notify_on_success = True
    pg_dump_timeout = 300

    def __init__(self, backup_dir):
        self.backup_dir = backup_dir


def create_fake_backup(directory, db_name, timestamp):
    path = Path(directory) / f"{db_name}_{timestamp}.sql.gz"
    with gzip.open(path, 'wb') as f:
        f.write(b"-- fake sql dump")
    return path


@pytest.fixture
def config(tmp_path):
    return MockConfig(backup_dir=str(tmp_path))


# ── rotate_backups ──────────────────────────────────────────────────────────

class TestRotateBackups:
    def test_removes_oldest_when_over_retention(self, config):
        for i in range(1, 6):
            create_fake_backup(config.backup_dir, config.db_name, f"20260101_0000{i:02d}")
        removed = rotate_backups(config)
        assert removed == 2
        remaining = list(Path(config.backup_dir).glob("*.sql.gz"))
        assert len(remaining) == 3

    def test_keeps_all_below_retention(self, config):
        for i in range(1, 3):
            create_fake_backup(config.backup_dir, config.db_name, f"20260101_0000{i:02d}")
        removed = rotate_backups(config)
        assert removed == 0
        assert len(list(Path(config.backup_dir).glob("*.sql.gz"))) == 2

    def test_empty_dir_returns_zero(self, config):
        assert rotate_backups(config) == 0

    def test_exact_retention_count_removes_none(self, config):
        for i in range(1, 4):
            create_fake_backup(config.backup_dir, config.db_name, f"20260101_0000{i:02d}")
        removed = rotate_backups(config)
        assert removed == 0
        assert len(list(Path(config.backup_dir).glob("*.sql.gz"))) == 3

    def test_preserves_newest_backups(self, config):
        timestamps = ['20260101_000001', '20260101_000002', '20260101_000003',
                      '20260101_000004', '20260101_000005']
        for ts in timestamps:
            create_fake_backup(config.backup_dir, config.db_name, ts)
        rotate_backups(config)
        remaining = sorted(Path(config.backup_dir).glob("*.sql.gz"))
        names = [f.name for f in remaining]
        assert any('000003' in n for n in names)
        assert any('000004' in n for n in names)
        assert any('000005' in n for n in names)
        assert not any('000001' in n for n in names)
        assert not any('000002' in n for n in names)

    def test_does_not_delete_other_db_backups(self, config):
        for i in range(1, 6):
            create_fake_backup(config.backup_dir, config.db_name, f"20260101_0000{i:02d}")
        other = Path(config.backup_dir) / "otherdb_20260101_000001.sql.gz"
        with gzip.open(other, 'wb') as f:
            f.write(b"other")
        rotate_backups(config)
        assert other.exists()

    def test_retention_one_keeps_only_last(self, config):
        config.backup_retention = 1
        for i in range(1, 4):
            create_fake_backup(config.backup_dir, config.db_name, f"20260101_0000{i:02d}")
        removed = rotate_backups(config)
        assert removed == 2
        remaining = list(Path(config.backup_dir).glob(f"{config.db_name}_*.sql.gz"))
        assert len(remaining) == 1


# ── list_backups ─────────────────────────────────────────────────────────────

class TestListBackups:
    def test_returns_metadata_fields(self, config):
        create_fake_backup(config.backup_dir, config.db_name, '20260101_120000')
        backups = list_backups(config)
        assert len(backups) == 1
        assert 'name' in backups[0]
        assert 'path' in backups[0]
        assert 'size_mb' in backups[0]
        assert 'mtime' in backups[0]

    def test_returns_newest_first(self, config):
        create_fake_backup(config.backup_dir, config.db_name, '20260101_120000')
        create_fake_backup(config.backup_dir, config.db_name, '20260101_130000')
        backups = list_backups(config)
        assert len(backups) == 2
        assert '130000' in backups[0]['name']

    def test_empty_dir_returns_empty_list(self, config):
        assert list_backups(config) == []

    def test_size_mb_is_positive(self, config):
        create_fake_backup(config.backup_dir, config.db_name, '20260101_120000')
        backups = list_backups(config)
        assert backups[0]['size_mb'] >= 0

    def test_path_field_is_absolute(self, config):
        create_fake_backup(config.backup_dir, config.db_name, '20260101_120000')
        backups = list_backups(config)
        assert backups[0]['path'].startswith('/')


# ── run_backup ────────────────────────────────────────────────────────────────

class TestRunBackup:
    @patch('backup.subprocess.run')
    def test_success_returns_true(self, mock_run, config):
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL dump", stderr=b"")
        assert run_backup(config, notifier) is True
        assert len(list(Path(config.backup_dir).glob("*.sql.gz"))) == 1

    @patch('backup.subprocess.run')
    def test_success_notifies_with_checkmark(self, mock_run, config):
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL dump", stderr=b"")
        run_backup(config, notifier)
        notifier.send.assert_called_once()
        assert '✅' in notifier.send.call_args[0][0]

    @patch('backup.subprocess.run')
    def test_failure_returns_false(self, mock_run, config):
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"connection refused")
        assert run_backup(config, notifier) is False

    @patch('backup.subprocess.run')
    def test_failure_notifies_with_cross(self, mock_run, config):
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"error")
        run_backup(config, notifier)
        notifier.send.assert_called_once()
        assert '❌' in notifier.send.call_args[0][0]

    @patch('backup.subprocess.run')
    def test_failure_removes_partial_file(self, mock_run, config):
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"error")
        run_backup(config, notifier)
        assert list(Path(config.backup_dir).glob("*.sql.gz")) == []

    @patch('backup.subprocess.run')
    def test_notify_on_success_false_skips_notification(self, mock_run, config):
        config.notify_on_success = False
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL", stderr=b"")
        run_backup(config, notifier)
        notifier.send.assert_not_called()

    @patch('backup.subprocess.run')
    def test_creates_backup_dir_if_missing(self, mock_run, tmp_path, config):
        config.backup_dir = str(tmp_path / 'nested' / 'deep')
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL", stderr=b"")
        result = run_backup(config, notifier)
        assert result is True
        assert Path(config.backup_dir).is_dir()

    @patch('backup.subprocess.run')
    def test_backup_file_is_valid_gzip(self, mock_run, config):
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL dump content", stderr=b"")
        run_backup(config, notifier)
        files = list(Path(config.backup_dir).glob("*.sql.gz"))
        assert len(files) == 1
        with gzip.open(files[0], 'rb') as f:
            content = f.read()
        assert content == b"-- SQL dump content"

    @patch('backup.subprocess.run')
    def test_timeout_returns_false(self, mock_run, config):
        notifier = MagicMock()
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='pg_dump', timeout=300)
        assert run_backup(config, notifier) is False
        notifier.send.assert_called_once()
        assert '❌' in notifier.send.call_args[0][0]

    @patch('backup.subprocess.run')
    def test_timeout_removes_partial_file(self, mock_run, config):
        notifier = MagicMock()
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='pg_dump', timeout=300)
        run_backup(config, notifier)
        assert list(Path(config.backup_dir).glob("*.sql.gz")) == []

    @patch('backup.subprocess.run')
    def test_pg_dump_called_with_correct_args(self, mock_run, config):
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL", stderr=b"")
        run_backup(config, notifier)
        cmd = mock_run.call_args[0][0]
        assert 'pg_dump' in cmd
        assert '-h' in cmd
        assert config.db_host in cmd
        assert '-U' in cmd
        assert config.db_user in cmd

    @patch('backup.subprocess.run')
    def test_pg_dump_uses_timeout_from_config(self, mock_run, config):
        config.pg_dump_timeout = 120
        notifier = MagicMock()
        mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL", stderr=b"")
        run_backup(config, notifier)
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['timeout'] == 120


# ── _notify_failure ───────────────────────────────────────────────────────────

class TestNotifyFailure:
    def test_sends_message_with_db_name(self):
        notifier = MagicMock()
        _notify_failure(notifier, 'mydb', 'myhost', 'connection refused')
        msg = notifier.send.call_args[0][0]
        assert 'mydb' in msg
        assert '❌' in msg

    def test_truncates_long_error_message(self):
        notifier = MagicMock()
        long_error = 'x' * 500
        _notify_failure(notifier, 'db', 'host', long_error)
        msg = notifier.send.call_args[0][0]
        assert len(msg) < 700


# ── _print_list_table ─────────────────────────────────────────────────────────

class TestPrintListTable:
    def test_prints_table_header(self, capsys):
        backups = [{'name': 'mydb_20260101_120000.sql.gz', 'size_mb': 1.5,
                    'mtime': '2026-01-01T12:00:00'}]
        _print_list_table(backups)
        out = capsys.readouterr().out
        assert 'Nombre' in out
        assert 'mydb_20260101_120000.sql.gz' in out

    def test_prints_empty_message_when_no_backups(self, capsys):
        _print_list_table([])
        out = capsys.readouterr().out
        assert 'No hay backups' in out
