# Rapport de Phase 2 — Architecture

**Date :** 2026-07-06 · **Statut : ✅**

## Livré

- `docs/ARCHITECTURE.md` : schéma mermaid complet (Data → Strategies → Backtest →
  Validation → Risk → Execution → Monitoring), 6 principes non négociables (poids cibles,
  limites côté exécuteur, anti-lookahead par construction, multi-actifs natif, config
  immuable, paper d'abord), contrats d'interface (Strategy, BacktestEngine, RiskManager,
  Executor), flux de données, persistance.
- Interface `Strategy` implémentée (`src/strategies/base.py`) : classe abstraite,
  `generate_targets(data) -> DataFrame de poids ∈ [0,1]`, espace de paramètres +
  mécanisme de presets (conservateur/équilibré/agressif) testé.
- 20 squelettes de modules avec docstrings (data, backtest, validation×6, risk×2,
  execution×4, monitoring×3).

## Preuves d'exécution (R1)

```
$ make test
...............................                                          [100%]
31 passed in 0.48s
$ ruff check src/ tests/
All checks passed!
```

## Critères d'acceptation

| Critère | Statut |
|---|---|
| ARCHITECTURE.md relu et cohérent | ✅ |
| Squelettes de modules + docstrings | ✅ (23 modules importables) |
| Tests d'import verts | ✅ (31 tests dont 23 imports paramétrés) |

## Choix notables

- Le contrat « matrice de poids cibles » unifie mono-actif et cross-sectional : le moteur
  et le risk manager n'ont qu'un seul format d'entrée — décision clé pour éviter un
  refactoring multi-actifs plus tard.
- Même chemin de code signaux backtest/live (réduit le risque d'implementation shortfall).
