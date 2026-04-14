"""Tests para el módulo de backup."""
import gzip
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from backup import rotate_backups, list_backups, run_backup


class MockConfig:
    db_host = 'localhost'
    db_port = 5432
    db_user = 'postgres'
    db_password = 'secret'
    db_name = 'testdb'
    backup_retention = 3
    notify_on_success = True

    def __init__(self, backup_dir):
        self.backup_dir = backup_dir


def create_fake_backup(directory, db_name, timestamp):
    """Crea un archivo de backup falso .sql.gz."""
    path = Path(directory) / f"{db_name}_{timestamp}.sql.gz"
    with gzip.open(path, 'wb') as f:
        f.write(b"-- fake sql dump")
    return path


@pytest.fixture
def config(tmp_path):
    return MockConfig(backup_dir=str(tmp_path))


def test_rotate_backups_removes_old(config):
    for i in range(1, 6):
        create_fake_backup(config.backup_dir, config.db_name, f"20260101_0000{i:02d}")

    removed = rotate_backups(config)
    assert removed == 2

    remaining = list(Path(config.backup_dir).glob("*.sql.gz"))
    assert len(remaining) == 3


def test_rotate_backups_keeps_all_below_retention(config):
    for i in range(1, 3):
        create_fake_backup(config.backup_dir, config.db_name, f"20260101_0000{i:02d}")

    removed = rotate_backups(config)
    assert removed == 0
    assert len(list(Path(config.backup_dir).glob("*.sql.gz"))) == 2


def test_rotate_backups_empty_dir(config):
    removed = rotate_backups(config)
    assert removed == 0


def test_rotate_keeps_exact_retention(config):
    for i in range(1, 4):
        create_fake_backup(config.backup_dir, config.db_name, f"20260101_0000{i:02d}")

    removed = rotate_backups(config)
    assert removed == 0
    assert len(list(Path(config.backup_dir).glob("*.sql.gz"))) == 3


def test_list_backups_returns_metadata(config):
    create_fake_backup(config.backup_dir, config.db_name, '20260101_120000')
    create_fake_backup(config.backup_dir, config.db_name, '20260101_130000')

    backups = list_backups(config)
    assert len(backups) == 2
    assert '130000' in backups[0]['name']
    assert 'size_mb' in backups[0]
    assert 'mtime' in backups[0]
    assert 'path' in backups[0]


def test_list_backups_empty_dir(config):
    backups = list_backups(config)
    assert backups == []


@patch('backup.subprocess.run')
def test_run_backup_success(mock_run, config):
    notifier = MagicMock()
    mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL dump", stderr=b"")

    result = run_backup(config, notifier)

    assert result is True
    backups = list(Path(config.backup_dir).glob("*.sql.gz"))
    assert len(backups) == 1


@patch('backup.subprocess.run')
def test_run_backup_notifies_on_success(mock_run, config):
    notifier = MagicMock()
    mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL dump", stderr=b"")

    run_backup(config, notifier)
    notifier.send.assert_called_once()
    msg = notifier.send.call_args[0][0]
    assert '✅' in msg


@patch('backup.subprocess.run')
def test_run_backup_failure_notifies(mock_run, config):
    notifier = MagicMock()
    mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"connection refused")

    result = run_backup(config, notifier)

    assert result is False
    notifier.send.assert_called_once()
    msg = notifier.send.call_args[0][0]
    assert '❌' in msg


@patch('backup.subprocess.run')
def test_run_backup_failure_no_partial_file(mock_run, config):
    notifier = MagicMock()
    mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"error")

    run_backup(config, notifier)

    backups = list(Path(config.backup_dir).glob("*.sql.gz"))
    assert len(backups) == 0


@patch('backup.subprocess.run')
def test_run_backup_no_notify_on_failure_config(mock_run, config):
    config.notify_on_success = False
    notifier = MagicMock()
    mock_run.return_value = MagicMock(returncode=0, stdout=b"-- SQL", stderr=b"")

    run_backup(config, notifier)

    notifier.send.assert_not_called()
