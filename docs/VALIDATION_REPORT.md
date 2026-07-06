# VALIDATION REPORT — verdicts par couple stratégie × actif

Protocole complet (docs/reports/PHASE_6.md) exécuté en 104s.
**0 couple(s) VALIDÉ(S) / 38 testés — 38 rejetés.** Rappel : il est statistiquement NORMAL que la
majorité échoue ; le dire est la preuve que le protocole fonctionne.

Configurations testées au total (comptage honnête, tous couples) : **5192**.
Coûts stressés appliqués partout pour les critères : frais ×1,5, slippage ×2.

Deux passes : (1) les 7 familles brutes ; (2) suffixe `_VT` = **l'UNIQUE itération
de refonte autorisée par R3** (overlay volatility targeting 25 %/30 bougies, paramètres
fixes, motivée par la recherche Phase 1 et le mode d'échec dominant de la passe 1 —
drawdowns > 30 %). Les verdicts de la passe 2 sont DÉFINITIFS : aucune autre
itération n'est permise.

**Conclusion honnête : AUCUNE stratégie n'est validée pour le trading.** Les meilleures
candidates (DonchianBreakout_VT, AtrBreakout_VT sur ETH/SOL) affichent des Sharpe OOS
autour de 1 et des drawdowns < 20 %, mais ne se distinguent PAS significativement d'une
baseline aléatoire calibrée (C6) et leur probabilité d'être le fruit du hasard/de la
sélection reste ≥ 78 % (DSR). Le paper trading (Phase 7) servira à valider
l'INFRASTRUCTURE, avec une stratégie explicitement étiquetée « NON VALIDÉE — observation
uniquement » (cf. ADR-004).

## Synthèse

| Stratégie | Périmètre | Verdict | Ret. OOS stress | Sharpe OOS | Max DD | PF | Fen.+ | Pctl vs aléa | DSR | P(hasard) |
|---|---|---|---|---|---|---|---|---|---|---|
| EmaCross | BTC/USDT | **REJETÉE** | +196.5% | 0.82 | -62.4% | 3.86 | 62% | 76 | 0.01 | 99% |
| EmaCross | ETH/USDT | **REJETÉE** | +117.8% | 0.65 | -76.1% | 3.85 | 50% | 54 | 0.03 | 97% |
| EmaCross | SOL/USDT | **REJETÉE** | +128.1% | 0.94 | -53.4% | 2.18 | 25% | 62 | 0.09 | 91% |
| DonchianBreakout | BTC/USDT | **REJETÉE** | +296.9% | 1.01 | -60.4% | 3.69 | 62% | 67 | 0.01 | 99% |
| DonchianBreakout | ETH/USDT | **REJETÉE** | +319.2% | 0.91 | -49.3% | 3.56 | 62% | 92 | 0.04 | 96% |
| DonchianBreakout | SOL/USDT | **REJETÉE** | +189.6% | 1.12 | -45.3% | 2.93 | 50% | 29 | 0.09 | 91% |
| MeanReversion | BTC/USDT | **REJETÉE** | +40.2% | 0.50 | -20.7% | 3.49 | 38% | 34 | 0.02 | 98% |
| MeanReversion | ETH/USDT | **REJETÉE** | -21.2% | -0.10 | -44.3% | 0.75 | 25% | 70 | 0.00 | 100% |
| MeanReversion | SOL/USDT | **REJETÉE** | +40.8% | 0.69 | -28.5% | 4.73 | 50% | 95 | 0.31 | 69% |
| AtrBreakout | BTC/USDT | **REJETÉE** | +81.5% | 0.59 | -59.1% | 2.57 | 50% | 64 | 0.02 | 98% |
| AtrBreakout | ETH/USDT | **REJETÉE** | +675.7% | 1.13 | -58.8% | 5.54 | 62% | 79 | 0.20 | 80% |
| AtrBreakout | SOL/USDT | **REJETÉE** | +112.2% | 0.91 | -50.5% | 2.81 | 25% | 45 | 0.04 | 96% |
| CrossSectionalMomentum | PORTFOLIO | **REJETÉE** | +791.0% | 1.18 | -61.2% | 3.97 | 62% | 42 | 0.05 | 95% |
| ConditionalDca | BTC/USDT | **REJETÉE** | +0.1% | 0.22 | -62.7% | 6.17 | 75% | 24 | 0.01 | 99% |
| ConditionalDca | ETH/USDT | **REJETÉE** | +75.3% | 0.53 | -65.2% | 11.85 | 88% | 60 | 0.01 | 99% |
| ConditionalDca | SOL/USDT | **REJETÉE** | +12.4% | 0.43 | -75.3% | 46.19 | 75% | 74 | 0.29 | 71% |
| GridRange | BTC/USDT | **REJETÉE** | -44.6% | -0.36 | -58.3% | 0.91 | 38% | 18 | 0.00 | 100% |
| GridRange | ETH/USDT | **REJETÉE** | -14.1% | 0.06 | -60.5% | 1.12 | 38% | 20 | 0.00 | 100% |
| GridRange | SOL/USDT | **REJETÉE** | +29.9% | 0.53 | -38.7% | 2.25 | 75% | 50 | 0.16 | 84% |
| EmaCross_VT | BTC/USDT | **REJETÉE** | +75.8% | 0.78 | -37.4% | 3.67 | 62% | 53 | 0.00 | 100% |
| EmaCross_VT | ETH/USDT | **REJETÉE** | +80.4% | 0.78 | -35.9% | 3.43 | 75% | 66 | 0.03 | 97% |
| EmaCross_VT | SOL/USDT | **REJETÉE** | +43.1% | 1.04 | -18.1% | 1.99 | 50% | 36 | 0.09 | 91% |
| DonchianBreakout_VT | BTC/USDT | **REJETÉE** | +88.0% | 0.89 | -35.3% | 3.45 | 50% | 52 | 0.00 | 100% |
| DonchianBreakout_VT | ETH/USDT | **REJETÉE** | +77.7% | 0.84 | -18.1% | 2.87 | 75% | 84 | 0.02 | 98% |
| DonchianBreakout_VT | SOL/USDT | **REJETÉE** | +42.6% | 1.08 | -15.6% | 2.28 | 75% | 46 | 0.02 | 98% |
| MeanReversion_VT | BTC/USDT | **REJETÉE** | +5.0% | 0.18 | -13.9% | 1.29 | 38% | 21 | 0.00 | 100% |
| MeanReversion_VT | ETH/USDT | **REJETÉE** | -7.3% | -0.32 | -14.9% | 0.37 | 25% | 58 | 0.00 | 100% |
| MeanReversion_VT | SOL/USDT | **REJETÉE** | +11.3% | 0.76 | -6.5% | 4.74 | 50% | 56 | 0.22 | 78% |
| AtrBreakout_VT | BTC/USDT | **REJETÉE** | +62.1% | 0.81 | -31.5% | 3.10 | 62% | 47 | 0.03 | 97% |
| AtrBreakout_VT | ETH/USDT | **REJETÉE** | +130.7% | 1.12 | -17.2% | 4.20 | 75% | 68 | 0.19 | 81% |
| AtrBreakout_VT | SOL/USDT | **REJETÉE** | +26.3% | 0.81 | -17.9% | 2.47 | 50% | 50 | 0.01 | 99% |
| CrossSectionalMomentum_VT | PORTFOLIO | **REJETÉE** | +108.6% | 0.99 | -29.4% | 3.49 | 62% | 25 | 0.01 | 99% |
| ConditionalDca_VT | BTC/USDT | **REJETÉE** | +13.4% | 0.27 | -33.0% | 8.01 | 75% | 22 | 0.01 | 99% |
| ConditionalDca_VT | ETH/USDT | **REJETÉE** | +30.6% | 0.54 | -27.5% | 4.30 | 75% | 59 | 0.00 | 100% |
| ConditionalDca_VT | SOL/USDT | **REJETÉE** | +14.0% | 0.47 | -26.5% | 56.27 | 75% | 57 | 0.27 | 73% |
| GridRange_VT | BTC/USDT | **REJETÉE** | -26.9% | -0.58 | -34.9% | 0.81 | 50% | 11 | 0.00 | 100% |
| GridRange_VT | ETH/USDT | **REJETÉE** | +18.5% | 0.46 | -14.4% | 1.44 | 62% | 55 | 0.00 | 100% |
| GridRange_VT | SOL/USDT | **REJETÉE** | +0.8% | 0.10 | -13.0% | 1.61 | 75% | 56 | 0.08 | 92% |

