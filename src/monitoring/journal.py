"""Exports du journal (SQLite -> CSV) : trades ET décisions complètes (R10)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.execution.state import StateStore


def export_decisions_csv(store: StateStore, out_path: str | Path) -> int:
    """Exporte TOUTES les décisions (trades, non-trades, refus, breakers) en CSV."""
    rows = store.decisions()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ts", "kind", "symbol", "payload"])
        writer.writerows(rows)
    return len(rows)


def export_trades_csv(store: StateStore, out_path: str | Path) -> int:
    """Exporte les ordres exécutés (kind=order) en CSV structuré."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ts", "symbol", "side", "qty", "price", "fee", "client_order_id"])
        for ts, kind, symbol, payload in store.decisions():
            if kind != "order":
                continue
            p = json.loads(payload)
            writer.writerow(
                [
                    ts,
                    symbol,
                    p.get("side"),
                    p.get("qty"),
                    p.get("price"),
                    p.get("fee"),
                    p.get("coid"),
                ]
            )
            n += 1
    return n
