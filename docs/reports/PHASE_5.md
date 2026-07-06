# Rapport de Phase 5 — Stratégies

**Date :** 2026-07-06 · **Statut : ✅**

## Livré

- `src/strategies/indicators.py` : EMA, SMA, RSI (Wilder), ATR (Wilder), canaux de
  Donchian (décalés de 1 — la bougie courante n'entre jamais dans le canal),
  z-score, volatilité réalisée — pandas pur, strictement causaux.
- `src/strategies/families.py` — **7 familles** (exigence : ≥ 6), chacune avec
  espace de paramètres documenté + 3 presets (conservative/balanced/aggressive) :
  1. `ema_cross` — trend following EMA + filtre de tendance SMA
  2. `donchian` — breakout de canal (Turtle), sortie canal court
  3. `mean_reversion` — RSI + z-score, **time-stop obligatoire** (RESEARCH §3)
  4. `atr_breakout` — breakout de volatilité, trailing stop k×ATR
  5. `momentum_xs` — momentum cross-sectional top-k avec filtre absolu (mom > 0)
  6. `dca_conditional` — exposition proportionnelle à la décote vs SMA longue
  7. `grid_range` — grille bornée autour d'une SMA, **stop global sous le range**
  8. `vol_target_overlay` — overlay de volatility targeting (min(1, cible/réalisée),
     jamais de levier) applicable à toute stratégie sous-jacente
- `src/strategies/baselines.py` — **2 baselines juges de paix** :
  - `buy_hold` (étalon passif)
  - `random_timing` : P(switch) = 1/hold_bars, calibrable sur le turnover de la
    stratégie comparée, seedé et reproductible (protocole RESEARCH §4)

## Tests (sorties réelles, R1)

- 12 tests sur **séries construites à la main** où le résultat attendu est connu
  (breakout Donchian entre/sort aux bonnes bougies, mean reversion entre sur le
  crash et sort sur récupération OU time-stop, grid s'arrête sous le range,
  momentum ne sélectionne que le gagnant si positif, DCA à 0,5 au prix moyen…).
- 2 tests **génériques paramétrés sur les 10 stratégies** :
  - poids ∈ [0,1], aucun NaN, colonnes complètes ;
  - **causalité** : réécriture massive du futur (t ≥ 300) → poids passés
    strictement identiques (contrat anti-lookahead de l'interface).

```
$ make test
82 passed, 1 warning in 3.18s
```

## Critères d'acceptation

| Critère | Statut |
|---|---|
| ≥ 6 familles via interface commune | ✅ 7 familles + 1 overlay |
| Espace de paramètres + 3 presets chacune | ✅ |
| Baselines buy & hold + aléatoire calibrée | ✅ |
| Tests unitaires sur séries manuelles | ✅ (attendus vérifiés à la main) |

## Note honnête

La famille « carry funding » identifiée en Phase 1 n'est PAS implémentée :
périmètre spot + Bybit EU sans futures pour les particuliers UE (ADR-002).
Documenté comme limite, pas comme oubli.