## Détail par couple

### EmaCross × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'fast': 10, 'slow': 30, 'trend_filter': 0}`
- Configurations testées pour ce couple : 165
- OOS stressé : rendement +196.5%, annualisé +31.3%, Sharpe 0.82, Sortino 0.87, Calmar 0.50, max DD -62.4% (850 bougies), PF 3.86, win rate 50%, 16 trades, expectancy +13.610%
- Fenêtres WF positives (stress) : 62% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.35, médiane des voisins 1.11 -> robuste
- Monte Carlo (2000 tirages, 16 trades) : rendement IC95 [-39.2%, +587.0%], DD p95 -76.8%, P(rendement<0) = 6%
- DSR : SR̂=0.0430, SR₀=0.1042, DSR=0.01 -> **probabilité que le résultat soit dû au hasard/sélection : 99%**
- Par régime (OOS stressé) : bull +675.4% (448 bougies), bear -61.8% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +90.7% ; percentile vs 200 baselines aléatoires calibrées : 76 ; Calmar 2.02 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### EmaCross × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'fast': 10, 'slow': 30, 'trend_filter': 0}`
- Configurations testées pour ce couple : 165
- OOS stressé : rendement +117.8%, annualisé +21.6%, Sharpe 0.65, Sortino 0.59, Calmar 0.28, max DD -76.1% (822 bougies), PF 3.85, win rate 44%, 16 trades, expectancy +19.852%
- Fenêtres WF positives (stress) : 50% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.97, médiane des voisins 1.03 -> robuste
- Monte Carlo (2000 tirages, 16 trades) : rendement IC95 [-29.2%, +743.2%], DD p95 -106.6%, P(rendement<0) = 4%
- DSR : SR̂=0.0339, SR₀=0.0834, DSR=0.03 -> **probabilité que le résultat soit dû au hasard/sélection : 97%**
- Par régime (OOS stressé) : bull +1664.3% (464 bougies), bear -87.7% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +5.2% ; percentile vs 200 baselines aléatoires calibrées : 54 ; Calmar 0.08 vs B&H 0.27
- Critères OK : C1_rendement_net_positif_stress, C4_profit_factor_min_1.15, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### EmaCross × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'fast': 10, 'slow': 30, 'trend_filter': 0}`
- Configurations testées pour ce couple : 93
- OOS stressé : rendement +128.1%, annualisé +51.2%, Sharpe 0.94, Sortino 1.28, Calmar 0.96, max DD -53.4% (284 bougies), PF 2.18, win rate 17%, 12 trades, expectancy +8.207%
- Fenêtres WF positives (stress) : 25% (4 fenêtres)
- Sensibilité : Sharpe optimal 1.54, médiane des voisins 1.44 -> robuste
- Monte Carlo (2000 tirages, 12 trades) : rendement IC95 [-120.5%, +440.5%], DD p95 -107.1%, P(rendement<0) = 32%
- DSR : SR̂=0.0494, SR₀=0.0986, DSR=0.09 -> **probabilité que le résultat soit dû au hasard/sélection : 91%**
- Par régime (OOS stressé) : bull +619.8% (189 bougies), bear -68.3% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +19.4% ; percentile vs 200 baselines aléatoires calibrées : 62 ; Calmar 0.54 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90

