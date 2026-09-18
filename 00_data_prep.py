"""
00_data_prep.py — Load raw data and construct all derived variables used
across the replication scripts. Every analysis script imports build_data().

Data: data/cleaneddta_panelall.dta  (18,049 rows; 950 analytic evaluators)

Scale note: judged life satisfaction is stored 1-11 but was displayed to
participants on a 0-10 ladder. We keep the stored coding for ΔSWB (a
difference, so the offset cancels) and convert to 0-10 only for reporting
baseline *levels*.
"""
import numpy as np
import pandas as pd

DATA_PATH = "data/cleaneddta_panelall.dta"


def build_data():
    df = pd.read_stata(DATA_PATH, convert_categoricals=False)

    # ---- evaluator-level table (one row per participant) ----
    subj = (df.sort_values("SubjectID")
              .groupby("SubjectID", as_index=False)
              .first())

    # baseline judged SWB of the target (stored 1-11)
    subj["baseline"] = subj["swb_bl"]
    subj["baseline0"] = subj["swb_bl"] - 1        # 0-10 displayed scale

    # ---- demographic similarity (randomized) ----
    subj["prof_age"]   = np.where(subj["treat_old"] == 1, 55, 35)
    subj["same_gender"] = (((subj["pq_gender"] == 1) & (subj["treat_female"] == 1)) |
                           ((subj["pq_gender"] == 0) & (subj["treat_female"] == 0))).astype(float)
    subj["age_gap"]    = (subj["pq_age"] - subj["prof_age"]).abs()
    subj["age_gap_z"]  = (subj["age_gap"] - subj["age_gap"].mean()) / subj["age_gap"].std()

    # ---- perceived similarity (self-report, 1-11 stored) ----
    subj["perc"]   = subj["s_smlrt"]
    subj["perc0"]  = subj["s_smlrt"] - 1
    subj["perc_z"] = (subj["s_smlrt"] - subj["s_smlrt"].mean()) / subj["s_smlrt"].std()

    # ---- circumstance matches ----
    subj["m_married"] = (subj["pq_marital"] == 1).astype(float)
    subj["m_2kids"]   = subj["pq_nchildren"].isin([2, 3, 4]).astype(float)
    subj["m_income"]  = (subj["pq_hhincome"].sub(5).abs() <= 1).astype(float)
    subj.loc[subj["pq_hhincome"].isna(), "m_income"] = np.nan
    subj.loc[subj["pq_hhincome"] == 14, "m_income"] = np.nan
    subj["m_health"]  = ((subj["pq_h1"].sub(4).abs() <= 1) &
                         (subj["pq_h4"].sub(4).abs() <= 1)).astype(float)
    subj.loc[subj["pq_h1"].isna() | subj["pq_h4"].isna(), "m_health"] = np.nan

    # ---- evaluator covariates (for control specifications) ----
    subj["ev_female"]  = (subj["pq_gender"] == 1).astype(float)
    subj["ev_married"] = (subj["pq_marital"] == 1).astype(float)
    subj["ev_loginc"]  = np.log(subj["pq_hhincome"].replace(14, np.nan) + 1)
    subj["inc_miss"]   = (subj["pq_hhincome"].isin([14]) | subj["pq_hhincome"].isna()).astype(float)
    subj["ev_loginc"]  = subj["ev_loginc"].fillna(subj["ev_loginc"].mean())
    subj["ev_age"]     = subj["pq_age"].fillna(subj["pq_age"].mean())
    subj["ev_edu"]     = subj["pq_edu"].replace(6, np.nan)
    subj["ev_edu"]     = subj["ev_edu"].fillna(subj["ev_edu"].mean())
    subj["ev_nonwhite"] = (subj["pq_race"] != 0).astype(float)
    subj.loc[subj["pq_race"].isna(), "ev_nonwhite"] = 0.0
    subj["ev_ownswb"]  = subj["swb_own"]

    return df, subj


# shock code -> common label maps (verified from value labels)
P1_TO_SHOCK = {1: "backpain", 2: "cut10", 3: "cut20", 4: "demote"}   # negatives only
P2_TO_SHOCK = {1: "cut10", 2: "cut20", 3: "demote", 4: "backpain"}   # allocation task


def judgment_panel(df, subj):
    """Part-1 judgment panel: 8 shocks per evaluator, with ΔSWB."""
    keep = subj[["SubjectID", "baseline", "same_gender", "age_gap_z",
                 "perc", "perc0", "perc_z",
                 "m_married", "m_2kids", "m_income", "m_health",
                 "ev_female", "ev_married", "ev_loginc", "inc_miss",
                 "ev_age", "ev_edu", "ev_nonwhite", "ev_ownswb"]]
    sh = df[df["ETPage_Code"] == 2].copy().merge(keep, on="SubjectID", how="left")
    sh["dswb"] = sh["swb_sk"] - sh["baseline"]
    sh["neg"]  = sh["treat_p1shock_neg"]
    return sh


def allocation_panel(df, subj):
    """Part-2 allocation panel: 4 negative shocks per evaluator."""
    keep = subj[["SubjectID", "baseline", "same_gender", "age_gap_z",
                 "perc_z", "m_married", "m_2kids", "m_income", "m_health",
                 "ev_female", "ev_married", "ev_loginc", "inc_miss",
                 "ev_age", "ev_edu", "ev_nonwhite", "ev_ownswb"]]
    al = df[df["alct"].notna()].copy().merge(keep, on="SubjectID", how="left")
    al["alloc"] = al["alct"]
    al["shock"] = al["treat_p2shock"].map(P2_TO_SHOCK)
    return al


if __name__ == "__main__":
    df, subj = build_data()
    print(f"raw rows: {len(df):,}")
    print(f"evaluators: {subj['SubjectID'].nunique()}")
    sh = judgment_panel(df, subj)
    al = allocation_panel(df, subj)
    print(f"judgment panel rows: {len(sh):,}")
    print(f"allocation panel rows: {len(al):,}")
    print(f"baseline (0-10): mean={subj['baseline0'].mean():.3f} SD={subj['baseline0'].std():.3f}")
