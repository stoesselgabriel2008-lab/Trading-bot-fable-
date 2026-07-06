"""Persistance d'état SQLite + journal des décisions + réconciliation.

Trois vérités doivent concorder à chaque démarrage ET périodiquement :
(1) l'état exchange (ou simulé), (2) l'état mémoire, (3) cette base SQLite.
Toute divergence au-delà de la tolérance -> Safe Mode (arrêt + alerte), jamais
de « réparation » silencieuse. (cf. RESEARCH.md §7)

Le journal enregistre TOUTES les décisions — trades, non-trades, refus du
risk manager, déclenchements de breakers (règle R10).
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS positions (
    symbol TEXT PRIMARY KEY,
    qty REAL NOT NULL,
    avg_price REAL NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
    client_order_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty REAL NOT NULL,
    price REAL,
    status TEXT NOT NULL,           -- pending | filled | rejected | cancelled
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS equity_history (
    ts TEXT PRIMARY KEY,
    equity REAL NOT NULL,
    cash REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,             -- target | order | no_trade | risk_clamp | breaker | error | kill
    symbol TEXT,
    payload TEXT NOT NULL           -- JSON
);
CREATE TABLE IF NOT EXISTS kv (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def new_client_order_id() -> str:
    """clientOrderId unique — la clé de l'idempotence des ordres (RESEARCH §7)."""
    return f"bot-{uuid.uuid4().hex[:20]}"


@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float


class StateStore:
    """Accès SQLite (WAL) à l'état persistant du bot."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------ positions
    def upsert_position(self, pos: Position) -> None:
        self.conn.execute(
            "INSERT INTO positions(symbol, qty, avg_price, updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(symbol) DO UPDATE SET qty=excluded.qty, "
            "avg_price=excluded.avg_price, updated_at=excluded.updated_at",
            (pos.symbol, pos.qty, pos.avg_price, _now()),
        )
        self.conn.commit()

    def get_positions(self) -> dict[str, Position]:
        rows = self.conn.execute("SELECT symbol, qty, avg_price FROM positions").fetchall()
        return {r[0]: Position(r[0], r[1], r[2]) for r in rows if abs(r[1]) > 1e-12}

    # ------------------------------------------------------------ ordres
    def record_order(
        self, client_order_id: str, symbol: str, side: str, qty: float, price: float | None,
        status: str = "pending",
    ) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO orders VALUES(?,?,?,?,?,?,?,?)",
            (client_order_id, symbol, side, qty, price, status, _now(), _now()),
        )
        self.conn.commit()

    def update_order_status(self, client_order_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE orders SET status=?, updated_at=? WHERE client_order_id=?",
            (status, _now(), client_order_id),
        )
        self.conn.commit()

    def order_exists(self, client_order_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM orders WHERE client_order_id=?", (client_order_id,)
        ).fetchone()
        return row is not None

    def pending_orders(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT client_order_id FROM orders WHERE status='pending'"
        ).fetchall()
        return [r[0] for r in rows]

    # ------------------------------------------------------------ equity / kv
    def record_equity(self, equity: float, cash: float) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO equity_history VALUES(?,?,?)", (_now(), equity, cash)
        )
        self.conn.commit()

    def equity_history(self, limit: int = 10_000) -> list[tuple[str, float, float]]:
        return self.conn.execute(
            "SELECT ts, equity, cash FROM equity_history ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()[::-1]

    def set_kv(self, key: str, value: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO kv VALUES(?,?)", (key, value))
        self.conn.commit()

    def get_kv(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    # ------------------------------------------------------------ décisions (R10)
    def log_decision(self, kind: str, symbol: str | None, payload: dict) -> None:
        self.conn.execute(
            "INSERT INTO decisions(ts, kind, symbol, payload) VALUES(?,?,?,?)",
            (_now(), kind, symbol, json.dumps(payload, ensure_ascii=False, default=str)),
        )
        self.conn.commit()

    def decisions(self, since_ts: str | None = None) -> list[tuple]:
        if since_ts:
            return self.conn.execute(
                "SELECT ts, kind, symbol, payload FROM decisions WHERE ts >= ? ORDER BY id",
                (since_ts,),
            ).fetchall()
        return self.conn.execute(
            "SELECT ts, kind, symbol, payload FROM decisions ORDER BY id"
        ).fetchall()


def reconcile(
    local: dict[str, Position], remote: dict[str, float], tolerance_pct: float
) -> list[str]:
    """Compare positions locales vs exchange. Retourne la liste des divergences
    (vide = état cohérent). Toute divergence doit conduire au Safe Mode."""
    problems = []
    symbols = set(local) | set(remote)
    for sym in symbols:
        lq = local[sym].qty if sym in local else 0.0
        rq = remote.get(sym, 0.0)
        ref = max(abs(lq), abs(rq))
        if ref > 1e-12 and abs(lq - rq) / ref > tolerance_pct:
            problems.append(f"{sym}: local={lq:.8f} exchange={rq:.8f}")
    return problems
