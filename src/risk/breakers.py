"""Circuit breakers automatiques (règle R9).

- N pertes consécutives -> PAUSE temporaire ;
- perte horaire ou journalière > seuil -> HALT ;
- drawdown max depuis le plus haut -> HALT ;
- taux d'erreurs API anormal -> HALT ;
- divergence de réconciliation (position locale ≠ exchange) -> HALT + alerte.

Le kill switch manuel (scripts/kill.py) est indépendant de ces breakers.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from enum import Enum

from src.utils.config import RiskConfig
from src.utils.logging_setup import get_logger

logger = get_logger("risk.breakers")


class Action(Enum):
    CONTINUE = "continue"
    PAUSE = "pause"
    HALT = "halt"


@dataclass
class BreakerStatus:
    action: Action
    reason: str = ""


class CircuitBreakers:
    """État des circuit breakers, alimenté par l'exécuteur à chaque cycle."""

    def __init__(self, config: RiskConfig, clock=time.time) -> None:
        self.config = config
        self.clock = clock
        self.consecutive_losses = 0
        self.paused_until: float = 0.0
        self.peak_equity: float = 0.0
        self.day_start_equity: float | None = None
        self.day_start_ts: float = 0.0
        self.hour_start_equity: float | None = None
        self.hour_start_ts: float = 0.0
        self.api_errors: deque[float] = deque()

    # ------------------------------------------------------------ événements
    def record_trade_result(self, pnl: float) -> None:
        cb = self.config.circuit_breakers
        if pnl < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= cb.max_consecutive_losses:
                self.paused_until = self.clock() + cb.pause_after_losses_minutes * 60
                logger.error(
                    "CIRCUIT BREAKER : %d pertes consécutives -> pause jusqu'à +%d min",
                    self.consecutive_losses,
                    cb.pause_after_losses_minutes,
                )
        else:
            self.consecutive_losses = 0

    def record_api_error(self) -> None:
        self.api_errors.append(self.clock())

    def record_reconciliation_divergence(self, local: float, remote: float) -> BreakerStatus:
        tol = self.config.circuit_breakers.reconciliation_tolerance_pct
        ref = max(abs(local), abs(remote), 1e-9)
        if abs(local - remote) / ref > tol:
            msg = f"réconciliation : local={local:.6f} ≠ exchange={remote:.6f} (tol {tol:.2%})"
            logger.critical("CIRCUIT BREAKER HALT : %s", msg)
            return BreakerStatus(Action.HALT, msg)
        return BreakerStatus(Action.CONTINUE)

    # ------------------------------------------------------------ évaluation
    def check(self, equity: float) -> BreakerStatus:
        """À appeler à chaque cycle AVANT toute décision de trading."""
        cb = self.config.circuit_breakers
        limits = self.config.limits
        now = self.clock()

        if now < self.paused_until:
            return BreakerStatus(Action.PAUSE, "pause après pertes consécutives")

        # Fenêtres journalière / horaire (réinitialisées au fil de l'eau).
        if self.day_start_equity is None or now - self.day_start_ts >= 86_400:
            self.day_start_equity, self.day_start_ts = equity, now
        if self.hour_start_equity is None or now - self.hour_start_ts >= 3_600:
            self.hour_start_equity, self.hour_start_ts = equity, now

        self.peak_equity = max(self.peak_equity, equity)

        daily_loss = 1 - equity / self.day_start_equity if self.day_start_equity else 0.0
        if daily_loss > limits.max_daily_loss_pct:
            msg = f"perte journalière {daily_loss:.2%} > {limits.max_daily_loss_pct:.2%}"
            logger.critical("CIRCUIT BREAKER HALT : %s", msg)
            return BreakerStatus(Action.HALT, msg)

        hourly_loss = 1 - equity / self.hour_start_equity if self.hour_start_equity else 0.0
        if hourly_loss > cb.max_hourly_loss_pct:
            msg = f"perte horaire {hourly_loss:.2%} > {cb.max_hourly_loss_pct:.2%}"
            logger.critical("CIRCUIT BREAKER HALT : %s", msg)
            return BreakerStatus(Action.HALT, msg)

        drawdown = 1 - equity / self.peak_equity if self.peak_equity else 0.0
        if drawdown > limits.max_drawdown_pct:
            msg = f"drawdown {drawdown:.2%} > {limits.max_drawdown_pct:.2%}"
            logger.critical("CIRCUIT BREAKER HALT : %s", msg)
            return BreakerStatus(Action.HALT, msg)

        while self.api_errors and now - self.api_errors[0] > 3_600:
            self.api_errors.popleft()
        if len(self.api_errors) > cb.max_api_errors_per_hour:
            msg = f"{len(self.api_errors)} erreurs API/h > {cb.max_api_errors_per_hour}"
            logger.critical("CIRCUIT BREAKER HALT : %s", msg)
            return BreakerStatus(Action.HALT, msg)

        return BreakerStatus(Action.CONTINUE)
