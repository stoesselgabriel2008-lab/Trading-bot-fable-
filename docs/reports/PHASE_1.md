# Rapport de Phase 1 — Recherche web massive

**Date :** 2026-07-06 · **Statut : ✅ critères d'acceptation atteints**

## Volume (exigence : ≥ 50 WebSearch, ≥ 25 pages lues intégralement)

- **52 requêtes WebSearch distinctes** couvrant les 9 sujets obligatoires dans l'ordre.
- **26 pages lues intégralement** : 24 via WebFetch + 2 PDF académiques téléchargés puis
  lus par extraction locale (arxiv 2009.12155 « A Decade of Evidence of Trend Following
  in Cryptocurrencies » ; BIS Working Paper n°1087 « Crypto carry »).
- Tout est consigné dans `docs/RESEARCH.md` avec URL + date + points de désaccord.

## Découverte majeure

**Binance a cessé de servir l'UE (dont la France) au 1er juillet 2026**, faute de licence
MiCA — recoupé par CoinDesk (26/06/2026) et Euronews (25/06/2026). L'utilisateur étant en
France, l'exchange principal ne peut pas être Binance.

## Décisions issues de la recherche

| ADR | Décision |
|---|---|
| **ADR-002** | Exchange principal : **Bybit** (licence MiCA FMA Autriche valable en France, vérifiée sur casptracker.eu le 06/07/2026 + testnet complet + Demo Trading mainnet `api-demo.bybit.com`). Données historiques de backtest : **API publique Binance** (sans clé, historique 2017+). |
| **ADR-003** | **Construction sur mesure** autour de ccxt (MIT) ; backtesting.py 0.6.5 comme moteur de référence pour la validation croisée ; Freqtrade/Nautilus/vectorbt écartés avec justifications. |

## Enseignements structurants pour les phases suivantes

1. **Anti-lookahead** : test de décalage + test random-walk + validation croisée (Phase 4) ;
   exécution t+1 stricte ; bougie courante toujours rejetée.
2. **DSR** : formule complète de Bailey & López de Prado vérifiée (2 sources) — implémentée
   en Phase 6 avec comptage exhaustif des essais.
3. **Coûts** : 0,10 % taker (Bybit et Binance, 2 sources chacun) + slippage 5 bps (BTC/ETH,
   fourchette documentée 0,05-0,1 %) ; stress ×1,5/×2 obligatoire.
4. **Corrélation BTC-altcoins 0,70-0,90** → la limite d'exposition portefeuille prime sur
   les limites par actif ; quantification sur nos données en Phase 3.
5. **Robustesse** : réconciliation 3 états (exchange/mémoire/SQLite) + Safe Mode ;
   écritures atomiques ; monitoring de santé économique et pas seulement technique ;
   clientOrderId idempotents.
6. **Famille carry funding documentée mais exclue** (pas de futures Bybit EU pour les
   particuliers UE ; périmètre spot).
7. **Fiscal (informatif, pas un conseil)** : flat tax 31,4 % en 2026, crypto-crypto non
   imposable, formulaires 2086/3916-bis.

## Critères d'acceptation

| Critère | Statut |
|---|---|
| RESEARCH.md complet, sources datées | ✅ (9 sections, compteur final inclus) |
| Matrice de décision frameworks | ✅ (RESEARCH.md §1 + ADR-003) |
| Choix exchange justifié en ADR | ✅ (ADR-002 avec matrice) |
| Choix stack justifié en ADR | ✅ (ADR-001 + ADR-003) |

## Erreurs typiques évitées

- Frais pris d'une seule source → chaque frais recoupé par 2 sources.
- Confusion testnet Bybit vs Demo Trading mainnet → distinction documentée (clé testnet
  inutilisable sur demo et vice-versa).
- Chiffres marketing (DCA « 6 712 % », trend following « 255 %/an ») pris pour argent
  comptant → signalés comme suspects, soumis à NOTRE validation Phase 6.
