import logging

import requests

from services.notifier import Notifier
from core.models import Order


class TelegramNotifier(Notifier):
    def __init__(self, bot_token: str, chat_id: str):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def _send(self, message: str) -> None:
        try:
            payload = {"chat_id": self._chat_id, "text": message}
            requests.post(self._base_url, json=payload)
        except Exception as e:
            logging.warning(f"Failed to send Telegram notification: {e}")

    def notify(self, message: str) -> None:
        self._send(message)

    def notify_order(self, order: Order) -> None:
        message = f"Order: {order.side.upper()} {round(order.quantity, 4)} {order.symbol}"
        self._send(message)

    def notify_error(self, error: str) -> None:
        message = f"ERROR: {error}"
        self._send(message)