### DonchianBreakout × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'entry': 26, 'exit': 10}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement +296.9%, annualisé +41.3%, Sharpe 1.01, Sortino 1.07, Calmar 0.68, max DD -60.4% (881 bougies), PF 3.69, win rate 58%, 19 trades, expectancy +11.018%
- Fenêtres WF positives (stress) : 62% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.24, médiane des voisins 1.18 -> robuste
- Monte Carlo (2000 tirages, 19 trades) : rendement IC95 [-20.7%, +580.3%], DD p95 -73.0%, P(rendement<0) = 6%
- DSR : SR̂=0.0528, SR₀=0.1174, DSR=0.01 -> **probabilité que le résultat soit dû au hasard/sélection : 99%**
- Par régime (OOS stressé) : bull +580.3% (448 bougies), bear -41.7% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +81.7% ; percentile vs 200 baselines aléatoires calibrées : 67 ; Calmar 1.65 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### DonchianBreakout × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'entry': 10, 'exit': 5}`
- Configurations testées pour ce couple : 123
- OOS stressé : rendement +319.2%, annualisé +43.2%, Sharpe 0.91, Sortino 0.85, Calmar 0.88, max DD -49.3% (822 bougies), PF 3.56, win rate 50%, 26 trades, expectancy +10.753%
- Fenêtres WF positives (stress) : 62% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.94, médiane des voisins 0.93 -> robuste
- Monte Carlo (2000 tirages, 26 trades) : rendement IC95 [+57.3%, +519.6%], DD p95 -72.5%, P(rendement<0) = 0%
- DSR : SR̂=0.0474, SR₀=0.0928, DSR=0.04 -> **probabilité que le résultat soit dû au hasard/sélection : 96%**
- Par régime (OOS stressé) : bull +746.9% (464 bougies), bear -50.5% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +60.7% ; percentile vs 200 baselines aléatoires calibrées : 92 ; Calmar 1.64 vs B&H 0.27
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct

### DonchianBreakout × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'entry': 26, 'exit': 10}`
- Configurations testées pour ce couple : 71
- OOS stressé : rendement +189.6%, annualisé +70.4%, Sharpe 1.12, Sortino 1.29, Calmar 1.55, max DD -45.3% (274 bougies), PF 2.93, win rate 50%, 10 trades, expectancy +16.237%
- Fenêtres WF positives (stress) : 50% (4 fenêtres)
- Sensibilité : Sharpe optimal 1.80, médiane des voisins 1.77 -> robuste
- Monte Carlo (2000 tirages, 10 trades) : rendement IC95 [-81.0%, +496.9%], DD p95 -100.6%, P(rendement<0) = 13%
- DSR : SR̂=0.0587, SR₀=0.1045, DSR=0.09 -> **probabilité que le résultat soit dû au hasard/sélection : 91%**
- Par régime (OOS stressé) : bull +495.0% (189 bougies), bear -51.3% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : -13.8% ; percentile vs 200 baselines aléatoires calibrées : 29 ; Calmar -0.37 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### MeanReversion × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'rsi_entry': 30, 'rsi_period': 14, 'time_stop': 7, 'z_entry': -2.0, 'z_window': 20}`
- Configurations testées pour ce couple : 241
- OOS stressé : rendement +40.2%, annualisé +8.8%, Sharpe 0.50, Sortino 0.18, Calmar 0.43, max DD -20.7% (1240 bougies), PF 3.49, win rate 57%, 7 trades, expectancy +6.335%
- Fenêtres WF positives (stress) : 38% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.48, médiane des voisins 0.44 -> robuste
- DSR : SR̂=0.0262, SR₀=0.0796, DSR=0.02 -> **probabilité que le résultat soit dû au hasard/sélection : 98%**
- Par régime (OOS stressé) : bull +0.0% (448 bougies), bear +40.2% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +20.0% ; percentile vs 200 baselines aléatoires calibrées : 34 ; Calmar 1.62 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### MeanReversion × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'rsi_entry': 25, 'rsi_period': 14, 'time_stop': 8, 'z_entry': -2.5, 'z_window': 20}`
- Configurations testées pour ce couple : 241
- OOS stressé : rendement -21.2%, annualisé -5.8%, Sharpe -0.10, Sortino -0.03, Calmar -0.13, max DD -44.3% (781 bougies), PF 0.75, win rate 43%, 7 trades, expectancy -1.677%
- Fenêtres WF positives (stress) : 25% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.10, médiane des voisins 0.04 -> îlot étroit (REJET)
- DSR : SR̂=-0.0052, SR₀=0.0811, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +0.0% (464 bougies), bear -21.2% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +11.1% ; percentile vs 200 baselines aléatoires calibrées : 70 ; Calmar 1.71 vs B&H 0.27
- Critères OK : C7_calmar_competitif_vs_bh
- Critères ÉCHOUÉS : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C8_robustesse_parametres

### MeanReversion × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'rsi_entry': 30, 'rsi_period': 10, 'time_stop': 10, 'z_entry': -2.0, 'z_window': 20}`
- Configurations testées pour ce couple : 137
- OOS stressé : rendement +40.8%, annualisé +18.7%, Sharpe 0.69, Sortino 0.33, Calmar 0.66, max DD -28.5% (512 bougies), PF 4.73, win rate 60%, 5 trades, expectancy +8.954%
- Fenêtres WF positives (stress) : 50% (4 fenêtres)
- Sensibilité : Sharpe optimal 0.91, médiane des voisins 0.78 -> robuste
- DSR : SR̂=0.0362, SR₀=0.0523, DSR=0.31 -> **probabilité que le résultat soit dû au hasard/sélection : 69%**
- Par régime (OOS stressé) : bull +0.0% (189 bougies), bear +40.8% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +82.8% ; percentile vs 200 baselines aléatoires calibrées : 95 ; Calmar 10.90 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C5_min_60pct_fenetres_positives

