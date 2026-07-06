"""Boucle d'exécution du bot (mode paper par défaut).

Cycle (à chaque clôture de bougie) :
 1. kill switch ?           -> arrêt propre
 2. données fraîches        (bougies CLÔTURÉES uniquement)
 3. réconciliation          local (SQLite) vs broker -> divergence = Safe Mode
 4. circuit breakers        (equity, pertes, erreurs API)
 5. stratégies -> poids     (même code que le backtest)
 6. RiskManager.clamp       (R8 — refus journalisés)
 7. ordres delta            (rebalancement si |Δpoids| > seuil)
 8. persistance + journal   (TOUTES les décisions, R10)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data.fetcher import build_exchange, fetch_ohlcv_history, timeframe_ms
from src.execution.broker import PaperBroker
from src.execution.state import Position, StateStore, new_client_order_id, reconcile
from src.risk.breakers import Action, CircuitBreakers
from src.risk.manager import RiskManager
from src.strategies.base import Strategy
from src.utils.config import ExchangeConfig, RiskConfig
from src.utils.logging_setup import get_logger

logger = get_logger("execution.executor")

KILL_FLAG = Path(__file__).resolve().parents[2] / "state" / "KILL"
#: rebalancement seulement si l'écart de poids dépasse ce seuil (limite le churn)
REBALANCE_THRESHOLD = 0.02
#: bougies d'historique conservées pour le calcul des signaux
LOOKBACK_BARS = 600


@dataclass
class CycleReport:
    ts: str
    equity: float
    action: str  # traded | no_trade | paused | halted | killed | safe_mode
    detail: str = ""


class PaperExecutor:
    """Orchestre N stratégies × M actifs en mode paper (simulation locale)."""

    def __init__(
        self,
        strategy: Strategy,
        symbols: list[str],
        timeframe: str,
        exchange_cfg: ExchangeConfig,
        risk_cfg: RiskConfig,
        state_path: str | Path = "state/bot.sqlite",
        strategy_label: str = "",
    ) -> None:
        self.strategy = strategy
        self.symbols = symbols
        self.timeframe = timeframe
        self.cfg = exchange_cfg
        self.store = StateStore(state_path)
        self.risk = RiskManager(risk_cfg)
        self.breakers = CircuitBreakers(risk_cfg)
        self.label = strategy_label
        self.data_exchange = build_exchange(exchange_cfg.data.live_source)
        self.broker = PaperBroker(
            initial_cash=float(
                self.store.get_kv("cash", str(risk_cfg.capital.initial)) or risk_cfg.capital.initial
            ),
            taker_fee=exchange_cfg.fees.taker,
            slippage_bps=exchange_cfg.slippage.base_bps,
        )
        # Reprise après crash : recharger les positions persistées dans le broker simulé.
        for sym, pos in self.store.get_positions().items():
            self.broker.positions[sym] = pos.qty
        self.halted = False

    # ------------------------------------------------------------------ data
    def fetch_closed_candles(self) -> dict[str, pd.DataFrame]:
        out = {}
        tf_ms = timeframe_ms(self.timeframe)
        since = self.data_exchange.milliseconds() - LOOKBACK_BARS * tf_ms
        for sym in self.symbols:
            out[sym] = fetch_ohlcv_history(self.data_exchange, sym, self.timeframe, since)
        return out

    # ------------------------------------------------------------------ cycle
    def run_cycle(self) -> CycleReport:
        ts = pd.Timestamp.utcnow().isoformat()

        # 1. Kill switch manuel.
        if KILL_FLAG.exists():
            self.store.log_decision("kill", None, {"reason": "kill switch flag présent"})
            logger.critical("KILL SWITCH détecté -> arrêt propre")
            self.halted = True
            return CycleReport(ts, self.last_equity({}), "killed", "kill switch")

        if self.halted:
            return CycleReport(ts, self.last_equity({}), "halted", "précédemment arrêté")

        # 2. Données fraîches (bougies clôturées).
        try:
            data = self.fetch_closed_candles()
        except Exception as exc:
            self.breakers.record_api_error()
            self.store.log_decision("error", None, {"stage": "fetch", "error": str(exc)})
            logger.error("échec fetch données : %s", exc)
            return CycleReport(ts, self.last_equity({}), "no_trade", f"fetch KO: {exc}")

        prices = {s: float(df["close"].iloc[-1]) for s, df in data.items() if len(df)}
        equity = self.broker.equity(prices)

        # 3. Réconciliation : SQLite (vérité persistée) vs broker (vérité « exchange »).
        problems = reconcile(
            self.store.get_positions(),
            self.broker.remote_positions(),
            self.risk.config.circuit_breakers.reconciliation_tolerance_pct,
        )
        if problems:
            self.store.log_decision("breaker", None, {"reconciliation": problems})
            logger.critical("SAFE MODE : divergence de réconciliation %s", problems)
            self.halted = True
            return CycleReport(ts, equity, "safe_mode", "; ".join(problems))

        # 4. Circuit breakers.
        status = self.breakers.check(equity)
        if status.action is Action.HALT:
            self.store.log_decision("breaker", None, {"halt": status.reason})
            self.halted = True
            return CycleReport(ts, equity, "halted", status.reason)
        if status.action is Action.PAUSE:
            self.store.log_decision("breaker", None, {"pause": status.reason})
            return CycleReport(ts, equity, "paused", status.reason)

        # 5. Stratégies -> poids cibles (dernière bougie clôturée).
        targets_matrix = self.strategy.generate_targets(data)
        raw_targets = {s: float(targets_matrix[s].iloc[-1]) for s in targets_matrix.columns}
        self.store.log_decision(
            "target", None, {"strategy": self.label, "targets": raw_targets, "equity": equity}
        )

        # 6. Limites de risque (R8).
        targets, clamp_report = self.risk.clamp_targets(raw_targets)
        for adj in clamp_report.adjustments:
            self.store.log_decision("risk_clamp", None, {"adjustment": adj})

        # 7. Ordres delta.
        traded = self._rebalance(targets, prices, equity)

        # 8. Persistance.
        equity_after = self.broker.equity(prices)
        self.store.record_equity(equity_after, self.broker.cash)
        self.store.set_kv("cash", str(self.broker.cash))
        if not traded:
            self.store.log_decision("no_trade", None, {"reason": "poids dans la tolérance"})
        return CycleReport(ts, equity_after, "traded" if traded else "no_trade")

    # ------------------------------------------------------------------ ordres
    def _rebalance(
        self, targets: dict[str, float], prices: dict[str, float], equity: float
    ) -> bool:
        traded = False
        for sym, target_w in targets.items():
            price = prices.get(sym)
            if not price:
                continue
            current_qty = self.broker.positions.get(sym, 0.0)
            current_w = current_qty * price / equity if equity > 0 else 0.0
            delta_w = target_w - current_w
            if abs(delta_w) < REBALANCE_THRESHOLD:
                continue
            # Plafond de taille d'ordre (R8) — l'exécuteur écrête, jamais la stratégie.
            delta_w, refusal = self.risk.clamp_order_size(sym, delta_w)
            if refusal:
                self.store.log_decision("risk_clamp", sym, {"order": refusal})
            qty = abs(delta_w) * equity / price
            side = "buy" if delta_w > 0 else "sell"
            if side == "sell":
                qty = min(qty, current_qty)
            if qty * price < 5.0:  # notionnel minimal (poussière)
                continue
            coid = new_client_order_id()
            self.store.record_order(coid, sym, side, qty, price)
            try:
                fill = self.broker.market_order(sym, side, qty, price, client_order_id=coid)
            except ValueError as exc:
                self.store.update_order_status(coid, "rejected")
                self.store.log_decision("error", sym, {"order": coid, "error": str(exc)})
                continue
            self.store.update_order_status(coid, "filled")
            new_qty = self.broker.positions.get(sym, 0.0)
            self.store.upsert_position(Position(sym, new_qty, fill.price))
            self.store.log_decision(
                "order",
                sym,
                {"coid": coid, "side": side, "qty": qty, "price": fill.price, "fee": fill.fee},
            )
            pnl_estimate = -fill.fee if side == "buy" else (fill.price * qty) * 0.0
            self.breakers.record_trade_result(pnl_estimate)
            traded = True
        return traded

    def last_equity(self, prices: dict[str, float]) -> float:
        hist = self.store.equity_history(limit=1)
        if hist:
            return hist[-1][1]
        return self.broker.equity(prices) if prices else self.broker.cash
