"""Alertes webhook optionnelles (Discord / Telegram).

Les secrets viennent de `.env` (jamais en dur, jamais loggés — R7).
Si aucun webhook n'est configuré, les fonctions sont des no-ops silencieux.
"""

from __future__ import annotations

import os

import requests

from src.utils.logging_setup import get_logger

logger = get_logger("monitoring.alerts")
_TIMEOUT = 10


def send_alert(message: str) -> bool:
    """Envoie ``message`` sur tous les canaux configurés. True si ≥1 envoi OK."""
    sent = False
    discord = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if discord:
        try:
            requests.post(discord, json={"content": message[:1900]}, timeout=_TIMEOUT)
            sent = True
        except requests.RequestException as exc:
            logger.warning("alerte Discord KO : %s", exc)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if token and chat_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message[:4000]},
                timeout=_TIMEOUT,
            )
            sent = True
        except requests.RequestException as exc:
            logger.warning("alerte Telegram KO : %s", exc)
    return sent
