# ADR-001 — Stack technique initiale

**Date :** 2026-07-06 · **Statut :** accepté

## Contexte

Le projet exige des versions pinnées et vérifiées (règle R5 : la mémoire
d'entraînement peut être obsolète). Toutes les versions ci-dessous ont été
vérifiées **en direct sur PyPI** le 2026-07-06 via `pip index versions`
(sortie brute dans `docs/reports/PHASE_0.md`).

## Décisions

| Composant | Choix | Justification |
|---|---|---|
| Python | 3.12 (3.11.15/3.12/3.13 disponibles) | 3.12 : mûr, supporté par tout l'écosystème ; 3.13 encore évité par prudence pour les deps compilées |
| Connectivité | ccxt 4.5.64 | Standard de fait multi-exchange, testnets supportés — confirmé en Phase 1 |
| DataFrames | pandas **2.3.3** (pas 3.0.3) | pandas 3.0 est sorti mais très récent (copy-on-write par défaut, dtypes string) ; backtesting.py/vectorbt non garantis compatibles. On reste sur la dernière 2.x mature. |
| Numérique | numpy 2.3.5 | Compatible pandas 2.3.x ; 2.4.6 existe mais 2.3.5 est la version testée avec pandas 2.3.3 |
| Stockage | pyarrow 24.0.0 (parquet) | Format colonne compact, rapide, portable |
| Config | pydantic 2.13.4 + PyYAML 6.0.3 | Validation stricte + modèles immuables (R10) |
| Scheduler | APScheduler 3.11.3 | Branche 3.x stable (la 4.x est en pré-release depuis longtemps) |
| Backtest de référence | backtesting.py 0.6.5 | Léger, peu de contraintes de deps ; sert UNIQUEMENT à la validation croisée du moteur maison (Phase 4). vectorbt 1.1.0 noté en alternative si besoin. |
| Tests | pytest 9.1.1 + pytest-cov 7.1.0 | Standard |
| Qualité | ruff 0.15.20, mypy 2.1.0, pip-audit 2.10.1 | Lint+format unifiés, typage des modules cœur, audit deps |

## Conséquences

- Le moteur de backtest est développé **sur mesure** (contrôle total de la
  modélisation des coûts et de l'anti-lookahead) — décision confirmée ou
  infirmée par la recherche Phase 1 (ADR-003 framework).
- Toute montée de version passe par une mise à jour de cet ADR.
