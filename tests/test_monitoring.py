"""Tests du monitoring (Phase 8) : snapshot, shortfall, rapports, exports."""

from __future__ import annotations

import pytest

from src.execution.state import StateStore
from src.monitoring.journal import export_decisions_csv, export_trades_csv
from src.monitoring.reporting import (
    build_snapshot,
    realized_expectancy,
    render_daily_report,
    render_dashboard_html,
)


@pytest.fixture
def store(tmp_path) -> StateStore:
    s = StateStore(tmp_path / "bot.sqlite")
    s.log_decision("target", None, {"strategy": "test", "targets": {}, "equity": 10_000})
    # Aller-retour gagnant : achat 1 @100, vente 1 @110, frais 0,1 chacun.
    s.log_decision(
        "order", "BTC/USDT", {"coid": "a1", "side": "buy", "qty": 1.0, "price": 100.0, "fee": 0.1}
    )
    s.log_decision(
        "order", "BTC/USDT", {"coid": "a2", "side": "sell", "qty": 1.0, "price": 110.0, "fee": 0.1}
    )
    # Aller-retour perdant : achat 2 @50, vente 2 @45.
    s.log_decision(
        "order", "ETH/USDT", {"coid": "b1", "side": "buy", "qty": 2.0, "price": 50.0, "fee": 0.1}
    )
    s.log_decision(
        "order", "ETH/USDT", {"coid": "b2", "side": "sell", "qty": 2.0, "price": 45.0, "fee": 0.1}
    )
    s.log_decision("no_trade", None, {"reason": "test"})
    s.log_decision("error", None, {"stage": "fetch", "error": "x"})
    s.record_equity(10_000, 10_000)
    s.record_equity(10_200, 5_000)
    s.record_equity(9_900, 5_000)
    return s


def test_snapshot_counts_and_drawdown(store) -> None:
    snap = build_snapshot(store)
    assert snap.equity == 9_900
    assert snap.n_orders == 4
    assert snap.n_api_errors == 1
    assert snap.current_drawdown == pytest.approx(9_900 / 10_200 - 1)


def test_realized_expectancy_fifo(store) -> None:
    exp, n = realized_expectancy(store)
    assert n == 2
    # PnL 1 : 1*(110-100) - 0.1 = 9.9 ; PnL 2 : 2*(45-50) - 0.1 = -10.1 ; ref 10 000.
    assert exp == pytest.approx((9.9 - 10.1) / 2 / 10_000)


def test_daily_report_flags_divergence() -> None:
    from src.monitoring.reporting import DailySnapshot

    snap = DailySnapshot("2026-01-01", 10_000, 0.0, 0.0, 0, 0, 0, {})
    txt = render_daily_report(snap, (0.001, 50), (0.02, 50), "test")
    assert "DIVERGENCE FORTE" in txt
    txt2 = render_daily_report(snap, (None, 0), (0.02, 50), "test")
    assert "insuffisant" in txt2


def test_dashboard_and_csv_exports(store, tmp_path) -> None:
    html = render_dashboard_html(store, "label-test")
    assert "label-test" in html and "data:image/png;base64," in html
    assert export_decisions_csv(store, tmp_path / "d.csv") == 7
    assert export_trades_csv(store, tmp_path / "t.csv") == 4
    assert (tmp_path / "t.csv").read_text(encoding="utf-8").count("\n") == 5  # entête + 4
