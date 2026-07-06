"""Contrôle qualité systématique des OHLCV.

Contrôles (cf. RESEARCH.md §6) : gaps temporels, doublons, cohérence OHLC,
volume nul, mouvements extrêmes. Politique : **jamais d'interpolation
silencieuse** — les anomalies sont détectées, comptées et journalisées, les
données brutes sont conservées telles quelles.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.data.fetcher import timeframe_ms

#: Seuil de mouvement close-to-close considéré « extrême » par timeframe.
EXTREME_MOVE_THRESHOLDS = {"1h": 0.10, "4h": 0.20, "1d": 0.30}


@dataclass
class QualityReport:
    """Résultat du contrôle qualité d'une série OHLCV."""

    symbol: str
    timeframe: str
    n_rows: int
    start: str
    end: str
    n_duplicates: int
    n_gaps: int
    gap_details: list[str]
    n_ohlc_violations: int
    n_zero_volume: int
    n_extreme_moves: int
    extreme_details: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Vrai si aucune anomalie bloquante (doublons ou incohérences OHLC)."""
        return self.n_duplicates == 0 and self.n_ohlc_violations == 0

    def to_markdown_row(self) -> str:
        status = "✅" if self.ok else "❌"
        return (
            f"| {self.symbol} | {self.timeframe} | {self.n_rows} | {self.start} → {self.end} "
            f"| {self.n_duplicates} | {self.n_gaps} | {self.n_ohlc_violations} "
            f"| {self.n_zero_volume} | {self.n_extreme_moves} | {status} |"
        )


def check_ohlcv(df: pd.DataFrame, symbol: str, timeframe: str) -> QualityReport:
    """Analyse une série OHLCV et retourne un rapport de qualité complet."""
    if df.empty:
        return QualityReport(symbol, timeframe, 0, "-", "-", 0, 0, [], 0, 0, 0)

    n_dup = int(df.index.duplicated().sum())

    # Gaps : différences d'index supérieures à l'intervalle attendu.
    tf = pd.Timedelta(milliseconds=timeframe_ms(timeframe))
    deltas = df.index.to_series().diff().dropna()
    gaps = deltas[deltas > tf]
    gap_details = [
        f"{ts.isoformat()} : trou de {delta} ({int(delta / tf) - 1} bougies manquantes)"
        for ts, delta in gaps.items()
    ]

    # Cohérence OHLC : high >= max(open, close) et low <= min(open, close), prix > 0.
    bad_high = df["high"] < df[["open", "close"]].max(axis=1)
    bad_low = df["low"] > df[["open", "close"]].min(axis=1)
    non_positive = (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
    n_violations = int((bad_high | bad_low | non_positive).sum())

    n_zero_vol = int((df["volume"] == 0).sum())

    threshold = EXTREME_MOVE_THRESHOLDS.get(timeframe, 0.20)
    returns = df["close"].pct_change().abs()
    extreme = returns[returns > threshold]
    extreme_details = [f"{ts.isoformat()} : |Δclose| = {r:.1%}" for ts, r in extreme.items()]

    return QualityReport(
        symbol=symbol,
        timeframe=timeframe,
        n_rows=len(df),
        start=str(df.index.min()),
        end=str(df.index.max()),
        n_duplicates=n_dup,
        n_gaps=len(gaps),
        gap_details=gap_details[:20],
        n_ohlc_violations=n_violations,
        n_zero_volume=n_zero_vol,
        n_extreme_moves=len(extreme),
        extreme_details=extreme_details[:20],
    )


def correlation_matrix(closes: dict[str, pd.Series]) -> pd.DataFrame:
    """Corrélation des rendements journaliers entre actifs (RESEARCH.md §5)."""
    returns = pd.DataFrame({sym: s.pct_change() for sym, s in closes.items()}).dropna()
    return returns.corr()


def render_report(reports: list[QualityReport], correlations: pd.DataFrame | None) -> str:
    """Génère le rapport qualité markdown complet."""
    lines = [
        "# Rapport de qualité des données",
        "",
        "| Actif | TF | Bougies | Période | Doublons | Gaps | OHLC KO | Vol=0 | Moves extrêmes | OK |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    lines += [r.to_markdown_row() for r in reports]
    for r in reports:
        if r.gap_details or r.extreme_details:
            lines += ["", f"## Détails {r.symbol} {r.timeframe}"]
            lines += [f"- GAP {d}" for d in r.gap_details]
            lines += [f"- EXTREME {d}" for d in r.extreme_details]
    if correlations is not None:
        lines += [
            "",
            "## Corrélation des rendements journaliers (illusion de diversification, R§5)",
            "",
            "```",
            correlations.round(3).to_string(),
            "```",
        ]
    return "\n".join(lines) + "\n"
