"""Téléchargement OHLCV multi-sources via ccxt.

Sources supportées :
- ``binance_public`` : endpoint public data-api.binance.vision (aucune clé requise,
  historique spot le plus profond — ADR-002).
- ``bybit`` : API publique Bybit (exchange d'exécution).

Les instances ccxt sont créées avec ``trust_env`` afin d'honorer les proxys et
bundles CA de l'environnement (HTTPS_PROXY / REQUESTS_CA_BUNDLE) ; sans proxy,
c'est un no-op. La vérification TLS n'est JAMAIS désactivée.
"""

from __future__ import annotations

import time
from typing import Any

import ccxt
import pandas as pd

from src.utils.logging_setup import get_logger

logger = get_logger("data.fetcher")

OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]
_PAGE_LIMIT = 1000
_MAX_RETRIES = 4


def build_exchange(source: str) -> ccxt.Exchange:
    """Construit l'instance ccxt correspondant à une source de données."""
    common: dict[str, Any] = {
        "trust_env": True,
        "requests_trust_env": True,
        "enableRateLimit": True,
    }
    if source == "binance_public":
        ex = ccxt.binance({**common, "options": {"fetchMarkets": ["spot"]}})
        # Endpoint public sans authentification (cf. RESEARCH.md §2).
        ex.urls["api"]["public"] = "https://data-api.binance.vision/api/v3"
        return ex
    if source == "bybit":
        return ccxt.bybit(common)
    raise ValueError(f"Source de données inconnue : {source!r}")


def timeframe_ms(timeframe: str) -> int:
    """Durée d'une bougie en millisecondes (ex. '1h' -> 3_600_000)."""
    return int(ccxt.Exchange.parse_timeframe(timeframe) * 1000)


def _fetch_page_with_retries(
    exchange: ccxt.Exchange, symbol: str, timeframe: str, since: int
) -> list[list[float]]:
    delay = 2.0
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=_PAGE_LIMIT)
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as exc:
            if attempt == _MAX_RETRIES:
                raise
            logger.warning(
                "fetch_ohlcv %s %s retry %d/%d après erreur réseau: %s",
                symbol,
                timeframe,
                attempt + 1,
                _MAX_RETRIES,
                exc,
            )
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def fetch_ohlcv_history(
    exchange: ccxt.Exchange,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int | None = None,
) -> pd.DataFrame:
    """Télécharge l'historique OHLCV complet par pagination time-based.

    - Avance ``since`` après chaque page ; déduplique par timestamp.
    - **Rejette la dernière bougie si elle n'est pas clôturée** (anti-lookahead,
      cf. RESEARCH.md §4 : la bougie courante est incomplète).

    Returns:
        DataFrame indexé par DatetimeIndex UTC croissant, colonnes OHLCV float.
    """
    tf_ms = timeframe_ms(timeframe)
    now_ms = exchange.milliseconds() if until_ms is None else until_ms
    rows: list[list[float]] = []
    cursor = since_ms
    while cursor < now_ms:
        page = _fetch_page_with_retries(exchange, symbol, timeframe, cursor)
        if not page:
            break
        rows.extend(page)
        last_ts = int(page[-1][0])
        next_cursor = last_ts + tf_ms
        if next_cursor <= cursor:  # aucune progression -> stop (sécurité anti-boucle)
            break
        cursor = next_cursor
    df = to_dataframe(rows)
    # Rejet de la bougie non clôturée : une bougie ouverte à t est close à t+tf.
    if not df.empty:
        cutoff = pd.Timestamp(now_ms - tf_ms + 1, unit="ms", tz="UTC")
        df = df[df.index <= cutoff]
    logger.info(
        "fetch %s %s : %d bougies (%s -> %s)",
        symbol,
        timeframe,
        len(df),
        df.index.min() if not df.empty else None,
        df.index.max() if not df.empty else None,
    )
    return df


def to_dataframe(rows: list[list[float]]) -> pd.DataFrame:
    """Convertit les lignes ccxt en DataFrame OHLCV normalisé (UTC, trié, dédupliqué)."""
    if not rows:
        return pd.DataFrame(columns=OHLCV_COLUMNS[1:]).set_axis(
            pd.DatetimeIndex([], tz="UTC", name="timestamp"), axis=0
        )
    df = pd.DataFrame(rows, columns=OHLCV_COLUMNS)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = (
        df.drop_duplicates(subset="timestamp", keep="last")
        .sort_values("timestamp")
        .set_index("timestamp")
        .astype(float)
    )
    return df
