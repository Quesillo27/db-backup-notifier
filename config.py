"""Configuración desde variables de entorno."""
import os


class Config:
    def __init__(self):
        # Base de datos
        self.db_host = os.environ.get('DB_HOST', 'localhost')
        self.db_port = int(os.environ.get('DB_PORT', '5432'))
        self.db_user = os.environ.get('DB_USER', 'postgres')
        self.db_password = os.environ.get('DB_PASSWORD', '')
        self.db_name = os.environ.get('DB_NAME', 'mydb')

        # Backup
        self.backup_dir = os.environ.get('BACKUP_DIR', '/backups')
        self.backup_retention = int(os.environ.get('BACKUP_RETENTION', '7'))

        # Telegram
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        self.notify_on_success = os.environ.get('NOTIFY_ON_SUCCESS', 'true').lower() == 'true'

    def validate(self):
        """Valida que las variables requeridas estén presentes."""
        errors = []
        if not self.db_name:
            errors.append('DB_NAME es requerido')
        if not self.db_user:
            errors.append('DB_USER es requerido')
        return errors
