"""Indicateurs techniques en pandas pur (aucune dépendance TA externe).

Tous les indicateurs sont strictement causaux : la valeur en t ne dépend que
des données ≤ t (rolling non centré, ewm standard).
"""

from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI de Wilder (lissage exponentiel alpha=1/period)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, float("nan"))
    out = 100 - 100 / (1 + rs)
    return out.fillna(50.0)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (lissage de Wilder)."""
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def donchian(df: pd.DataFrame, window: int) -> tuple[pd.Series, pd.Series]:
    """Canal de Donchian : (plus haut, plus bas) des ``window`` bougies CLOSES
    précédentes — décalé de 1 pour exclure la bougie courante du canal."""
    upper = df["high"].rolling(window).max().shift(1)
    lower = df["low"].rolling(window).min().shift(1)
    return upper, lower


def zscore(series: pd.Series, window: int) -> pd.Series:
    mean = series.rolling(window).mean()
    std = series.rolling(window).std(ddof=0)
    return (series - mean) / std.replace(0.0, float("nan"))


def realized_vol(close: pd.Series, window: int) -> pd.Series:
    """Volatilité réalisée des rendements simples (écart-type glissant, par bougie)."""
    return close.pct_change().rolling(window).std(ddof=0)
