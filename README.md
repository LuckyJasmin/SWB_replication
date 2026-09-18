# Replication package — "What Happens Matters More Than Who"

This package reproduces every result reported in **Section 4** (and the
associated appendix tables and figures) of the manuscript, directly from the
raw data file.

## Contents

```
replication/
├── README.md                         this file
├── requirements.txt                  Python dependencies
├── olstools.py                       OLS with cluster-robust (CR1) SEs
├── 00_data_prep.py                   loads data, builds all derived variables
├── 01_loss_asymmetry.py              §4.1  · Figure 2
├── 02_prereg_demographic.py          §4.2  · Table 1, Tables A2–A4
├── 03_perceived_similarity_moderation.py  §4.3.1 · Table 2
├── 04_redistribution.py              §4.3.2 · Figure 3, Table A5
├── 05_attention.py                   §4.3.3 · Figure 4, Table A6
├── 06_determinants.py                §4.3.4 · Table 3, Table A7
├── 07_baseline_and_balance.py        §4.1  · Figure A1, Table A1
├── data/
│   └── cleaneddta_panelall.dta       analytic dataset (950 evaluators)
└── output/                           figures written here when scripts run
```

## How to run

```bash
pip install -r requirements.txt
python 01_loss_asymmetry.py
python 02_prereg_demographic.py
# ... etc. Each script is standalone and prints its results to the console.
```

Every script imports `00_data_prep.py` (which reads `data/cleaneddta_panelall.dta`)
and `olstools.py`, so run them from inside the `replication/` folder. Scripts
print each estimate to the console labeled by the table/figure it corresponds to,
and figure scripts write PNGs to `output/`.

## Data and key variable construction

- **Unit of analysis.** The raw file is a long panel (18,049 rows). Two panels
  are built in `00_data_prep.py`: the *judgment panel* (`ETPage_Code==2`, eight
  shocks per evaluator, 7,600 rows) and the *allocation panel* (four negative
  shocks per evaluator, 3,799 rows). An evaluator-level table (`subj`) holds
  one row per participant.
- **ΔSWB** = post-shock judged life satisfaction − judged baseline. Life
  satisfaction is stored 1–11 but was displayed on a 0–10 ladder; because ΔSWB
  is a difference the offset cancels, so ΔSWB uses the stored coding. Baseline
  *levels* are reported on the 0–10 scale (stored − 1); hence "baseline 6.23".
- **Demographic similarity:** `same_gender` (1 if evaluator and target share
  gender) and `age_gap_z` (standardized |evaluator age − target age|). Both are
  randomized through the target profile.
- **Perceived similarity:** self-reported 1–11 (`perc`), used raw on the 0–10
  scale (`perc0`) in Table 2 column 2 and standardized (`perc_z`) elsewhere.
- **Circumstance matches:** married, 2+ children, income within one bracket of
  the profile, and comparable ("moderate") health.
- **Shock mapping.** The judgment task and allocation task index the four
  negative shocks with different codes; `P1_TO_SHOCK` / `P2_TO_SHOCK` reconcile
  them so each allocation decision is matched to the same shock's judged loss.

## Standard errors

`olstools.ols_cluster` computes OLS with cluster-robust (CR1) standard errors
clustered by participant, matching Stata's `regress y x..., vce(cluster id)`
(finite-sample factor `(G/(G-1))·((N-1)/(N-k))`, inference on `t(G-1)`).
Evaluator fixed-effects specifications are estimated by within-participant
demeaning.

## Notes on samples (why N differs across tables)

The manuscript uses a **common estimation sample within each table** so that
columns are comparable. Three participants are missing evaluator age, which is
needed to build `age_gap_z`; wherever a table includes an age-based column, all
columns of that table drop those participants. Consequently:

- **Table 1 / Tables A2–A3 (pre-registered):** 947 participants (7,575 judgment
  obs; 3,787 allocation obs).
- **Table 2, Table A6, Figure 2/3/4, Table A5:** 950 participants (7,599
  judgment obs; 3,799/3,798 allocation obs), since these use perceived
  similarity, which is non-missing for all 950.
- **Table 3 / Table A7:** income- and health-match specifications lose a few
  additional participants with missing income/health (N = 918 / 7,359), as noted
  in the manuscript.

## Reproduction status

All reported estimates reproduce to the precision shown in the manuscript. One
immaterial cosmetic difference: in Table 2 column 2 (raw 0–10 similarity scale),
the *Negative* main-effect coefficient is −3.00 here vs −3.05 as printed; this is
the intercept-shift term from the raw-scale centering and is not an object of
inference — the interaction of interest (0.048, p<0.01) matches exactly. All
other coefficients, standard errors, R², and Ns match.

The magnitude test for the loss-asymmetry claim (§4.1) is the **paired**
within-participant comparison of |ΔSWB| for negative vs. positive shocks
(t = 23.9, p < 0.001), reproduced in `01_loss_asymmetry.py`.
