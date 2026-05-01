import logging
import threading
import time
from typing import Any, Optional

import requests

from services.notifier import Notifier


class TelegramListener:
    def __init__(self, bot_token: str, chat_id: str, stop_event: threading.Event, pause_event: threading.Event, dashboard: Optional[Any] = None, notifier: Optional[Notifier] = None):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._stop_event = stop_event
        self._pause_event = pause_event
        self._dashboard = dashboard
        self._notifier = notifier
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._offset: Optional[int] = None

    def _send_message(self, text: str) -> None:
        try:
            url = f"{self._base_url}/sendMessage"
            payload = {"chat_id": self._chat_id, "text": text}
            requests.post(url, json=payload)
        except Exception as e:
            logging.warning(f"Failed to send Telegram message: {e}")

    def _handle_command(self, command: str) -> None:
        if command == "/stop":
            self._stop_event.set()
            self._send_message("Bot stopping after current tick.")
        elif command == "/pause":
            self._pause_event.set()
            self._send_message("Bot paused.")
        elif command == "/resume":
            self._pause_event.clear()
            self._send_message("Bot resumed.")
        elif command == "/status":
            if self._pause_event.is_set():
                self._send_message("Bot is paused.")
            else:
                self._send_message("Bot is running.")
        elif command == "/summary":
            if self._notifier is not None and self._dashboard is not None:
                self._notifier.notify_summary(self._dashboard.get_summary())
            else:
                self._send_message("Summary not available.")

    def _drain_updates(self) -> None:
        try:
            url = f"{self._base_url}/getUpdates"
            params = {"offset": -1, "timeout": 0}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("ok") and data.get("result"):
                updates = data["result"]
                if updates:
                    last_update_id = updates[-1].get("update_id")
                    if last_update_id is not None:
                        self._offset = last_update_id + 1
                        logging.info(f"Drained updates, offset set to {self._offset}")
        except Exception as e:
            logging.warning(f"Failed to drain updates: {e}")

    def start(self) -> None:
        self._drain_updates()
        while not self._stop_event.is_set():
            try:
                url = f"{self._base_url}/getUpdates"
                params = {"timeout": 30}
                if self._offset is not None:
                    params["offset"] = self._offset

                response = requests.get(url, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()

                if not data.get("ok"):
                    logging.warning(f"Telegram API error: {data}")
                    time.sleep(5)
                    continue

                updates = data.get("result", [])
                for update in updates:
                    update_id = update.get("update_id")
                    if update_id is not None:
                        self._offset = update_id + 1

                    message = update.get("message", {})
                    message_chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "").strip()

                    logging.info(f"Listener received update: {update}")


                    if str(message_chat_id) != str(self._chat_id):
                        continue

                    if text.startswith("/"):
                        self._handle_command(text.split()[0].lower())

            except Exception as e:
                logging.exception("Error in Telegram listener polling")
                time.sleep(5)
