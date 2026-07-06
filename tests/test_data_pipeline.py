"""Tests unitaires du pipeline de données (Phase 3) — sans réseau."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data.fetcher import to_dataframe
from src.data.quality import check_ohlcv, correlation_matrix
from src.data.storage import dataset_path, load, merge_frames, save


def make_ohlcv(n: int = 48, freq: str = "1h", start: str = "2024-01-01") -> pd.DataFrame:
    idx = pd.date_range(start, periods=n, freq=freq, tz="UTC", name="timestamp")
    close = 100 + np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": np.full(n, 10.0),
        },
        index=idx,
    )


# ---------------------------------------------------------------- fetcher
def test_to_dataframe_sorts_and_dedupes() -> None:
    rows = [
        [3_600_000, 1, 2, 0.5, 1.5, 10],
        [0, 1, 2, 0.5, 1.2, 10],
        [3_600_000, 1, 2, 0.5, 1.6, 11],  # doublon : le dernier gagne
    ]
    df = to_dataframe(rows)
    assert len(df) == 2
    assert df.index.is_monotonic_increasing
    assert df.index.tz is not None  # UTC
    assert df["close"].iloc[-1] == 1.6


def test_to_dataframe_empty() -> None:
    df = to_dataframe([])
    assert df.empty


# ---------------------------------------------------------------- storage
def test_save_load_roundtrip(tmp_path) -> None:
    df = make_ohlcv(10)
    path = tmp_path / "x" / "1h.parquet"
    save(df, path)
    loaded = load(path)
    pd.testing.assert_frame_equal(df, loaded, check_freq=False)


def test_merge_frames_idempotent() -> None:
    df = make_ohlcv(24)
    older, newer = df.iloc[:16], df.iloc[12:]  # chevauchement de 4 bougies
    merged = merge_frames(older, newer)
    pd.testing.assert_frame_equal(merged, df, check_freq=False)
    # Ré-appliquer la même mise à jour ne change rien (idempotence).
    pd.testing.assert_frame_equal(merge_frames(merged, newer), df, check_freq=False)


def test_dataset_path_layout(tmp_path) -> None:
    p = dataset_path("binance_public", "BTC/USDT", "4h", tmp_path)
    assert p == tmp_path / "binance_public" / "BTC-USDT" / "4h.parquet"


# ---------------------------------------------------------------- qualité
def test_quality_clean_series() -> None:
    r = check_ohlcv(make_ohlcv(48), "BTC/USDT", "1h")
    assert r.ok
    assert r.n_gaps == 0 and r.n_duplicates == 0
    assert r.n_zero_volume == 0 and r.n_extreme_moves == 0


def test_quality_detects_gap() -> None:
    df = make_ohlcv(48)
    df = df.drop(df.index[10:13])  # 3 bougies manquantes
    r = check_ohlcv(df, "BTC/USDT", "1h")
    assert r.n_gaps == 1
    assert "3 bougies manquantes" in r.gap_details[0]


def test_quality_detects_ohlc_violation_and_zero_volume() -> None:
    df = make_ohlcv(24)
    df.iloc[5, df.columns.get_loc("high")] = 0.0  # high < open/close ET prix nul
    df.iloc[7, df.columns.get_loc("volume")] = 0.0
    r = check_ohlcv(df, "BTC/USDT", "1h")
    assert not r.ok
    assert r.n_ohlc_violations >= 1
    assert r.n_zero_volume == 1


def test_quality_detects_extreme_move() -> None:
    df = make_ohlcv(24, freq="1d")
    df.iloc[10, df.columns.get_loc("close")] *= 2  # +100 % en un jour
    r = check_ohlcv(df, "BTC/USDT", "1d")
    assert r.n_extreme_moves >= 1


def test_quality_duplicates_detected() -> None:
    df = make_ohlcv(10)
    df = pd.concat([df, df.iloc[[4]]]).sort_index()
    r = check_ohlcv(df, "X", "1h")
    assert r.n_duplicates == 1
    assert not r.ok


def test_correlation_matrix_perfect_and_inverse() -> None:
    rng = np.random.default_rng(42)
    a = pd.Series(np.cumprod(1 + rng.normal(0.001, 0.02, 200)), name="A")
    corr = correlation_matrix({"A": a, "B": a * 3, "C": 1 / a})
    assert corr.loc["A", "B"] == pytest.approx(1.0)
    assert corr.loc["A", "C"] == pytest.approx(-1.0, abs=0.05)
