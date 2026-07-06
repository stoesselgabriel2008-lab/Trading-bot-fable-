"""Brokers d'exécution.

- ``PaperBroker`` : simulation locale — fills au dernier prix connu + slippage,
  frais taker appliqués, positions/cash simulés. Aucune clé API requise.
- ``CcxtBroker`` : adaptateur ccxt (Bybit demo/testnet/live) avec retries à
  backoff exponentiel et clientOrderId idempotents. Le mode ``live`` est
  VERROUILLÉ (R6) : il exige `live_trading: true` dans la config, la
  GO_LIVE_CHECKLIST complétée et une confirmation humaine — jamais activé
  par le bot lui-même.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import ccxt

from src.execution.state import new_client_order_id
from src.utils.logging_setup import get_logger

logger = get_logger("execution.broker")


@dataclass
class Fill:
    client_order_id: str
    symbol: str
    side: str  # buy | sell
    qty: float
    price: float
    fee: float


class PaperBroker:
    """Simulation locale d'exécution au marché (mode ``paper``)."""

    def __init__(self, initial_cash: float, taker_fee: float, slippage_bps: float) -> None:
        self.cash = initial_cash
        self.taker_fee = taker_fee
        self.slippage = slippage_bps / 10_000.0
        self.positions: dict[str, float] = {}  # qty par symbole

    def market_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        ref_price: float,
        client_order_id: str | None = None,
    ) -> Fill:
        """Exécute immédiatement au prix de référence ± slippage."""
        coid = client_order_id or new_client_order_id()
        price = (
            ref_price * (1 + self.slippage) if side == "buy" else ref_price * (1 - self.slippage)
        )
        notional = qty * price
        fee = notional * self.taker_fee
        if side == "buy":
            total = notional + fee
            if total > self.cash + 1e-9:
                raise ValueError(f"cash insuffisant : {total:.2f} > {self.cash:.2f}")
            self.cash -= total
            self.positions[symbol] = self.positions.get(symbol, 0.0) + qty
        else:
            held = self.positions.get(symbol, 0.0)
            if qty > held + 1e-9:
                raise ValueError(f"vente à découvert interdite : {qty} > {held}")
            self.cash += notional - fee
            self.positions[symbol] = held - qty
        logger.info(
            "PAPER FILL %s %s %s qty=%.8f px=%.2f fee=%.4f", coid, side, symbol, qty, price, fee
        )
        return Fill(coid, symbol, side, qty, price, fee)

    def equity(self, prices: dict[str, float]) -> float:
        return self.cash + sum(q * prices.get(s, 0.0) for s, q in self.positions.items())

    def remote_positions(self) -> dict[str, float]:
        """Équivalent de « l'état exchange » pour la réconciliation en mode paper."""
        return {s: q for s, q in self.positions.items() if abs(q) > 1e-12}


class CcxtBroker:
    """Ordres réels via ccxt (testnet/demo Bybit). Live verrouillé (R6)."""

    MAX_RETRIES = 4

    def __init__(
        self,
        exchange_id: str,
        mode: str,
        live_trading: bool,
        api_key: str = "",
        api_secret: str = "",
    ) -> None:
        if mode == "live" and not live_trading:
            raise PermissionError(
                "Mode live demandé mais live_trading=false — verrou R6. "
                "Voir docs/GO_LIVE_CHECKLIST.md."
            )
        if mode == "live":
            raise PermissionError(
                "Le passage en live exige une confirmation humaine explicite hors bot (R6) "
                "— non implémenté volontairement dans cette mission."
            )
        klass = getattr(ccxt, exchange_id)
        self.exchange = klass(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "trust_env": True,
                "requests_trust_env": True,
            }
        )
        if mode == "testnet":
            self.exchange.set_sandbox_mode(True)

    def _with_retries(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        delay = 2.0
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return fn(*args, **kwargs)
            except (ccxt.NetworkError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as exc:
                if attempt == self.MAX_RETRIES:
                    raise
                logger.warning("retry %d/%d après %s", attempt + 1, self.MAX_RETRIES, exc)
                time.sleep(delay)
                delay *= 2

    def market_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        ref_price: float,
        client_order_id: str | None = None,
    ) -> Fill:
        coid = client_order_id or new_client_order_id()
        # clientOrderId transmis -> en cas de timeout, re-soumettre avec le MÊME id
        # est sans danger : l'exchange dédoublonne (idempotence, RESEARCH §7).
        order = self._with_retries(
            self.exchange.create_order,
            symbol,
            "market",
            side,
            qty,
            None,
            {"clientOrderId": coid},
        )
        price = float(order.get("average") or order.get("price") or ref_price)
        fee_cost = 0.0
        if order.get("fee") and order["fee"].get("cost"):
            fee_cost = float(order["fee"]["cost"])
        return Fill(coid, symbol, side, qty, price, fee_cost)

    def remote_positions(self) -> dict[str, float]:
        balance = self._with_retries(self.exchange.fetch_balance)
        out = {}
        for currency, amount in balance.get("total", {}).items():
            if amount and currency not in ("USDT", "USD", "EUR"):
                out[f"{currency}/USDT"] = float(amount)
        return out

    def cancel_all(self, symbols: list[str]) -> None:
        for sym in symbols:
            try:
                self._with_retries(self.exchange.cancel_all_orders, sym)
            except ccxt.BaseError as exc:  # rien à annuler, marché fermé…
                logger.warning("cancel_all %s : %s", sym, exc)
