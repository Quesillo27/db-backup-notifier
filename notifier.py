"""Módulo de notificaciones via Telegram."""
import logging
import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, config):
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id

    def send(self, message: str) -> bool:
        """Envía mensaje a Telegram. Retorna True si exitoso."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram no configurado — omitiendo notificación")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            resp = requests.post(url, json={
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }, timeout=10)
            resp.raise_for_status()
            logger.info("Notificación Telegram enviada")
            return True
        except Exception as e:
            logger.error(f"Error enviando notificación Telegram: {e}")
            return False
