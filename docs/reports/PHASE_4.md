# Rapport de Phase 4 — Moteur de backtest réaliste

**Date :** 2026-07-06 · **Statut : ✅**

## Livré

- `src/backtest/engine.py` : moteur vectorisé multi-actifs — poids décidés à la
  clôture de t → effectifs à l'**open de t+1** (`shift(1)`), coûts = turnover ×
  (taker + slippage), long-only, positions fractionnaires, exposition brute ≤ 1
  (pas de levier), actifs non cotés forcés à poids 0, épisodes de trade extraits.
- `src/backtest/metrics.py` : rendement total/annualisé, volatilité, Sharpe,
  Sortino, Calmar, max drawdown + durée, profit factor, win rate, expectancy,
  exposition moyenne, nb de trades, turnover, frais cumulés (base 365 j/24 h).
- `CostModel.from_configs(...)` avec multiplicateurs de stress (préparé pour la
  Phase 6 : frais ×1,5, slippage ×2).

## Les 3 tests anti-lookahead OBLIGATOIRES — tous verts (sorties réelles, R1)

### Test 1 — décalage temporel
- `test_signal_at_t_captures_only_next_period` : un saut de +50 % entre open[5]
  et open[6] n'est PAS capté par un signal posé en t=4 (equity finale = 1.0
  exactement) et EST capté par un signal posé en t=3 (equity = 1.5). ✅
- `test_future_data_change_does_not_affect_past_equity` : réécrire les prix à
  partir de t=30 laisse l'equity 0..29 strictement identique. ✅

### Test 2 — random walk (40 seeds × 1500 bougies, sans dérive ni structure)
- Stratégie honnête (EMA 10/30) avant frais : |moyenne des log-rendements| < 3
  erreurs types → **≈ 0 sur du bruit pur**. ✅
- Après frais (0,10 % + 5 bps) : moyenne **négative**. ✅
- **Canari** : une stratégie qui triche volontairement (utilise open[t+2]/open[t+1])
  explose la borne → le test détecte bien un vrai lookahead. ✅

### Test 3 — validation croisée avec backtesting.py 0.6.5
EMA 20/50, BTC/USDT 1d réel 2019-2024, frais 0,1 %, exécution open t+1 :
```
moteur maison : equity finale = 22.8690
backtesting.py: equity finale = 23.0626
écart relatif = 0.840%   (tolérance 2 %)
```
Écart expliqué : backtesting.py trade en parts entières (atténué par un rescaling
×10⁻⁶ des prix) et gère un résidu de cash, notre moteur est purement fractionnaire.

### Mini-cas 10 bougies vérifié à la main
`test_hand_verified_ten_candles` : equity finale attendue calculée à la main
(0,99 × 105/101 × 110/105 × 0,99 × 0,995 × … ) reproduite à 1e-12 près ; turnover
total = 3,0 ; 2 épisodes de trade ; coûts cumulés = 3 %. ✅

## Suite complète

```
$ make test
51 passed, 1 warning in 2.74s
$ ruff check src/ tests/ scripts/
All checks passed!
```

## Critères d'acceptation

| Critère | Statut |
|---|---|
| Test unitaire de décalage | ✅ |
| Test random walk (≈0 avant frais, <0 après) | ✅ + canari |
| Validation croisée librairie de référence | ✅ (écart 0,84 % expliqué) |
| Métriques vérifiées à la main sur 10 bougies | ✅ (précision 1e-12) |
