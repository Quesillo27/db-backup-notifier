"""Configuración desde variables de entorno."""
import os


class Config:
    def __init__(self):
        # Base de datos
        self.db_host = os.environ.get('DB_HOST', 'localhost')
        self.db_user = os.environ.get('DB_USER', 'postgres')
        self.db_password = os.environ.get('DB_PASSWORD', '')
        self.db_name = os.environ.get('DB_NAME', 'mydb')

        try:
            self.db_port = int(os.environ.get('DB_PORT', '5432'))
        except ValueError:
            self.db_port = 5432

        # Backup
        self.backup_dir = os.environ.get('BACKUP_DIR', '/backups')

        try:
            self.backup_retention = max(1, int(os.environ.get('BACKUP_RETENTION', '7')))
        except ValueError:
            self.backup_retention = 7

        try:
            self.pg_dump_timeout = int(os.environ.get('PG_DUMP_TIMEOUT', '300'))
        except ValueError:
            self.pg_dump_timeout = 300

        # Telegram
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        self.notify_on_success = os.environ.get('NOTIFY_ON_SUCCESS', 'true').lower() == 'true'

    def validate(self) -> list:
        """Valida que las variables requeridas estén presentes. Retorna lista de errores."""
        errors = []
        if not self.db_name:
            errors.append('DB_NAME es requerido')
        if not self.db_user:
            errors.append('DB_USER es requerido')
        if self.db_port <= 0 or self.db_port > 65535:
            errors.append(f'DB_PORT inválido: {self.db_port} (rango válido: 1–65535)')
        if self.backup_retention < 1:
            errors.append('BACKUP_RETENTION debe ser mayor a 0')
        if self.pg_dump_timeout < 10:
            errors.append('PG_DUMP_TIMEOUT debe ser al menos 10 segundos')
        return errors
