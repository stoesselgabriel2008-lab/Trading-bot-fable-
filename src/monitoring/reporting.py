"""Rapport quotidien auto-généré + implementation shortfall + dashboard HTML.

Implementation shortfall (détecteur ultime d'un backtest trop optimiste) :
comparaison continue de l'expectancy réalisée en paper vs celle prédite par le
backtest de la MÊME stratégie sur la même période récente et aux mêmes coûts.
Divergence forte = investigation obligatoire avant toute autre chose.
"""

from __future__ import annotations

import base64
import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.backtest.engine import CostModel, run_backtest
from src.execution.state import StateStore
from src.strategies.base import Strategy


@dataclass
class DailySnapshot:
    date: str
    equity: float
    pnl_since_start: float
    current_drawdown: float
    n_orders: int
    n_decisions: int
    n_api_errors: int
    positions: dict[str, float]


def build_snapshot(store: StateStore) -> DailySnapshot:
    hist = store.equity_history()
    equity = hist[-1][1] if hist else 0.0
    first = hist[0][1] if hist else equity
    peak = max((h[1] for h in hist), default=equity)
    decisions = store.decisions()
    return DailySnapshot(
        date=datetime.now(UTC).strftime("%Y-%m-%d"),
        equity=equity,
        pnl_since_start=(equity / first - 1) if first else 0.0,
        current_drawdown=(equity / peak - 1) if peak else 0.0,
        n_orders=sum(1 for d in decisions if d[1] == "order"),
        n_decisions=len(decisions),
        n_api_errors=sum(1 for d in decisions if d[1] == "error"),
        positions={s: p.qty for s, p in store.get_positions().items()},
    )


def realized_expectancy(store: StateStore) -> tuple[float | None, int]:
    """Expectancy réalisée par aller-retour en paper (approx. par symbole FIFO).

    Retourne (expectancy en fraction d'equity, nombre d'aller-retours) ;
    (None, n) si l'échantillon est vide.
    """
    fills: dict[str, list[tuple[float, float]]] = {}
    pnls: list[float] = []
    equity0 = None
    for _ts, kind, symbol, payload in store.decisions():
        if kind == "target" and equity0 is None:
            equity0 = json.loads(payload).get("equity")
        if kind != "order":
            continue
        p = json.loads(payload)
        book = fills.setdefault(symbol, [])
        if p["side"] == "buy":
            book.append((p["qty"], p["price"]))
        else:  # sell : clôt FIFO
            qty_to_close = p["qty"]
            while qty_to_close > 1e-12 and book:
                q, buy_px = book[0]
                used = min(q, qty_to_close)
                pnl = used * (p["price"] - buy_px) - p.get("fee", 0.0)
                ref = equity0 or 10_000.0
                pnls.append(pnl / ref)
                if used >= q:
                    book.pop(0)
                else:
                    book[0] = (q - used, buy_px)
                qty_to_close -= used
    if not pnls:
        return None, 0
    return sum(pnls) / len(pnls), len(pnls)


def backtest_expectancy(
    strategy: Strategy,
    data: dict[str, pd.DataFrame],
    cost: CostModel,
) -> tuple[float | None, int]:
    """Expectancy prédite par le backtest de la même stratégie (mêmes coûts)."""
    targets = strategy.generate_targets(data)
    res = run_backtest(data, targets, cost)
    pnls = [t.pnl_pct_of_equity for t in res.trades]
    if not pnls:
        return None, 0
    return sum(pnls) / len(pnls), len(pnls)


