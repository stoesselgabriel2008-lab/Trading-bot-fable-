"""Télécharge l'historique OHLCV pour tous les actifs/timeframes de assets.yaml.

Usage : make fetch-data  (reproductible, mise à jour incrémentale idempotente)
Produit : data/{source}/{symbol}/{tf}.parquet + docs/reports/DATA_QUALITY.md
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ccxt

from src.data.fetcher import build_exchange
from src.data.quality import check_ohlcv, correlation_matrix, render_report
from src.data.storage import update_incremental
from src.utils.config import load_assets_config, load_exchange_config
from src.utils.logging_setup import setup_logging

# Historique maximal visé (l'exchange tronque de lui-même au listing du marché).
DEFAULT_SINCE = "2017-01-01T00:00:00Z"


def main() -> int:
    logger = setup_logging()
    assets_cfg = load_assets_config()
    ex_cfg = load_exchange_config()
    source = ex_cfg.data.historical_source
    exchange = build_exchange(source)
    since_ms = ccxt.Exchange.parse8601(DEFAULT_SINCE)

    reports = []
    daily_closes = {}
    for asset in assets_cfg.assets:
        for tf in assets_cfg.timeframes:
            df = update_incremental(exchange, source, asset.symbol, tf, since_ms)
            report = check_ohlcv(df, asset.symbol, tf)
            reports.append(report)
            if tf == "1d":
                daily_closes[asset.symbol] = df["close"]
            logger.info(
                "qualité %s %s : %d bougies, %d gaps, %d doublons, %d violations OHLC",
                asset.symbol,
                tf,
                report.n_rows,
                report.n_gaps,
                report.n_duplicates,
                report.n_ohlc_violations,
            )

    corr = correlation_matrix(daily_closes) if len(daily_closes) >= 2 else None
    out = Path(__file__).resolve().parents[1] / "docs" / "reports" / "DATA_QUALITY.md"
    out.write_text(render_report(reports, corr), encoding="utf-8")
    logger.info("rapport qualité écrit : %s", out)

    blocking = [r for r in reports if not r.ok]
    if blocking:
        logger.error("anomalies bloquantes sur %d dataset(s)", len(blocking))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