### AtrBreakout × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'k_entry': 0.5, 'k_exit': 3.25, 'lookback': 20}`
- Configurations testées pour ce couple : 165
- OOS stressé : rendement +81.5%, annualisé +16.1%, Sharpe 0.59, Sortino 0.50, Calmar 0.27, max DD -59.1% (945 bougies), PF 2.57, win rate 62%, 13 trades, expectancy +9.010%
- Fenêtres WF positives (stress) : 50% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.23, médiane des voisins 1.16 -> robuste
- Monte Carlo (2000 tirages, 13 trades) : rendement IC95 [-59.0%, +350.2%], DD p95 -77.3%, P(rendement<0) = 13%
- DSR : SR̂=0.0311, SR₀=0.0862, DSR=0.02 -> **probabilité que le résultat soit dû au hasard/sélection : 98%**
- Par régime (OOS stressé) : bull +130.5% (448 bougies), bear -21.2% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +79.3% ; percentile vs 200 baselines aléatoires calibrées : 64 ; Calmar 2.00 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C4_profit_factor_min_1.15, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### AtrBreakout × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'k_entry': 0.25, 'k_exit': 2.0, 'lookback': 10}`
- Configurations testées pour ce couple : 163
- OOS stressé : rendement +675.7%, annualisé +67.1%, Sharpe 1.13, Sortino 1.13, Calmar 1.14, max DD -58.8% (822 bougies), PF 5.54, win rate 61%, 18 trades, expectancy +17.201%
- Fenêtres WF positives (stress) : 62% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.14, médiane des voisins 1.15 -> robuste
- Monte Carlo (2000 tirages, 18 trades) : rendement IC95 [+8.4%, +710.0%], DD p95 -61.8%, P(rendement<0) = 2%
- DSR : SR̂=0.0593, SR₀=0.0814, DSR=0.20 -> **probabilité que le résultat soit dû au hasard/sélection : 80%**
- Par régime (OOS stressé) : bull +1698.0% (464 bougies), bear -56.9% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +36.8% ; percentile vs 200 baselines aléatoires calibrées : 79 ; Calmar 0.82 vs B&H 0.27
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90

