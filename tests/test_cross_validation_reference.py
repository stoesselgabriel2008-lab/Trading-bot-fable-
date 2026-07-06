"""Validation croisée du moteur maison contre backtesting.py (Phase 4, test n°3).

Backtest identique (croisement EMA 20/50, BTC/USDT 1d, mêmes frais 0,1 %,
exécution à l'open de la bougie suivante) dans les deux moteurs — les résultats
doivent concorder. Tout écart au-delà de la tolérance doit être expliqué.

Nécessite les données réelles (make fetch-data) ; sauté sinon.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.engine import CostModel, run_backtest
from src.data.storage import DATA_DIR, dataset_path, load

DATA_PATH = dataset_path("binance_public", "BTC/USDT", "1d", DATA_DIR)

pytestmark = pytest.mark.skipif(
    not DATA_PATH.exists(), reason="données réelles absentes (lancer make fetch-data)"
)

FEE = 0.001
EMA_FAST, EMA_SLOW = 20, 50


def load_btc_daily() -> pd.DataFrame:
    df = load(DATA_PATH)
    assert df is not None
    # Fenêtre fixe pour la reproductibilité du test.
    return df.loc["2019-01-01":"2024-12-31"]


def ema_signal(close: pd.Series) -> pd.Series:
    fast = close.ewm(span=EMA_FAST, adjust=False).mean()
    slow = close.ewm(span=EMA_SLOW, adjust=False).mean()
    return (fast > slow).astype(float)


def run_our_engine(df: pd.DataFrame) -> float:
    targets = pd.DataFrame({"BTC": ema_signal(df["close"])}, index=df.index)
    res = run_backtest({"BTC": df}, targets, CostModel(fee_rate=FEE, slippage_rate=0.0))
    return float(res.equity.iloc[-1])


def run_reference_engine(df: pd.DataFrame) -> float:
    from backtesting import Backtest, Strategy

    # backtesting.py trade en unités entières : on réduit l'échelle des prix pour
    # rendre les parts quasi fractionnaires (astuce documentée), sans changer les
    # rendements relatifs.
    scale = 1e-6
    naive = df.copy()
    naive.index = naive.index.tz_localize(None)
    data = pd.DataFrame(
        {
            "Open": naive["open"] * scale,
            "High": naive["high"] * scale,
            "Low": naive["low"] * scale,
            "Close": naive["close"] * scale,
            "Volume": naive["volume"],
        }
    )

    class EmaCross(Strategy):
        def init(self) -> None:
            close = pd.Series(self.data.Close, index=self.data.index)
            self.signal = self.I(lambda: ema_signal(close).to_numpy(), name="signal", overlay=False)

        def next(self) -> None:
            if self.signal[-1] > 0.5 and not self.position:
                self.buy()
            elif self.signal[-1] < 0.5 and self.position:
                self.position.close()

    bt = Backtest(data, EmaCross, cash=1_000_000, commission=FEE, exclusive_orders=False)
    stats = bt.run()
    return float(stats["Equity Final [$]"] / 1_000_000)


def test_engine_matches_reference_on_real_btc() -> None:
    df = load_btc_daily()
    ours = run_our_engine(df)
    reference = run_reference_engine(df)
    # Tolérance 2 % relative : résidu attendu = arrondi aux parts entières de
    # backtesting.py (atténué par le rescaling) et gestion du cash fractionnel.
    assert ours == pytest.approx(reference, rel=0.02), (
        f"moteur maison {ours:.4f} vs backtesting.py {reference:.4f} — "
        "écart > 2 %, à investiguer avant de continuer"
    )
