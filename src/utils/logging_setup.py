"""Logging structuré du projet : console + fichier rotatif.

Toutes les décisions du bot (trades, non-trades, refus du risk manager,
déclenchements de circuit breakers) passent par ces loggers (règle R10).
Aucun secret ne doit jamais être loggé.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def setup_logging(
    log_dir: str | Path = "logs",
    level: int = logging.INFO,
    filename: str = "trading_bot.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 10,
) -> logging.Logger:
    """Configure le logger racine du projet (idempotent).

    Returns:
        Le logger racine ``trading_bot``.
    """
    logger = logging.getLogger("trading_bot")
    if logger.handlers:  # déjà configuré (appels répétés en tests)
        return logger
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / filename, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Logger enfant du logger racine (ex. ``get_logger("execution")``)."""
    return logging.getLogger(f"trading_bot.{name}")
