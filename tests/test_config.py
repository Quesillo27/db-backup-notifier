"""Tests para el módulo de configuración."""
import os
import pytest
from unittest.mock import patch

from config import Config


def test_default_values():
    with patch.dict(os.environ, {}, clear=False):
        config = Config()
        assert config.db_host == 'localhost'
        assert config.db_port == 5432
        assert config.db_user == 'postgres'
        assert config.backup_retention == 7
        assert config.notify_on_success is True


def test_env_override():
    env = {
        'DB_HOST': 'myhost',
        'DB_PORT': '5433',
        'DB_USER': 'myuser',
        'DB_PASSWORD': 'secret',
        'DB_NAME': 'mydb',
        'BACKUP_DIR': '/tmp/backups',
        'BACKUP_RETENTION': '14',
        'NOTIFY_ON_SUCCESS': 'false',
    }
    with patch.dict(os.environ, env):
        config = Config()
        assert config.db_host == 'myhost'
        assert config.db_port == 5433
        assert config.db_user == 'myuser'
        assert config.db_password == 'secret'
        assert config.db_name == 'mydb'
        assert config.backup_dir == '/tmp/backups'
        assert config.backup_retention == 14
        assert config.notify_on_success is False


def test_notify_on_success_true_variants():
    for val in ['true', 'True', 'TRUE']:
        with patch.dict(os.environ, {'NOTIFY_ON_SUCCESS': val}):
            config = Config()
            assert config.notify_on_success is True


def test_validate_empty_db_name():
    with patch.dict(os.environ, {'DB_NAME': '', 'DB_USER': 'user'}):
        config = Config()
        errors = config.validate()
        assert any('DB_NAME' in e for e in errors)


def test_validate_ok():
    with patch.dict(os.environ, {'DB_NAME': 'mydb', 'DB_USER': 'user'}):
        config = Config()
        errors = config.validate()
        assert errors == []
