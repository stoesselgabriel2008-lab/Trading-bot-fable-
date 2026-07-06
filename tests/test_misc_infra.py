"""Tests d'infrastructure : scheduler, alertes, logging, stockage incrémental, broker live-lock."""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from src.data.fetcher import timeframe_ms
from src.data.storage import dataset_path, load, update_incremental
from src.execution.broker import CcxtBroker
from src.execution.scheduler import run_fast_cycles, run_scheduled
from src.monitoring import alerts
from src.utils.logging_setup import get_logger, setup_logging


# ------------------------------------------------------------------ scheduler
def test_fast_cycles_runs_n_times() -> None:
    calls = []
    run_fast_cycles(lambda: calls.append(1), 5)
    assert len(calls) == 5


def test_scheduler_rejects_unknown_timeframe() -> None:
    with pytest.raises(ValueError):
        run_scheduled(lambda: None, "3m")


# ------------------------------------------------------------------ verrou live (R6)
def test_ccxt_broker_live_locked() -> None:
    with pytest.raises(PermissionError):
        CcxtBroker("bybit", mode="live", live_trading=False)
    # Même avec live_trading=true : le live exige une confirmation humaine hors bot.
    with pytest.raises(PermissionError):
        CcxtBroker("bybit", mode="live", live_trading=True)


# ------------------------------------------------------------------ alertes
def test_alerts_noop_without_config(monkeypatch) -> None:
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    assert alerts.send_alert("test") is False


def test_alerts_post_to_configured_webhooks(monkeypatch) -> None:
    sent = []
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://example.invalid/hook")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(
        alerts.requests, "post", lambda url, json, timeout: sent.append(url) or None
    )
    assert alerts.send_alert("hello") is True
    assert len(sent) == 2


# ------------------------------------------------------------------ logging
def test_setup_logging_writes_rotating_file(tmp_path) -> None:
    root = logging.getLogger("trading_bot")
    old_handlers, root.handlers = root.handlers, []
    try:
        logger = setup_logging(log_dir=tmp_path)
        get_logger("unit").info("ligne de test")
        assert (tmp_path / "trading_bot.log").exists()
        assert "ligne de test" in (tmp_path / "trading_bot.log").read_text(encoding="utf-8")
        # Idempotent : le second appel ne double pas les handlers.
        assert setup_logging(log_dir=tmp_path) is logger
    finally:
        root.handlers = old_handlers


# ------------------------------------------------------------------ stockage incrémental
class FakeExchange:
    """Exchange minimal : sert des bougies 1h déterministes jusqu'à `now_ms`."""

    def __init__(self, n_bars: int) -> None:
        self.tf = timeframe_ms("1h")
        self.n = n_bars

    def milliseconds(self) -> int:
        return self.n * self.tf

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        first = max(0, since // self.tf)
        rows = []
        for i in range(int(first), min(int(first) + limit, self.n)):
            ts = i * self.tf
            rows.append([ts, 100 + i, 101 + i, 99 + i, 100.5 + i, 10.0])
        return rows


def test_update_incremental_first_and_second_run(tmp_path) -> None:
    ex = FakeExchange(n_bars=50)
    df1 = update_incremental(ex, "src", "AA/BB", "1h", default_since_ms=0, data_dir=tmp_path)
    # Les 50 bougies servies sont closes (la dernière clôture exactement à `now`).
    assert len(df1) == 50
    # De nouvelles bougies arrivent : la mise à jour reprend au bon endroit.
    ex.n = 60
    df2 = update_incremental(ex, "src", "AA/BB", "1h", default_since_ms=0, data_dir=tmp_path)
    assert len(df2) == 60
    assert df2.index.is_monotonic_increasing and not df2.index.duplicated().any()
    stored = load(dataset_path("src", "AA/BB", "1h", tmp_path))
    pd.testing.assert_frame_equal(stored, df2)
