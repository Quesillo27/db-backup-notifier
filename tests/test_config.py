"""Tests para el módulo de configuración."""
import os
import pytest
from unittest.mock import patch

from config import Config


class TestConfigDefaults:
    def test_default_db_host(self):
        with patch.dict(os.environ, {}, clear=False):
            assert Config().db_host == 'localhost'

    def test_default_db_port(self):
        assert Config().db_port == 5432

    def test_default_db_user(self):
        assert Config().db_user == 'postgres'

    def test_default_backup_retention(self):
        assert Config().backup_retention == 7

    def test_default_notify_on_success(self):
        assert Config().notify_on_success is True

    def test_default_pg_dump_timeout(self):
        assert Config().pg_dump_timeout == 300


class TestConfigEnvOverride:
    def test_all_vars_overridden(self):
        env = {
            'DB_HOST': 'myhost',
            'DB_PORT': '5433',
            'DB_USER': 'myuser',
            'DB_PASSWORD': 'secret',
            'DB_NAME': 'mydb',
            'BACKUP_DIR': '/tmp/backups',
            'BACKUP_RETENTION': '14',
            'NOTIFY_ON_SUCCESS': 'false',
            'PG_DUMP_TIMEOUT': '600',
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
            assert config.pg_dump_timeout == 600

    def test_notify_on_success_case_insensitive(self):
        for val in ['true', 'True', 'TRUE']:
            with patch.dict(os.environ, {'NOTIFY_ON_SUCCESS': val}):
                assert Config().notify_on_success is True
        for val in ['false', 'False', 'FALSE']:
            with patch.dict(os.environ, {'NOTIFY_ON_SUCCESS': val}):
                assert Config().notify_on_success is False

    def test_invalid_db_port_falls_back_to_default(self):
        with patch.dict(os.environ, {'DB_PORT': 'not_a_number'}):
            assert Config().db_port == 5432

    def test_invalid_backup_retention_falls_back_to_default(self):
        with patch.dict(os.environ, {'BACKUP_RETENTION': 'abc'}):
            assert Config().backup_retention == 7

    def test_backup_retention_zero_coerced_to_one(self):
        with patch.dict(os.environ, {'BACKUP_RETENTION': '0'}):
            assert Config().backup_retention == 1

    def test_invalid_pg_dump_timeout_falls_back_to_default(self):
        with patch.dict(os.environ, {'PG_DUMP_TIMEOUT': 'bad'}):
            assert Config().pg_dump_timeout == 300


class TestConfigValidation:
    def test_validate_empty_db_name_returns_error(self):
        with patch.dict(os.environ, {'DB_NAME': '', 'DB_USER': 'user'}):
            errors = Config().validate()
            assert any('DB_NAME' in e for e in errors)

    def test_validate_empty_db_user_returns_error(self):
        with patch.dict(os.environ, {'DB_NAME': 'mydb', 'DB_USER': ''}):
            errors = Config().validate()
            assert any('DB_USER' in e for e in errors)

    def test_validate_ok_with_required_fields(self):
        with patch.dict(os.environ, {'DB_NAME': 'mydb', 'DB_USER': 'user'}):
            errors = Config().validate()
            assert errors == []

    def test_validate_invalid_port_range(self):
        with patch.dict(os.environ, {'DB_NAME': 'mydb', 'DB_USER': 'user', 'DB_PORT': '99999'}):
            config = Config()
            config.db_port = 99999
            errors = config.validate()
            assert any('DB_PORT' in e for e in errors)

    def test_validate_multiple_errors_returned(self):
        with patch.dict(os.environ, {'DB_NAME': '', 'DB_USER': ''}):
            errors = Config().validate()
            assert len(errors) >= 2

    def test_validate_short_timeout_returns_error(self):
        with patch.dict(os.environ, {'DB_NAME': 'mydb', 'DB_USER': 'user', 'PG_DUMP_TIMEOUT': '5'}):
            config = Config()
            errors = config.validate()
            assert any('PG_DUMP_TIMEOUT' in e for e in errors)
