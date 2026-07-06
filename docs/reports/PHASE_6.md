# Rapport de Phase 6 — Validation anti-illusion

**Date :** 2026-07-06 · **Statut : ✅ (protocole exécuté intégralement — verdicts honnêtes)**

## Verdict global

**0 couple validé / 38 testés** (19 familles brutes × actifs + 19 refontes `_VT`).
La liste complète des rejets et leurs raisons : `docs/VALIDATION_REPORT.md`.
Rappel de la mission : ce résultat est un SUCCÈS du protocole, pas un échec du
projet — l'ennemi n°1 est l'illusion de performance.

## Protocole appliqué (ordre imposé, à chaque couple)

1. Découpage 70/15/15 — test final réservé, jamais utilisé pour ajuster.
2. Walk-forward rolling (IS 730 j / OOS 182 j) — métriques uniquement OOS.
3. Sensibilité ±15/±30 % autour de l'optimum (médiane des voisins ≥ 50 % du Sharpe).
4. Monte Carlo : bootstrap 2 000 tirages des trades OOS, IC 95 %, DD p95.
5. DSR (Bailey & López de Prado) avec **comptage honnête : ~5 200 configurations
   au total** — P(hasard) rapportée pour chaque couple.
6. Régimes bull/bear/range (SMA 200 + drawdown > 20 %).
7. Stress des coûts : frais ×1,5, slippage ×2 — critères évalués SOUS stress.
8. 8 critères de survie (C1..C8, mission §9.8).
9. Verdict + refonte unique R3 (passe 2 `_VT`) → rejets définitifs.

## Preuves d'exécution (sorties réelles, R1)

```
$ make validate
VERDICTS : 0 validées / 38 rejetées   (104 s)
rapport écrit : docs/VALIDATION_REPORT.md
```

Extraits de la synthèse (coûts stressés) :

| Couple | Ret. OOS | Sharpe | Max DD | Fen.+ | Pctl vs aléa | P(hasard) | Verdict |
|---|---|---|---|---|---|---|---|
| DonchianBreakout × BTC | +296,9 % | 1,01 | −60,4 % | 62 % | 67 | 99 % | REJETÉE (C2..C6) |
| CrossSectionalMomentum × PORTFOLIO | +791,0 % | 1,18 | −61,2 % | 62 % | 42 | 95 % | REJETÉE |
| DonchianBreakout_VT × SOL | +42,6 % | 1,08 | −15,6 % | 75 % | 46 | 98 % | REJETÉE (C6) |
| AtrBreakout_VT × ETH | +130,7 % | 1,12 | −17,2 % | 75 % | 68 | 81 % | REJETÉE (C6…) |
| GridRange × BTC | −44,6 % | −0,36 | −58,3 % | 38 % | 18 | 100 % | REJETÉE (presque tout) |

## Enseignements

1. **La refonte vol-target a fonctionné là où la recherche le prédisait** :
   drawdowns divisés par 2-3 (C3 passait alors presque partout) — mais elle ne
   crée pas d'edge : C6 (battre l'aléatoire calibré) reste infranchi.
2. **Le critère C6 est le vrai juge de paix** : des rendements OOS spectaculaires
   (+791 %) ne se distinguent pas d'une baseline aléatoire dans un marché
   structurellement haussier — exactement l'illusion que le protocole doit tuer.
3. Le DSR avec comptage honnête est impitoyable : tester ~165 configurations par
   couple suffit à rendre presque n'importe quel « bon » Sharpe compatible avec
   du hasard de sélection.

## Conséquences (ADR-004)

- Aucune stratégie éligible au trading ; le paper trading Phase 7 valide
  l'INFRASTRUCTURE avec `DonchianBreakout_VT` étiquetée « NON VALIDÉE —
  observation uniquement ».
- L'itération de refonte R3 est CONSOMMÉE : plus aucun ajustement autorisé.

## Critères d'acceptation de la phase

| Exigence mission | Statut |
|---|---|
| Protocole 9 étapes appliqué à chaque couple | ✅ (38 couples) |
| VALIDATION_REPORT.md avec rejets détaillés | ✅ |
| Comptage honnête des configurations + DSR | ✅ (~5 200, P(hasard) par couple) |
| Une seule itération de refonte (R3) | ✅ (passe `_VT`, définitive) |
| Test final touché une seule fois | ✅ (jamais atteint : aucun survivant) |