### AtrBreakout × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'k_entry': 0.5, 'k_exit': 1.75, 'lookback': 20}`
- Configurations testées pour ce couple : 93
- OOS stressé : rendement +112.2%, annualisé +45.8%, Sharpe 0.91, Sortino 0.95, Calmar 0.91, max DD -50.5% (442 bougies), PF 2.81, win rate 50%, 10 trades, expectancy +12.954%
- Fenêtres WF positives (stress) : 25% (4 fenêtres)
- Sensibilité : Sharpe optimal 1.89, médiane des voisins 1.86 -> robuste
- Monte Carlo (2000 tirages, 10 trades) : rendement IC95 [-66.5%, +343.8%], DD p95 -83.5%, P(rendement<0) = 11%
- DSR : SR̂=0.0475, SR₀=0.1076, DSR=0.04 -> **probabilité que le résultat soit dû au hasard/sélection : 96%**
- Par régime (OOS stressé) : bull +207.8% (189 bougies), bear -31.1% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +4.7% ; percentile vs 200 baselines aléatoires calibrées : 45 ; Calmar 0.17 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### CrossSectionalMomentum × PORTFOLIO — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'lookback': 30, 'rebalance_every': 3, 'top_k': 2}`
- Configurations testées pour ce couple : 161
- OOS stressé : rendement +791.0%, annualisé +73.0%, Sharpe 1.18, Sortino 1.16, Calmar 1.19, max DD -61.2% (702 bougies), PF 3.97, win rate 58%, 67 trades, expectancy +5.853%
- Fenêtres WF positives (stress) : 62% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.66, médiane des voisins 1.55 -> robuste
- Monte Carlo (2000 tirages, 67 trades) : rendement IC95 [+145.2%, +670.6%], DD p95 -54.5%, P(rendement<0) = 0%
- DSR : SR̂=0.0615, SR₀=0.1070, DSR=0.05 -> **probabilité que le résultat soit dû au hasard/sélection : 95%**
- Par régime (OOS stressé) : bull +4668.1% (373 bougies), bear -81.3% (1083 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +59.5% ; percentile vs 200 baselines aléatoires calibrées : 42 ; Calmar 1.15 vs B&H 2.64
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### ConditionalDca × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 260, 'max_discount': 0.3}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement +0.1%, annualisé +0.0%, Sharpe 0.22, Sortino 0.24, Calmar 0.00, max DD -62.7% (500 bougies), PF 6.17, win rate 88%, 8 trades, expectancy +2.342%
- Fenêtres WF positives (stress) : 75% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.23, médiane des voisins 0.25 -> robuste
- DSR : SR̂=0.0116, SR₀=0.0738, DSR=0.01 -> **probabilité que le résultat soit dû au hasard/sélection : 99%**
- Par régime (OOS stressé) : bull +27.9% (448 bougies), bear -21.8% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +21.1% ; percentile vs 200 baselines aléatoires calibrées : 24 ; Calmar 2.02 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### ConditionalDca × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 200, 'max_discount': 0.4}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement +75.3%, annualisé +15.1%, Sharpe 0.53, Sortino 0.60, Calmar 0.23, max DD -65.2% (596 bougies), PF 11.85, win rate 94%, 33 trades, expectancy +2.769%
- Fenêtres WF positives (stress) : 88% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.14, médiane des voisins 0.16 -> robuste
- Monte Carlo (2000 tirages, 33 trades) : rendement IC95 [+16.1%, +202.6%], DD p95 -16.3%, P(rendement<0) = 0%
- DSR : SR̂=0.0277, SR₀=0.0913, DSR=0.01 -> **probabilité que le résultat soit dû au hasard/sélection : 99%**
- Par régime (OOS stressé) : bull +22.8% (464 bougies), bear +42.8% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +14.3% ; percentile vs 200 baselines aléatoires calibrées : 60 ; Calmar 0.47 vs B&H 0.27
- Critères OK : C1_rendement_net_positif_stress, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90

### ConditionalDca × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 200, 'max_discount': 0.21}`
- Configurations testées pour ce couple : 71
- OOS stressé : rendement +12.4%, annualisé +6.0%, Sharpe 0.43, Sortino 0.41, Calmar 0.08, max DD -75.3% (700 bougies), PF 46.19, win rate 88%, 8 trades, expectancy +5.556%
- Fenêtres WF positives (stress) : 75% (4 fenêtres)
- Sensibilité : Sharpe optimal 0.02, médiane des voisins 0.02 -> robuste
- DSR : SR̂=0.0224, SR₀=0.0433, DSR=0.29 -> **probabilité que le résultat soit dû au hasard/sélection : 71%**
- Par régime (OOS stressé) : bull +0.9% (189 bougies), bear +11.5% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +41.2% ; percentile vs 200 baselines aléatoires calibrées : 74 ; Calmar 1.38 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90

### GridRange × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 30, 'range_pct': 0.1}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement -44.6%, annualisé -13.8%, Sharpe -0.36, Sortino -0.39, Calmar -0.24, max DD -58.3% (825 bougies), PF 0.91, win rate 56%, 52 trades, expectancy -0.199%
- Fenêtres WF positives (stress) : 38% (8 fenêtres)
- Sensibilité : Sharpe optimal -0.29, médiane des voisins -0.35 -> îlot étroit (REJET)
- Monte Carlo (2000 tirages, 52 trades) : rendement IC95 [-85.0%, +64.6%], DD p95 -87.5%, P(rendement<0) = 60%
- DSR : SR̂=-0.0187, SR₀=0.0618, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +63.6% (448 bougies), bear -66.1% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +12.5% ; percentile vs 200 baselines aléatoires calibrées : 18 ; Calmar 0.33 vs B&H 3.75
- Critères OK : aucun
- Critères ÉCHOUÉS : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh, C8_robustesse_parametres

### GridRange × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 35, 'range_pct': 0.15}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement -14.1%, annualisé -3.7%, Sharpe 0.06, Sortino 0.06, Calmar -0.06, max DD -60.5% (815 bougies), PF 1.12, win rate 55%, 73 trades, expectancy +0.303%
- Fenêtres WF positives (stress) : 38% (8 fenêtres)
- Sensibilité : Sharpe optimal -0.10, médiane des voisins -0.23 -> îlot étroit (REJET)
- Monte Carlo (2000 tirages, 73 trades) : rendement IC95 [-105.1%, +143.8%], DD p95 -116.7%, P(rendement<0) = 39%
- DSR : SR̂=0.0033, SR₀=0.0883, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +157.2% (464 bougies), bear -66.6% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : -28.1% ; percentile vs 200 baselines aléatoires calibrées : 20 ; Calmar -0.46 vs B&H 0.27
- Critères OK : aucun
- Critères ÉCHOUÉS : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh, C8_robustesse_parametres

### GridRange × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 100, 'range_pct': 0.2}`
- Configurations testées pour ce couple : 71
- OOS stressé : rendement +29.9%, annualisé +14.0%, Sharpe 0.53, Sortino 0.61, Calmar 0.36, max DD -38.7% (245 bougies), PF 2.25, win rate 62%, 21 trades, expectancy +2.969%
- Fenêtres WF positives (stress) : 75% (4 fenêtres)
- Sensibilité : Sharpe optimal 0.53, médiane des voisins 0.57 -> robuste
- Monte Carlo (2000 tirages, 21 trades) : rendement IC95 [-31.1%, +171.3%], DD p95 -52.9%, P(rendement<0) = 10%
- DSR : SR̂=0.0278, SR₀=0.0641, DSR=0.16 -> **probabilité que le résultat soit dû au hasard/sélection : 84%**
- Par régime (OOS stressé) : bull +8.4% (189 bougies), bear +19.8% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +10.5% ; percentile vs 200 baselines aléatoires calibrées : 50 ; Calmar 0.32 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### EmaCross_VT × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'fast': 10, 'slow': 30, 'trend_filter': 0}`
- Configurations testées pour ce couple : 165
- OOS stressé : rendement +75.8%, annualisé +15.2%, Sharpe 0.78, Sortino 0.81, Calmar 0.41, max DD -37.4% (641 bougies), PF 3.67, win rate 50%, 16 trades, expectancy +6.470%
- Fenêtres WF positives (stress) : 62% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.43, médiane des voisins 1.25 -> robuste
- Monte Carlo (2000 tirages, 16 trades) : rendement IC95 [-21.6%, +270.8%], DD p95 -42.4%, P(rendement<0) = 6%
- DSR : SR̂=0.0410, SR₀=0.1203, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +129.7% (448 bougies), bear -23.5% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +57.1% ; percentile vs 200 baselines aléatoires calibrées : 53 ; Calmar 2.62 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### EmaCross_VT × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'fast': 10, 'slow': 30, 'trend_filter': 0}`
- Configurations testées pour ce couple : 165
- OOS stressé : rendement +80.4%, annualisé +15.9%, Sharpe 0.78, Sortino 0.80, Calmar 0.44, max DD -35.9% (641 bougies), PF 3.43, win rate 44%, 16 trades, expectancy +6.649%
- Fenêtres WF positives (stress) : 75% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.01, médiane des voisins 1.09 -> robuste
- Monte Carlo (2000 tirages, 16 trades) : rendement IC95 [-11.0%, +239.9%], DD p95 -40.9%, P(rendement<0) = 4%
- DSR : SR̂=0.0407, SR₀=0.0918, DSR=0.03 -> **probabilité que le résultat soit dû au hasard/sélection : 97%**
- Par régime (OOS stressé) : bull +166.8% (464 bougies), bear -32.4% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +17.8% ; percentile vs 200 baselines aléatoires calibrées : 66 ; Calmar 0.51 vs B&H 0.27
- Critères OK : C1_rendement_net_positif_stress, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90

### EmaCross_VT × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'fast': 20, 'slow': 50, 'trend_filter': 260}`
- Configurations testées pour ce couple : 93
- OOS stressé : rendement +43.1%, annualisé +19.7%, Sharpe 1.04, Sortino 1.45, Calmar 1.09, max DD -18.1% (252 bougies), PF 1.99, win rate 17%, 12 trades, expectancy +2.326%
- Fenêtres WF positives (stress) : 50% (4 fenêtres)
- Sensibilité : Sharpe optimal 1.14, médiane des voisins 1.19 -> robuste
- Monte Carlo (2000 tirages, 12 trades) : rendement IC95 [-40.5%, +135.9%], DD p95 -36.1%, P(rendement<0) = 32%
- DSR : SR̂=0.0543, SR₀=0.1030, DSR=0.09 -> **probabilité que le résultat soit dû au hasard/sélection : 91%**
- Par régime (OOS stressé) : bull +87.2% (189 bougies), bear -23.5% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : -1.6% ; percentile vs 200 baselines aléatoires calibrées : 36 ; Calmar -0.09 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C8_robustesse_parametres
- Critères ÉCHOUÉS : C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### DonchianBreakout_VT × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'entry': 20, 'exit': 7}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement +88.0%, annualisé +17.2%, Sharpe 0.89, Sortino 0.94, Calmar 0.49, max DD -35.3% (881 bougies), PF 3.45, win rate 55%, 20 trades, expectancy +4.930%
- Fenêtres WF positives (stress) : 50% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.36, médiane des voisins 1.24 -> robuste
- Monte Carlo (2000 tirages, 20 trades) : rendement IC95 [-16.0%, +256.4%], DD p95 -35.0%, P(rendement<0) = 7%
- DSR : SR̂=0.0467, SR₀=0.1203, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +115.1% (448 bougies), bear -12.6% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +55.8% ; percentile vs 200 baselines aléatoires calibrées : 52 ; Calmar 3.15 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90

### DonchianBreakout_VT × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'entry': 10, 'exit': 5}`
- Configurations testées pour ce couple : 123
- OOS stressé : rendement +77.7%, annualisé +15.5%, Sharpe 0.84, Sortino 0.81, Calmar 0.85, max DD -18.1% (521 bougies), PF 2.87, win rate 50%, 26 trades, expectancy +3.302%
- Fenêtres WF positives (stress) : 75% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.08, médiane des voisins 1.03 -> robuste
- Monte Carlo (2000 tirages, 26 trades) : rendement IC95 [+4.9%, +171.2%], DD p95 -30.5%, P(rendement<0) = 2%
- DSR : SR̂=0.0441, SR₀=0.0958, DSR=0.02 -> **probabilité que le résultat soit dû au hasard/sélection : 98%**
- Par régime (OOS stressé) : bull +111.4% (464 bougies), bear -15.9% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +39.9% ; percentile vs 200 baselines aléatoires calibrées : 84 ; Calmar 2.38 vs B&H 0.27
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C6_bat_baseline_aleatoire_p90

### DonchianBreakout_VT × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'entry': 20, 'exit': 7}`
- Configurations testées pour ce couple : 71
- OOS stressé : rendement +42.6%, annualisé +19.5%, Sharpe 1.08, Sortino 1.15, Calmar 1.25, max DD -15.6% (266 bougies), PF 2.28, win rate 45%, 11 trades, expectancy +3.765%
- Fenêtres WF positives (stress) : 75% (4 fenêtres)
- Sensibilité : Sharpe optimal 1.75, médiane des voisins 1.75 -> robuste
- Monte Carlo (2000 tirages, 11 trades) : rendement IC95 [-31.9%, +136.9%], DD p95 -35.5%, P(rendement<0) = 16%
- DSR : SR̂=0.0566, SR₀=0.1303, DSR=0.02 -> **probabilité que le résultat soit dû au hasard/sélection : 98%**
- Par régime (OOS stressé) : bull +69.4% (189 bougies), bear -15.8% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +2.6% ; percentile vs 200 baselines aléatoires calibrées : 46 ; Calmar 0.24 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### MeanReversion_VT × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'rsi_entry': 30, 'rsi_period': 14, 'time_stop': 7, 'z_entry': -2.0, 'z_window': 20}`
- Configurations testées pour ce couple : 241
- OOS stressé : rendement +5.0%, annualisé +1.2%, Sharpe 0.18, Sortino 0.06, Calmar 0.09, max DD -13.9% (1240 bougies), PF 1.29, win rate 67%, 9 trades, expectancy +0.562%
- Fenêtres WF positives (stress) : 38% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.20, médiane des voisins 0.13 -> robuste
- DSR : SR̂=0.0095, SR₀=0.0959, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +2.2% (448 bougies), bear +2.7% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +12.2% ; percentile vs 200 baselines aléatoires calibrées : 21 ; Calmar 1.73 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### MeanReversion_VT × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'rsi_entry': 21, 'rsi_period': 14, 'time_stop': 10, 'z_entry': -2.0, 'z_window': 20}`
- Configurations testées pour ce couple : 241
- OOS stressé : rendement -7.3%, annualisé -1.9%, Sharpe -0.32, Sortino -0.07, Calmar -0.13, max DD -14.9% (680 bougies), PF 0.37, win rate 50%, 4 trades, expectancy -1.672%
- Fenêtres WF positives (stress) : 25% (8 fenêtres)
- Sensibilité : Sharpe optimal -0.13, médiane des voisins -0.13 -> îlot étroit (REJET)
- DSR : SR̂=-0.0165, SR₀=0.0830, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +0.0% (464 bougies), bear -7.3% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +2.8% ; percentile vs 200 baselines aléatoires calibrées : 58 ; Calmar 1.13 vs B&H 0.27
- Critères OK : C3_max_dd_max_30pct, C7_calmar_competitif_vs_bh
- Critères ÉCHOUÉS : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C8_robustesse_parametres

### MeanReversion_VT × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'rsi_entry': 30, 'rsi_period': 14, 'time_stop': 13, 'z_entry': -2.0, 'z_window': 20}`
- Configurations testées pour ce couple : 137
- OOS stressé : rendement +11.3%, annualisé +5.5%, Sharpe 0.76, Sortino 0.32, Calmar 0.85, max DD -6.5% (512 bougies), PF 4.74, win rate 50%, 4 trades, expectancy +2.880%
- Fenêtres WF positives (stress) : 50% (4 fenêtres)
- Sensibilité : Sharpe optimal 0.78, médiane des voisins 0.75 -> robuste
- DSR : SR̂=0.0399, SR₀=0.0660, DSR=0.22 -> **probabilité que le résultat soit dû au hasard/sélection : 78%**
- Par régime (OOS stressé) : bull +0.0% (189 bougies), bear +11.3% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +7.5% ; percentile vs 200 baselines aléatoires calibrées : 56 ; Calmar 4.39 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90

### AtrBreakout_VT × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'k_entry': 0.5, 'k_exit': 3.25, 'lookback': 20}`
- Configurations testées pour ce couple : 165
- OOS stressé : rendement +62.1%, annualisé +12.9%, Sharpe 0.81, Sortino 0.73, Calmar 0.41, max DD -31.5% (945 bougies), PF 3.10, win rate 62%, 13 trades, expectancy +5.449%
- Fenêtres WF positives (stress) : 62% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.40, médiane des voisins 1.27 -> robuste
- Monte Carlo (2000 tirages, 13 trades) : rendement IC95 [-24.1%, +200.2%], DD p95 -35.6%, P(rendement<0) = 10%
- DSR : SR̂=0.0421, SR₀=0.0898, DSR=0.03 -> **probabilité que le résultat soit dû au hasard/sélection : 97%**
- Par régime (OOS stressé) : bull +66.4% (448 bougies), bear -2.6% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +46.3% ; percentile vs 200 baselines aléatoires calibrées : 47 ; Calmar 2.20 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### AtrBreakout_VT × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'k_entry': 0.5, 'k_exit': 3.25, 'lookback': 20}`
- Configurations testées pour ce couple : 165
- OOS stressé : rendement +130.7%, annualisé +23.3%, Sharpe 1.12, Sortino 1.16, Calmar 1.36, max DD -17.2% (693 bougies), PF 4.20, win rate 61%, 18 trades, expectancy +5.367%
- Fenêtres WF positives (stress) : 75% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.14, médiane des voisins 1.10 -> robuste
- Monte Carlo (2000 tirages, 18 trades) : rendement IC95 [+1.0%, +211.0%], DD p95 -27.0%, P(rendement<0) = 2%
- DSR : SR̂=0.0586, SR₀=0.0815, DSR=0.19 -> **probabilité que le résultat soit dû au hasard/sélection : 81%**
- Par régime (OOS stressé) : bull +153.7% (464 bougies), bear -9.1% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +23.1% ; percentile vs 200 baselines aléatoires calibrées : 68 ; Calmar 0.79 vs B&H 0.27
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C6_bat_baseline_aleatoire_p90

### AtrBreakout_VT × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'k_entry': 0.5, 'k_exit': 1.75, 'lookback': 20}`
- Configurations testées pour ce couple : 93
- OOS stressé : rendement +26.3%, annualisé +12.4%, Sharpe 0.81, Sortino 0.76, Calmar 0.69, max DD -17.9% (444 bougies), PF 2.47, win rate 56%, 9 trades, expectancy +3.488%
- Fenêtres WF positives (stress) : 50% (4 fenêtres)
- Sensibilité : Sharpe optimal 1.87, médiane des voisins 1.82 -> robuste
- DSR : SR̂=0.0426, SR₀=0.1292, DSR=0.01 -> **probabilité que le résultat soit dû au hasard/sélection : 99%**
- Par régime (OOS stressé) : bull +46.0% (189 bougies), bear -13.5% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +5.1% ; percentile vs 200 baselines aléatoires calibrées : 50 ; Calmar 0.60 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90

### CrossSectionalMomentum_VT × PORTFOLIO — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'lookback': 30, 'rebalance_every': 3, 'top_k': 2}`
- Configurations testées pour ce couple : 161
- OOS stressé : rendement +108.6%, annualisé +20.2%, Sharpe 0.99, Sortino 1.00, Calmar 0.69, max DD -29.4% (641 bougies), PF 3.49, win rate 57%, 67 trades, expectancy +1.759%
- Fenêtres WF positives (stress) : 62% (8 fenêtres)
- Sensibilité : Sharpe optimal 1.69, médiane des voisins 1.59 -> robuste
- Monte Carlo (2000 tirages, 67 trades) : rendement IC95 [+39.3%, +199.8%], DD p95 -20.4%, P(rendement<0) = 0%
- DSR : SR̂=0.0518, SR₀=0.1206, DSR=0.01 -> **probabilité que le résultat soit dû au hasard/sélection : 99%**
- Par régime (OOS stressé) : bull +206.9% (373 bougies), bear -32.0% (1083 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +30.8% ; percentile vs 200 baselines aléatoires calibrées : 25 ; Calmar 1.43 vs B&H 2.64
- Critères OK : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### ConditionalDca_VT × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 260, 'max_discount': 0.3}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement +13.4%, annualisé +3.2%, Sharpe 0.27, Sortino 0.27, Calmar 0.10, max DD -33.0% (500 bougies), PF 8.01, win rate 89%, 9 trades, expectancy +2.226%
- Fenêtres WF positives (stress) : 75% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.26, médiane des voisins 0.27 -> robuste
- DSR : SR̂=0.0142, SR₀=0.0751, DSR=0.01 -> **probabilité que le résultat soit dû au hasard/sélection : 99%**
- Par régime (OOS stressé) : bull +14.5% (448 bougies), bear -1.0% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +12.4% ; percentile vs 200 baselines aléatoires calibrées : 22 ; Calmar 2.31 vs B&H 3.75
- Critères OK : C1_rendement_net_positif_stress, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh

### ConditionalDca_VT × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 260, 'max_discount': 0.3}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement +30.6%, annualisé +6.9%, Sharpe 0.54, Sortino 0.59, Calmar 0.25, max DD -27.5% (596 bougies), PF 4.30, win rate 94%, 33 trades, expectancy +0.564%
- Fenêtres WF positives (stress) : 75% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.03, médiane des voisins 0.03 -> robuste
- Monte Carlo (2000 tirages, 33 trades) : rendement IC95 [-1.2%, +39.5%], DD p95 -11.3%, P(rendement<0) = 4%
- DSR : SR̂=0.0283, SR₀=0.1048, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +9.0% (464 bougies), bear +19.9% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +13.1% ; percentile vs 200 baselines aléatoires calibrées : 59 ; Calmar 1.10 vs B&H 0.27
- Critères OK : C1_rendement_net_positif_stress, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C6_bat_baseline_aleatoire_p90

### ConditionalDca_VT × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 200, 'max_discount': 0.21}`
- Configurations testées pour ce couple : 71
- OOS stressé : rendement +14.0%, annualisé +6.8%, Sharpe 0.47, Sortino 0.47, Calmar 0.26, max DD -26.5% (333 bougies), PF 56.27, win rate 88%, 8 trades, expectancy +1.584%
- Fenêtres WF positives (stress) : 75% (4 fenêtres)
- Sensibilité : Sharpe optimal 0.09, médiane des voisins 0.09 -> robuste
- DSR : SR̂=0.0247, SR₀=0.0479, DSR=0.27 -> **probabilité que le résultat soit dû au hasard/sélection : 73%**
- Par régime (OOS stressé) : bull +0.2% (189 bougies), bear +13.8% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +17.9% ; percentile vs 200 baselines aléatoires calibrées : 57 ; Calmar 2.38 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C6_bat_baseline_aleatoire_p90

### GridRange_VT × BTC/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 30, 'range_pct': 0.1}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement -26.9%, annualisé -7.5%, Sharpe -0.58, Sortino -0.55, Calmar -0.22, max DD -34.9% (1438 bougies), PF 0.81, win rate 55%, 56 trades, expectancy -0.180%
- Fenêtres WF positives (stress) : 50% (8 fenêtres)
- Sensibilité : Sharpe optimal -0.22, médiane des voisins -0.31 -> îlot étroit (REJET)
- Monte Carlo (2000 tirages, 56 trades) : rendement IC95 [-43.0%, +23.6%], DD p95 -43.5%, P(rendement<0) = 74%
- DSR : SR̂=-0.0304, SR₀=0.0618, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +21.9% (448 bougies), bear -40.0% (1008 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +2.1% ; percentile vs 200 baselines aléatoires calibrées : 11 ; Calmar 0.09 vs B&H 3.75
- Critères OK : aucun
- Critères ÉCHOUÉS : C1_rendement_net_positif_stress, C2_sharpe_oos_min_0.8, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh, C8_robustesse_parametres

### GridRange_VT × ETH/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 30, 'range_pct': 0.1}`
- Configurations testées pour ce couple : 127
- OOS stressé : rendement +18.5%, annualisé +4.3%, Sharpe 0.46, Sortino 0.47, Calmar 0.30, max DD -14.4% (535 bougies), PF 1.44, win rate 58%, 65 trades, expectancy +0.341%
- Fenêtres WF positives (stress) : 62% (8 fenêtres)
- Sensibilité : Sharpe optimal 0.07, médiane des voisins -0.04 -> îlot étroit (REJET)
- Monte Carlo (2000 tirages, 65 trades) : rendement IC95 [-18.7%, +63.0%], DD p95 -29.8%, P(rendement<0) = 15%
- DSR : SR̂=0.0239, SR₀=0.0986, DSR=0.00 -> **probabilité que le résultat soit dû au hasard/sélection : 100%**
- Par régime (OOS stressé) : bull +33.2% (464 bougies), bear -11.0% (992 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +2.6% ; percentile vs 200 baselines aléatoires calibrées : 55 ; Calmar 0.17 vs B&H 0.27
- Critères OK : C1_rendement_net_positif_stress, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C6_bat_baseline_aleatoire_p90, C7_calmar_competitif_vs_bh, C8_robustesse_parametres

### GridRange_VT × SOL/USDT — REJETÉE

- Paramètres retenus (mode du walk-forward) : `{'ma_window': 100, 'range_pct': 0.2}`
- Configurations testées pour ce couple : 71
- OOS stressé : rendement +0.8%, annualisé +0.4%, Sharpe 0.10, Sortino 0.11, Calmar 0.03, max DD -13.0% (642 bougies), PF 1.61, win rate 64%, 33 trades, expectancy +0.393%
- Fenêtres WF positives (stress) : 75% (4 fenêtres)
- Sensibilité : Sharpe optimal 0.40, médiane des voisins 0.48 -> robuste
- Monte Carlo (2000 tirages, 33 trades) : rendement IC95 [-13.8%, +41.9%], DD p95 -18.4%, P(rendement<0) = 20%
- DSR : SR̂=0.0051, SR₀=0.0570, DSR=0.08 -> **probabilité que le résultat soit dû au hasard/sélection : 92%**
- Par régime (OOS stressé) : bull +6.1% (189 bougies), bear -5.0% (539 bougies), range +0.0% (0 bougies)
- Segment validation (15 %, coûts stressés) : +8.8% ; percentile vs 200 baselines aléatoires calibrées : 56 ; Calmar 0.89 vs B&H 0.46
- Critères OK : C1_rendement_net_positif_stress, C3_max_dd_max_30pct, C4_profit_factor_min_1.15, C5_min_60pct_fenetres_positives, C7_calmar_competitif_vs_bh, C8_robustesse_parametres
- Critères ÉCHOUÉS : C2_sharpe_oos_min_0.8, C6_bat_baseline_aleatoire_p90