def render_daily_report(
    snap: DailySnapshot,
    shortfall_realized: tuple[float | None, int],
    shortfall_backtest: tuple[float | None, int],
    strategy_label: str,
) -> str:
    r_exp, r_n = shortfall_realized
    b_exp, b_n = shortfall_backtest
    lines = [
        f"# Rapport quotidien — {snap.date}",
        "",
        f"Stratégie exécutée : {strategy_label}",
        "",
        f"- Equity : **{snap.equity:,.2f} USDT** (P&L depuis le début : {snap.pnl_since_start:+.2%})",
        f"- Drawdown courant : {snap.current_drawdown:.2%}",
        f"- Positions ouvertes : {snap.positions or 'aucune'}",
        f"- Ordres exécutés (cumul) : {snap.n_orders} · Décisions journalisées : {snap.n_decisions}",
        f"- Erreurs API (cumul) : {snap.n_api_errors}",
        "",
        "## Implementation shortfall (paper vs backtest)",
    ]
    if r_exp is None or b_exp is None:
        lines.append(
            f"- Échantillon insuffisant pour conclure (paper : {r_n} aller-retours, "
            f"backtest : {b_n} trades). Le suivi continue — aucune conclusion ne sera "
            "tirée sans données suffisantes (honnêteté avant tout)."
        )
    else:
        gap = r_exp - b_exp
        lines += [
            f"- Expectancy réalisée (paper, {r_n} AR) : {r_exp:+.4%} / trade",
            f"- Expectancy prédite (backtest, {b_n} trades) : {b_exp:+.4%} / trade",
            f"- Écart : {gap:+.4%}"
            + (
                " — ⚠️ DIVERGENCE FORTE : investigation obligatoire avant toute autre chose."
                if abs(gap) > max(0.5 * abs(b_exp), 0.002)
                else " — dans la tolérance."
            ),
        ]
    return "\n".join(lines) + "\n"


def render_dashboard_html(store: StateStore, strategy_label: str) -> str:
    """Dashboard HTML statique : equity curve (PNG base64), positions, santé."""
    hist = store.equity_history()
    img_b64 = ""
    if len(hist) >= 2:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        ts = [h[0][:16] for h in hist]
        eq = [h[1] for h in hist]
        fig, ax = plt.subplots(figsize=(9, 3.5))
        ax.plot(range(len(eq)), eq)
        ax.set_xticks([0, len(eq) - 1])
        ax.set_xticklabels([ts[0], ts[-1]])
        ax.set_title("Equity (paper)")
        ax.grid(True, alpha=0.3)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
        plt.close(fig)
        img_b64 = base64.b64encode(buf.getvalue()).decode()

    snap = build_snapshot(store)
    positions_rows = (
        "".join(f"<tr><td>{s}</td><td>{q:.8f}</td></tr>" for s, q in snap.positions.items())
        or "<tr><td colspan=2>aucune</td></tr>"
    )
    img_tag = (
        f'<img src="data:image/png;base64,{img_b64}" alt="equity"/>'
        if img_b64
        else "<p>historique insuffisant</p>"
    )
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Trading bot — dashboard paper</title>
<style>body{{font-family:system-ui;margin:2rem;max-width:900px}}table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:4px 10px}}­.warn{{color:#b00;font-weight:bold}}</style></head><body>
<h1>Dashboard paper trading</h1>
<p class="warn">⚠️ {strategy_label}</p>
<p>Généré le {datetime.now(UTC).isoformat()} — equity <b>{snap.equity:,.2f}</b> USDT,
P&amp;L {snap.pnl_since_start:+.2%}, drawdown courant {snap.current_drawdown:.2%},
{snap.n_orders} ordres, {snap.n_api_errors} erreurs API.</p>
{img_tag}
<h2>Positions</h2><table><tr><th>Symbole</th><th>Quantité</th></tr>{positions_rows}</table>
</body></html>"""


def write_all_reports(
    store: StateStore,
    strategy: Strategy,
    data: dict[str, pd.DataFrame],
    cost: CostModel,
    out_dir: str | Path,
    strategy_label: str,
) -> Path:
    """Génère rapport quotidien + dashboard + exports CSV. Retourne le chemin du rapport."""
    from src.monitoring.journal import export_decisions_csv, export_trades_csv

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    snap = build_snapshot(store)
    report = render_daily_report(
        snap, realized_expectancy(store), backtest_expectancy(strategy, data, cost), strategy_label
    )
    report_path = out / f"DAILY_{snap.date}.md"
    report_path.write_text(report, encoding="utf-8")
    (out / "dashboard.html").write_text(
        render_dashboard_html(store, strategy_label), encoding="utf-8"
    )
    export_decisions_csv(store, out / "decisions.csv")
    export_trades_csv(store, out / "trades.csv")
    return report_path
