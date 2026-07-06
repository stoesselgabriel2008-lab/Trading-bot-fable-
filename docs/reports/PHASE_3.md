# Rapport de Phase 3 — Pipeline de données

**Date :** 2026-07-06 · **Statut : ✅**

## Livré

- `src/data/fetcher.py` : fetch OHLCV paginé multi-sources (binance_public / bybit),
  retries backoff (2/4/8/16 s), **rejet systématique de la bougie non clôturée**.
- `src/data/storage.py` : parquet, écritures **atomiques** (tmp+rename), mise à jour
  incrémentale **idempotente** (reprise 3 bougies avant la dernière connue).
- `src/data/quality.py` : gaps, doublons, cohérence OHLC, volume nul, mouvements
  extrêmes, matrice de corrélation ; **aucune interpolation silencieuse**.
- `scripts/fetch_data.py` (= `make fetch-data`) : tous actifs × timeframes + rapport
  auto `docs/reports/DATA_QUALITY.md` ; code retour ≠ 0 si anomalie bloquante.
- 11 tests unitaires du pipeline (sans réseau, données synthétiques).

## Preuves d'exécution (R1)

### `make fetch-data` (2 exécutions — la 2e prouve l'idempotence)
```
dataset binance_public BTC/USDT 1h : 77763 bougies au total
dataset binance_public ETH/USDT 1d : 3245 bougies au total
fetch SOL/USDT 1h : 4 bougies (2026-07-06 11:00 -> 14:00)   <- 2e run : incrémental
rapport qualité écrit : docs/reports/DATA_QUALITY.md
```

### Synthèse qualité (extrait du rapport généré)
| Actif | TF | Bougies | Période | Doublons | Gaps | OHLC KO |
|---|---|---|---|---|---|---|
| BTC/USDT | 1h | 77 763 | 2017-08-17 → 2026-07-06 | 0 | 28 | 0 |
| BTC/USDT | 1d | 3 245 | 2017-08-17 → 2026-07-05 | 0 | 0 | 0 |
| ETH/USDT | 1h | 77 763 | 2017-08-17 → 2026-07-06 | 0 | 28 | 0 |
| SOL/USDT | 1d | 2 155 | 2020-08-11 → 2026-07-05 | 0 | 0 | 0 |

≈ **9 ans** d'historique BTC/ETH (objectif 5-7 ans dépassé), SOL depuis son listing.
Gaps horaires = maintenances exchange historiques (documentés, conservés tels quels).

### Corrélation des rendements journaliers (sortie réelle)
```
          BTC/USDT  ETH/USDT  SOL/USDT
BTC/USDT     1.000     0.805     0.571
ETH/USDT     0.805     1.000     0.637
SOL/USDT     0.571     0.637     1.000
```
→ Confirme l'« illusion de diversification » (RESEARCH.md §5) : la limite d'exposition
totale du portefeuille (0,60) est la contrainte pertinente.

### `make test`
```
42 passed in 1.03s
```

## Contraintes d'environnement découvertes (documentées, ADR-002 addendum)

1. ccxt ignore par défaut proxy/CA de l'environnement → instances créées avec
   `trust_env`/`requests_trust_env` (no-op hors proxy ; TLS jamais désactivé).
2. Binance **futures** (fapi) géo-bloqué (451) depuis l'environnement → marchés
   restreints au spot (`fetchMarkets: ['spot']`) — sans impact (périmètre spot).
3. **Bybit géo-bloqué (CloudFront 403) depuis l'IP de sortie cloud (US)** : Bybit
   bloque les États-Unis. Sans impact sur la mission (backtest + paper sur données
   Binance publiques) ; l'utilisateur en France accède normalement à Bybit EU —
   précisé dans le RUNBOOK pour le déploiement.

## Critères d'acceptation

| Critère | Statut |
|---|---|
| `make fetch-data` reproductible | ✅ (2 runs, incrémental prouvé) |
| Rapports de qualité générés | ✅ DATA_QUALITY.md par actif/TF |
| Tests unitaires du pipeline verts | ✅ 42 passed |
