"""Scheduler : déclenche un cycle à chaque clôture de bougie (+ délai de grâce).

APScheduler (BlockingScheduler) en production ; mode ``fast_cycles`` pour les
tests et démonstrations (N cycles immédiats sans attendre les clôtures).
"""

from __future__ import annotations

from collections.abc import Callable

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.utils.logging_setup import get_logger

logger = get_logger("execution.scheduler")

#: secondes de grâce après la clôture pour laisser l'exchange finaliser la bougie
GRACE_SECONDS = 20

_CRON_BY_TIMEFRAME = {
    "1h": {"minute": 0, "second": GRACE_SECONDS},
    "4h": {"hour": "0,4,8,12,16,20", "minute": 0, "second": GRACE_SECONDS},
    "1d": {"hour": 0, "minute": 0, "second": GRACE_SECONDS},
}


def run_scheduled(cycle_fn: Callable[[], object], timeframe: str) -> None:
    """Boucle bloquante : un cycle par clôture de bougie (UTC)."""
    if timeframe not in _CRON_BY_TIMEFRAME:
        raise ValueError(f"timeframe non supporté par le scheduler : {timeframe}")
    sched = BlockingScheduler(timezone="UTC")
    sched.add_job(
        cycle_fn,
        CronTrigger(timezone="UTC", **_CRON_BY_TIMEFRAME[timeframe]),
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    logger.info("scheduler démarré (timeframe %s, UTC)", timeframe)
    # Un cycle immédiat au démarrage (reprise après crash comprise).
    cycle_fn()
    sched.start()


def run_fast_cycles(cycle_fn: Callable[[], object], n_cycles: int, sleep_s: float = 0.0) -> None:
    """N cycles immédiats — tests d'intégration et démonstrations."""
    import time

    for _ in range(n_cycles):
        cycle_fn()
        if sleep_s:
            time.sleep(sleep_s)
