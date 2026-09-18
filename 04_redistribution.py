"""
04_redistribution.py
Section 4.3.2 — Perceived similarity and resource allocation.

Outputs:
  output/figure3_allocation_terciles.png   (Figure 3: allocation by similarity tercile)
  output/04_tableA5.docx                    (Table A5: harm-controls regression)

Run from inside the replication/ folder:  python 04_redistribution.py
Requires: python-docx
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib as mpl
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from olstools import ols_cluster

exec(open("00_data_prep.py").read())


def star(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""


df, subj = build_data()
al = allocation_panel(df, subj)

# ============================================================
# FIGURE 3 — allocation by perceived-similarity tercile  (unchanged)
# ============================================================
ev = subj[["SubjectID", "perc0"]].dropna()
almean = al.groupby("SubjectID", as_index=False)["alloc"].mean().merge(ev, on="SubjectID")
q1, q2 = almean["perc0"].quantile([1/3, 2/3])
def grp(v): return "Low" if v <= q1 else ("Medium" if v <= q2 else "High")
almean["g"] = almean["perc0"].apply(grp)
order = ["Low", "Medium", "High"]
summ = almean.groupby("g")["alloc"].agg(["mean", "sem", "count"]).reindex(order)

mpl.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"],
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "savefig.dpi": 200, "savefig.bbox": "tight"})
COLS = {"Low": "#A8C4B8", "Medium": "#6E9E8B", "High": "#3B6B5E"}
fig, ax = plt.subplots(figsize=(6.6, 4.6))
x = np.arange(3)
for i, gg in enumerate(order):
    ax.bar(x[i], summ.loc[gg, "mean"], width=0.6, color=COLS[gg], edgecolor="white",
           yerr=1.96*summ.loc[gg, "sem"], error_kw=dict(ecolor="#444", lw=1.3, capsize=4))
ax.set_xticks(x); ax.set_xticklabels(order)
ax.set_xlabel("Perceived similarity to target")
ax.set_ylabel("Mean allocation to target (out of 100 dollars)")
ax.set_ylim(0, 60)
os.makedirs("output", exist_ok=True)
fig.savefig("output/figure3_allocation_terciles.png"); plt.close(fig)
print("saved output/figure3_allocation_terciles.png")

# ============================================================
# TABLE A5 — does judged loss explain the similarity premium?
# ============================================================
bl = subj[["SubjectID", "baseline"]]
jud = df[df["ETPage_Code"] == 2][["SubjectID", "treat_p1shock", "swb_sk"]].merge(bl, on="SubjectID")
jud["dswb"] = jud["swb_sk"] - jud["baseline"]
jud = jud[jud["treat_p1shock"].isin([1, 2, 3, 4])].copy()
jud["shock"] = jud["treat_p1shock"].map(P1_TO_SHOCK)
jud = jud.rename(columns={"swb_sk": "postSWB"})[["SubjectID", "shock", "dswb", "postSWB", "baseline"]]

d = al.drop(columns=["baseline"]).merge(jud, on=["SubjectID", "shock"], how="left")
for s in ["cut10", "cut20", "demote"]:
    d[f"sk_{s}"] = (d["shock"] == s).astype(float)
SK = ["sk_cut10", "sk_cut20", "sk_demote"]
COVS = ["ev_female", "ev_married", "ev_loginc", "inc_miss",
        "ev_age", "ev_edu", "ev_nonwhite", "ev_ownswb"]
d["loss_abs"] = -d["dswb"]
d = d.dropna(subset=["alloc", "perc_z"]).reset_index(drop=True)


def run(cols, names):
    dd = d.dropna(subset=cols).copy()
    X = np.column_stack([np.ones(len(dd))] + [dd[c].values for c in cols])
    return ols_cluster(dd["alloc"].values, X, dd["SubjectID"].values, ["const"] + names)


specs = [
    (["perc_z"] + SK, ["PercSim"] + SK),
    (["perc_z", "dswb"] + SK, ["PercSim", "JudgedLoss"] + SK),
    (["perc_z", "dswb"] + SK + COVS, ["PercSim", "JudgedLoss"] + SK + COVS),
    (["perc_z", "loss_abs"] + SK, ["PercSim", "AbsLoss"] + SK),
    (["perc_z", "postSWB"] + SK, ["PercSim", "PostSWB"] + SK),
    (["perc_z", "postSWB", "baseline"] + SK, ["PercSim", "PostSWB", "Baseline"] + SK),
]
RES = [run(c, n) for c, n in specs]

# ---- Word table ----
doc = Document()
doc.styles["Normal"].font.name = "Times New Roman"
doc.styles["Normal"].font.size = Pt(11)


def setc(cell, txt, bold=False, ital=False, align="center", size=9):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER}[align]
    r = p.add_run(str(txt)); r.bold = bold; r.italic = ital
    r.font.name = "Times New Roman"; r.font.size = Pt(size)


p = doc.add_paragraph()
rr = p.add_run("Table A5. Does judged loss explain the similarity allocation premium?")
rr.bold = True; rr.font.size = Pt(11); rr.font.name = "Times New Roman"

t = doc.add_table(rows=1, cols=7); t.alignment = WD_TABLE_ALIGNMENT.CENTER
h = t.rows[0].cells
setc(h[0], "Dependent variable: amount allocated", bold=True, align="left", size=8)
for j in range(6):
    setc(h[j+1], f"({j+1})", bold=True)


def row(label, name):
    cr = t.add_row().cells; setc(cr[0], label, align="left")
    sr = t.add_row().cells; setc(sr[0], "", align="left")
    for j, (r, m) in enumerate(RES):
        if name in r.index:
            setc(cr[j+1], f"{r.loc[name,'coef']:.3f}{star(r.loc[name,'p'])}")
            setc(sr[j+1], f"({r.loc[name,'se']:.3f})", size=8)
        else:
            setc(cr[j+1], ""); setc(sr[j+1], "")


row("Perceived similarity (z)", "PercSim")
row("Judged loss (ΔSWB)", "JudgedLoss")
row("Absolute judged loss", "AbsLoss")
row("Post-shock life satisfaction", "PostSWB")
row("Baseline life satisfaction", "Baseline")

meta = [("Shock fixed effects", ["Yes"]*6),
        ("Evaluator covariates", ["No", "No", "Yes", "No", "No", "No"]),
        ("Observations", [f"{int(m['N']):,}" for _, m in RES]),
        ("R²", [f"{m['r2']:.3f}" for _, m in RES]),
        ("Participants", [f"{int(m['G'])}" for _, m in RES])]
for label, vals in meta:
    rr = t.add_row().cells; setc(rr[0], label, align="left", size=8)
    for j, v in enumerate(vals):
        setc(rr[j+1], v, size=8)

p = doc.add_paragraph(); nr = p.add_run(
 "Notes: OLS on the allocation panel (four negative shocks per participant). The dependent variable "
 "is the percentage of $100 allocated to the target. Perceived similarity is standardized. Judged "
 "loss (ΔSWB) is the participant’s shock-specific change in the target’s judged life satisfaction "
 "(post-shock minus baseline; more negative = larger perceived harm), matched to the same shock in "
 "the allocation task. Column 4 replaces signed loss with its absolute value; columns 5–6 use the "
 "post-shock life-satisfaction level (and, in column 6, the baseline level) in place of the change. "
 "All columns include shock fixed effects (worsened back pain omitted); column 3 adds evaluator "
 "covariates (gender, marital status, log household income and a missing-income indicator, age, "
 "education, a non-white indicator, and own life satisfaction). Cluster-robust standard errors (by "
 "participant) in parentheses. * p<0.05, ** p<0.01, *** p<0.001.")
nr.italic = True; nr.font.size = Pt(8); nr.font.name = "Times New Roman"

doc.save("output/04_tableA5.docx")
print("saved output/04_tableA5.docx")