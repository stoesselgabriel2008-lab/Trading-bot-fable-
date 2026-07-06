# GO LIVE CHECKLIST — document préparatoire (PAS une activation)

> **État au 2026-07-06 : le passage en live est INTERDIT et impossible.**
> (1) `live_trading: false` ; (2) le code lève PermissionError même si ce flag
> passait à true (testé) ; (3) **aucune stratégie n'a survécu à la validation
> anti-illusion** (VALIDATION_REPORT.md : 0/38) — il n'y a RIEN à passer en live.
> Ce document liste les conditions qui devraient TOUTES être réunies un jour.

## Conditions préalables strictes

- [ ] **Une stratégie VALIDÉE existe** : elle a passé les 8 critères du protocole
      (docs/reports/PHASE_6.md) sans modification post-hoc, test final compris.
- [ ] **2 à 4 semaines minimum de paper trading concluant** avec cette stratégie :
      implementation shortfall dans la tolérance (rapports quotidiens à l'appui).
- [ ] Compte exchange **au nom de l'utilisateur**, vérifié (KYC), chez un CASP
      agréé MiCA (Bybit EU : FMA Autriche — vérifier que c'est toujours le cas).
- [ ] Clés API **trade-only** (withdrawal DÉSACTIVÉ), **whitelist IP** activée,
      compte DÉDIÉ au bot, rotation des clés planifiée (trimestrielle).
- [ ] **Capital minime et dédié**, dont la perte TOTALE est acceptable et acceptée.
- [ ] `config/risk.yaml` relu ligne à ligne et signé des deux yeux : taille max
      d'ordre, position max, exposition max, perte journalière max, drawdown max,
      levier interdit.
- [ ] Circuit breakers testés en testnet (déclenchements volontaires, comme fait
      en paper dans PHASE_7.md/PHASE_9.md).
- [ ] Kill switch testé depuis la machine de production.
- [ ] Monitoring actif : rapports quotidiens lus, alertes webhook configurées.
- [ ] Fiscalité comprise (France : flat tax 31,4 % en 2026, formulaire 3916-bis
      pour les comptes étrangers — RESEARCH.md §9 ; **pas un conseil fiscal**).
- [ ] Déclaration écrite de l'utilisateur : « je comprends que la perte totale du
      capital engagé est possible et qu'aucun rendement n'est garanti ».
- [ ] Confirmation explicite, en toutes lettres, donnée à l'opérateur du bot —
      le bot lui-même ne peut PAS s'activer en live (verrou logiciel volontaire).

## Ce que le live exigerait techniquement (non implémenté volontairement)

Déverrouiller `CcxtBroker` (retrait de la PermissionError), passer `mode: live`,
`live_trading: true`, fournir des clés réelles. Ces étapes sont documentées pour
la transparence — PAS pour encourager le passage en live.
