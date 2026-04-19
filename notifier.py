"""Módulo de notificaciones via Telegram con reintentos."""
import time

import requests

from logger import get_logger

logger = get_logger('notifier')

_MAX_RETRIES = 2
_RETRY_DELAY = 3  # segundos


class TelegramNotifier:
    def __init__(self, config):
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id

    def send(self, message: str, retries: int = _MAX_RETRIES) -> bool:
        """Envía mensaje a Telegram. Retorna True si exitoso. Reintenta hasta `retries` veces."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram no configurado — omitiendo notificación")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        for attempt in range(retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=10)
                resp.raise_for_status()
                logger.info("Notificación Telegram enviada")
                return True
            except Exception as e:
                if attempt < retries:
                    logger.warning(f"Intento {attempt + 1} fallido, reintentando en {_RETRY_DELAY}s: {e}")
                    time.sleep(_RETRY_DELAY)
                else:
                    logger.error(f"Error enviando notificación Telegram tras {retries + 1} intentos: {e}")

        return False
