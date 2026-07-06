# ADR-004 — Périmètre de validation et conséquences du verdict « 0 validée »

**Date :** 2026-07-06 · **Statut :** accepté

## Périmètre retenu pour la Phase 6

- **Timeframe : 1d uniquement** (3 245 bougies BTC/ETH ≈ 9 ans, 2 155 SOL).
  Les données 1h/4h sont téléchargées et disponibles, mais multiplier les
  timeframes multiplie les configurations testées (et donc dégrade le DSR de
  chaque couple) sans historique supplémentaire. Extension possible ultérieure.
- Walk-forward : IS 730 bougies (~2 ans) / OOS 182 (~6 mois), rolling.
- Grilles volontairement petites (presets + variations univariées ±30 %) :
  2 595 configurations comptées en passe 1, ~5 200 au total avec la refonte.

## Refonte unique (R3)

Mode d'échec dominant de la passe 1 : **drawdown OOS > 30 %** (12 rejets sur 19)
avec des Sharpe parfois corrects. Refonte choisie : overlay de **volatility
targeting** à paramètres FIXES (25 % annualisé, fenêtre 30) appliqué uniformément
aux 7 familles — pré-enregistré dès la Phase 1 (RESEARCH §3/§5), donc pas de
torture de données. Résultat : drawdowns massivement réduits (ex. Donchian ETH
−49 % → −18 %) mais **aucun couple ne franchit C6** (battre significativement la
baseline aléatoire calibrée, percentile ≥ 90) ni ne réduit assez P(hasard).

## Décision

1. **Aucune stratégie n'est validée pour un trading (même paper) présenté comme
   « stratégie qui marche ».** Le VALIDATION_REPORT liste les 38 rejets et leurs
   raisons — c'est le livrable central et un résultat de mission VALIDE.
2. **Le paper trading de Phase 7 sert à valider l'infrastructure** (exécution,
   risk manager, breakers, persistance, kill switch, shortfall) : il tournera
   avec la meilleure candidate rejetée (`DonchianBreakout_VT`, preset balanced)
   étiquetée en clair « NON VALIDÉE — observation uniquement » dans la config,
   les logs et les rapports. Aucun capital réel n'est en jeu en mode paper.
3. Le passage en live reste verrouillé (R6) et n'aurait de toute façon AUCUNE
   stratégie éligible aujourd'hui — précisé dans GO_LIVE_CHECKLIST.md.

## Pistes futures honnêtes (sans promesse)

- Étendre l'univers d'actifs (10-20 cryptos liquides) pour donner du grain au
  momentum cross-sectional ; ré-évaluer alors C6 sur un vrai portefeuille.
- Tester le timeframe 4h pour les familles à time-stop court.
- Allonger l'OOS (fenêtres de 12 mois) pour réduire la variance des verdicts.
