# ADR-002 — Choix de l'exchange principal et des sources de données

**Date :** 2026-07-06 · **Statut :** accepté · **Contexte complet :** docs/RESEARCH.md §2

## Contexte

Critère n°1 imposé par la mission : **qualité du testnet**. Contrainte découverte en
Phase 1 : **Binance a cessé de servir l'UE (dont la France) au 01/07/2026** faute de
licence MiCA (CoinDesk 26/06/2026, Euronews 25/06/2026). L'utilisateur est en France.

## Matrice de décision

| Critère | Binance | **Bybit** | OKX | Kraken | Coinbase |
|---|---|---|---|---|---|
| Testnet/démo spot | ✅ excellent | ✅✅ testnet + **demo mainnet** (données réelles) | ✅ header simulé | ❌ futures seulement | ❌ mock |
| Licence MiCA (France) | ❌ | ✅ (FMA Autriche, 28/05/2025) | ✅ (Malte) | ✅ (Irlande) | ✅ (Luxembourg) |
| Support ccxt | certifié | certifié | certifié | oui | oui |
| Frais spot base | 0,10/0,10 % | 0,10/0,10 % | ~0,08/0,10 % | plus élevés | plus élevés |
| Historique kline public | ~2017 (le plus profond) | à mesurer (spot lancé ~2021) | moyen | moyen | moyen |

## Décision

1. **Exchange principal (exécution testnet/demo, et éventuel live futur) : Bybit.**
   Seul exchange cumulant licence MiCA couvrant la France ET double environnement de
   test (testnet complet + Demo Trading sur mainnet `api-demo.bybit.com` avec données
   de marché réelles — idéal pour le paper/testnet validation). Rate limits documentés
   (600 req/5 s/IP ; 10-20 ordres/s ; headers X-Bapi-Limit-*).
2. **Données historiques de backtest : API publique Binance** (`data-api.binance.vision`,
   sans compte ni clé — l'arrêt des services clients UE n'affecte pas l'accès aux données
   publiques de marché), car c'est l'historique spot le plus profond (2017+). Cohérence
   contrôlée par échantillon contre les klines Bybit en Phase 3.
3. **Mode `paper` (défaut)** : simulation locale sur données publiques live Bybit.

## Conséquences

- `config/exchange.yaml` : `id: bybit`, données historiques : source `binance_public`.
- Le module data supporte plusieurs sources dès la conception.
- Si Bybit EU restreignait davantage : bascule OKX (alternative documentée).
- Risque assumé : divergences mineures de prix Binance (historique) vs Bybit (exécution)
  — mesurées en Phase 3, intégrées au stress des coûts si significatives.
