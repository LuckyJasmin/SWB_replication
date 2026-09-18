"""
06_determinants.py
Section 4.3.4 — What predicts perceived similarity, and do the components moderate the bias?

Outputs a single Word file:
  output/06_tables.docx
    Table 3  — Determinants of perceived similarity (demographics; +circumstance; +health)
    Table A7 — Moderation of the negativity bias by demographic and circumstance matches

Run from inside the replication/ folder:  python 06_determinants.py
Requires: python-docx
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import f as fdist
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from olstools import ols_cluster

exec(open("00_data_prep.py").read())


def star(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""


df, subj = build_data()

# ============================================================
# TABLE 3 — determinants of perceived similarity
# ============================================================
s = subj.dropna(subset=["perc0", "age_gap", "same_gender"]).copy()
s["gen_health"] = s["pq_h1"]
s["bodily_pain"] = s["pq_h4"]


def det(cols, names):
    dd = s.dropna(subset=cols).copy()
    X = np.column_stack([np.ones(len(dd))] + [dd[c].values for c in cols])
    return ols_cluster(dd["perc0"].values, X, dd["SubjectID"].values, ["const"] + names)


# NOTE: the manuscript's Table 3 reports the age-gap coefficient on the RAW
# (years) scale (coef ~= -0.037), although the row is labelled "Age gap (z)".
# We therefore use the raw age gap here to reproduce the printed coefficients.
T3_SPECS = [
    (["age_gap", "same_gender"],
     ["Age gap (z)", "Same gender"]),
    (["age_gap", "same_gender", "m_married", "m_2kids", "m_income"],
     ["Age gap (z)", "Same gender", "Married match", "2+ children", "Income match"]),
    (["age_gap", "same_gender", "m_married", "m_2kids", "m_income", "gen_health", "bodily_pain"],
     ["Age gap (z)", "Same gender", "Married match", "2+ children", "Income match",
      "General health", "Bodily pain"]),
]
T3 = [det(c, n) for c, n in T3_SPECS]

# row order for Table 3
T3_ROWS = ["Age gap (z)", "Same gender", "Married match", "2+ children",
           "Income match", "General health", "Bodily pain"]

# ============================================================
# TABLE A7 — component matches moderating the negativity bias
# ============================================================
sh = judgment_panel(df, subj)
COMPS = [("m_married", "Married"), ("m_2kids", "2+ children"),
         ("m_income", "Income"), ("m_health", "Health")]
A7 = {}
for cv, lab in COMPS:
    d = sh.dropna(subset=["dswb", "neg", cv]).copy()
    d["int"] = d["neg"] * d[cv]
    X = np.column_stack([np.ones(len(d)), d["neg"], d[cv], d["int"]])
    A7[lab] = ols_cluster(d["dswb"].values, X, d["SubjectID"].values,
                          ["const", "Negative", "Sim", "NegxSim"])

# joint column: all four matches + interactions
dj = sh.dropna(subset=["dswb", "neg", "m_married", "m_2kids", "m_income", "m_health"]).copy()
cols, names = [dj["neg"].values], ["Negative"]
for cv, lab in COMPS:
    dj[f"i_{cv}"] = dj["neg"] * dj[cv]
    cols += [dj[cv].values, dj[f"i_{cv}"].values]
    names += [f"{lab} main", f"Neg×{lab}"]
Xj = np.column_stack([np.ones(len(dj))] + cols)
rj, mj = ols_cluster(dj["dswb"].values, Xj, dj["SubjectID"].values, ["const"] + names)
# joint Wald test that the four interactions are zero
V = mj["V"]; beta = rj["coef"].values
idx = [list(rj.index).index(f"Neg×{lab}") for _, lab in COMPS]
R = np.zeros((4, len(beta)))
for j2, ix in enumerate(idx):
    R[j2, ix] = 1
Rb = R @ beta
wald = float(Rb.T @ np.linalg.inv(R @ V @ R.T) @ Rb)
Fjoint = wald / 4
Gj = mj["G"]
pjoint = fdist.sf(Fjoint, 4, Gj - 1)

# ============================================================
# WORD OUTPUT
# ============================================================
doc = Document()
doc.styles["Normal"].font.name = "Times New Roman"
doc.styles["Normal"].font.size = Pt(11)


def setc(cell, txt, bold=False, ital=False, align="center", size=9):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER}[align]
    r = p.add_run(str(txt)); r.bold = bold; r.italic = ital
    r.font.name = "Times New Roman"; r.font.size = Pt(size)


def title(txt):
    p = doc.add_paragraph(); r = p.add_run(txt)
    r.bold = True; r.font.size = Pt(11); r.font.name = "Times New Roman"


def note(txt):
    p = doc.add_paragraph(); r = p.add_run(txt)
    r.italic = True; r.font.size = Pt(8); r.font.name = "Times New Roman"


# ---------- Table 3 ----------
title("Table 3. Determinants of perceived similarity")
t = doc.add_table(rows=1, cols=4); t.alignment = WD_TABLE_ALIGNMENT.CENTER
h = t.rows[0].cells
setc(h[0], "Dependent variable: perceived similarity", bold=True, align="left", size=8)
for j in range(3):
    setc(h[j+1], f"({j+1})", bold=True)
for rowname in T3_ROWS:
    cr = t.add_row().cells; setc(cr[0], rowname, align="left")
    sr = t.add_row().cells; setc(sr[0], "", align="left")
    for j, (r, m) in enumerate(T3):
        if rowname in r.index:
            setc(cr[j+1], f"{r.loc[rowname,'coef']:.3f}{star(r.loc[rowname,'p'])}")
            setc(sr[j+1], f"({r.loc[rowname,'se']:.3f})", size=8)
        else:
            setc(cr[j+1], ""); setc(sr[j+1], "")
rr = t.add_row().cells; setc(rr[0], "Observations", align="left", size=8)
for j, (r, m) in enumerate(T3):
    setc(rr[j+1], f"{int(m['N']):,}", size=8)
rr = t.add_row().cells; setc(rr[0], "R²", align="left", size=8)
for j, (r, m) in enumerate(T3):
    setc(rr[j+1], f"{m['r2']:.3f}", size=8)
note("Notes: Dependent variable is the evaluator’s self-reported perceived similarity to the target "
     "on the 0–10 scale (one observation per evaluator). Column 1 includes only demographic distance "
     "(standardized age gap and a same-gender indicator); column 2 adds matches on marital status, "
     "having two or more children, and income; column 3 adds self-reported general health and bodily "
     "pain. Heteroskedasticity-robust standard errors in parentheses. * p<0.05, ** p<0.01, "
     "*** p<0.001.")
doc.add_page_break()

# ---------- Table A7 ----------
title("Table A7. Moderation of the negativity bias by demographic and circumstance matches")
t = doc.add_table(rows=2, cols=6); t.alignment = WD_TABLE_ALIGNMENT.CENTER
h0 = t.rows[0].cells
setc(h0[0], "Dependent variable: ΔSWB", bold=True, align="left", size=8)
for j in range(4):
    setc(h0[j+1], f"({j+1})", bold=True)
setc(h0[5], "(5) Joint", bold=True)
h1 = t.rows[1].cells
setc(h1[0], "Similarity measure", ital=True, align="left", size=8)
for j, (_, lab) in enumerate(COMPS):
    setc(h1[j+1], lab, ital=True, size=8)
setc(h1[5], "All four matches", ital=True, size=8)


def a7_row(label, singles_name, joint_prefix):
    cr = t.add_row().cells; setc(cr[0], label, align="left")
    sr = t.add_row().cells; setc(sr[0], "", align="left")
    for j, (_, lab) in enumerate(COMPS):
        r, m = A7[lab]
        nm = singles_name
        setc(cr[j+1], f"{r.loc[nm,'coef']:.3f}{star(r.loc[nm,'p'])}")
        setc(sr[j+1], f"({r.loc[nm,'se']:.3f})", size=8)
    # joint column
    if joint_prefix is None:  # Negative shock (single 'Negative' term in joint model)
        setc(cr[5], f"{rj.loc['Negative','coef']:.3f}{star(rj.loc['Negative','p'])}")
        setc(sr[5], f"({rj.loc['Negative','se']:.3f})", size=8)
    else:
        setc(cr[5], ""); setc(sr[5], "")  # joint main/interaction shown implicitly via joint test


# Negative shock row (each single model's Negative coef; joint model's Negative in col 5)
cr = t.add_row().cells; setc(cr[0], "Negative shock", align="left")
sr = t.add_row().cells; setc(sr[0], "", align="left")
for j, (_, lab) in enumerate(COMPS):
    r, m = A7[lab]
    setc(cr[j+1], f"{r.loc['Negative','coef']:.3f}{star(r.loc['Negative','p'])}")
    setc(sr[j+1], f"({r.loc['Negative','se']:.3f})", size=8)
setc(cr[5], f"{rj.loc['Negative','coef']:.3f}{star(rj.loc['Negative','p'])}")
setc(sr[5], f"({rj.loc['Negative','se']:.3f})", size=8)

# Similarity term (main) row
cr = t.add_row().cells; setc(cr[0], "Similarity term", align="left")
sr = t.add_row().cells; setc(sr[0], "", align="left")
for j, (_, lab) in enumerate(COMPS):
    r, m = A7[lab]
    setc(cr[j+1], f"{r.loc['Sim','coef']:.3f}{star(r.loc['Sim','p'])}")
    setc(sr[j+1], f"({r.loc['Sim','se']:.3f})", size=8)
setc(cr[5], ""); setc(sr[5], "")

# Negative × Similarity term row
cr = t.add_row().cells; setc(cr[0], "Negative × Similarity term", align="left")
sr = t.add_row().cells; setc(sr[0], "", align="left")
for j, (_, lab) in enumerate(COMPS):
    r, m = A7[lab]
    setc(cr[j+1], f"{r.loc['NegxSim','coef']:.3f}{star(r.loc['NegxSim','p'])}")
    setc(sr[j+1], f"({r.loc['NegxSim','se']:.3f})", size=8)
setc(cr[5], ""); setc(sr[5], "")

# Observations
rr = t.add_row().cells; setc(rr[0], "Observations", align="left", size=8)
for j, (_, lab) in enumerate(COMPS):
    setc(rr[j+1], f"{int(A7[lab][1]['N']):,}", size=8)
setc(rr[5], f"{int(mj['N']):,}", size=8)

# Joint test row
rr = t.add_row().cells
setc(rr[0], "Joint test (4 interactions = 0)", align="left", size=8)
for j in range(4):
    setc(rr[j+1], "", size=8)
setc(rr[5], f"F(4,{Gj-1})={Fjoint:.2f}, p={pjoint:.2f}", size=8)

note("Notes: Dependent variable is the change in the target’s judged life satisfaction (post-shock "
     "minus baseline); unit of observation is evaluator × shock. Columns (1)–(4) define similarity "
     "based on whether the evaluator matches the target in marital status, having two or more "
     "children, income, and health, respectively. Column (5) includes all four similarity measures "
     "jointly; the joint test reports a Wald test that the four match × negative interactions are "
     "jointly zero. Cluster-robust standard errors (by evaluator) in parentheses. * p<0.05, "
     "** p<0.01, *** p<0.001.")

os.makedirs("output", exist_ok=True)
doc.save("output/06_tables.docx")
print("saved output/06_tables.docx")