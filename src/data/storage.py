"""Stockage parquet des OHLCV et mise à jour incrémentale idempotente.

Layout : ``data/{source}/{BASE-QUOTE}/{timeframe}.parquet``.
Écritures atomiques (fichier temporaire + rename) — cf. RESEARCH.md §7,
pattern « écritures non atomiques » des bots en production.
"""

from __future__ import annotations

import os
from pathlib import Path

import ccxt
import pandas as pd

from src.data.fetcher import fetch_ohlcv_history, timeframe_ms
from src.utils.logging_setup import get_logger

logger = get_logger("data.storage")

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

#: Chevauchement re-téléchargé lors d'une mise à jour incrémentale (bougies),
#: pour absorber d'éventuelles corrections de la dernière page par l'exchange.
_OVERLAP_BARS = 3


def dataset_path(source: str, symbol: str, timeframe: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / source / symbol.replace("/", "-") / f"{timeframe}.parquet"


def save(df: pd.DataFrame, path: Path) -> None:
    """Écriture parquet atomique (tmp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp)
    os.replace(tmp, path)


def load(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_parquet(path)


def merge_frames(existing: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame:
    """Fusionne ancien + nouveau : dédupliqué par timestamp (le nouveau gagne), trié."""
    if existing is None or existing.empty:
        return new
    merged = pd.concat([existing, new])
    merged = merged[~merged.index.duplicated(keep="last")].sort_index()
    return merged


def update_incremental(
    exchange: ccxt.Exchange,
    source: str,
    symbol: str,
    timeframe: str,
    default_since_ms: int,
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """Met à jour le parquet local — idempotent (relançable sans effet de bord).

    Reprend ``_OVERLAP_BARS`` bougies avant la dernière connue ; premier appel =
    téléchargement complet depuis ``default_since_ms``.
    """
    path = dataset_path(source, symbol, timeframe, data_dir)
    existing = load(path)
    if existing is not None and not existing.empty:
        last_ms = int(existing.index.max().timestamp() * 1000)
        since = last_ms - _OVERLAP_BARS * timeframe_ms(timeframe)
    else:
        since = default_since_ms
    fresh = fetch_ohlcv_history(exchange, symbol, timeframe, since_ms=since)
    merged = merge_frames(existing, fresh)
    save(merged, path)
    logger.info("dataset %s %s %s : %d bougies au total", source, symbol, timeframe, len(merged))
    return merged
