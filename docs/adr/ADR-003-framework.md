# ADR-003 — Sur-mesure vs framework existant

**Date :** 2026-07-06 · **Statut :** accepté · **Contexte complet :** docs/RESEARCH.md §1

## Options considérées

1. **Freqtrade** (GPL-3.0, ~49k ⭐) : bot directionnel complet et mûr. Mais : (a) le cœur
   de CETTE mission est le protocole de validation anti-illusion (DSR, random-walk test,
   comptage des essais), non fourni par Freqtrade ; (b) moteur de backtest = boîte
   moyennement transparente pour prouver l'absence de lookahead « by construction » ;
   (c) GPL-3.0 contraignante ; (d) courbe de configuration élevée pour un contrôle partiel.
2. **Nautilus Trader** : production-grade (Rust), mais complexité disproportionnée.
3. **vectorbt libre** : en maintenance seule, features réservées au PRO payant.
4. **backtrader** : non maintenu depuis ~2018 — éliminé.
5. **Sur mesure + ccxt (MIT) + backtesting.py comme référence** ✅

## Décision

**Construire sur mesure**, en réutilisant :
- **ccxt 4.5.64** (MIT, ~105 exchanges, rate limiter, sandbox mode) pour TOUTE la connectivité ;
- **backtesting.py 0.6.5** uniquement comme moteur de référence pour la validation croisée
  du moteur maison (Phase 4, test n°3) ;
- pandas/pyarrow pour les données.

## Justification

- Le protocole de validation (Phase 6) est la valeur du projet : il exige un moteur dont
  chaque ligne est auditable et testable (anti-lookahead prouvé par tests, pas par confiance).
- La modélisation des coûts (frais réels sourcés, slippage stressable, exécution t+1)
  doit être exactement celle spécifiée par la mission.
- Les limites de risque doivent vivre dans la couche d'exécution (R8) — architecture
  imposée difficile à garantir en surcouche d'un framework existant.

## Conséquences

- Plus de code à écrire et à tester (assumé : pytest ≥ 80 % en Phase 9).
- Pas de communauté pour déboguer le moteur → compensé par la validation croisée
  systématique contre backtesting.py et les tests sur cas construits à la main.
