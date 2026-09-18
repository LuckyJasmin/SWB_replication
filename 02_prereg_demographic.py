"""
02_prereg_demographic.py
Writes the pre-registered demographic-similarity tables to a single Word file:
  output/02_prereg_tables.docx
    Table 1  — H1 (ΔSWB) and H2 (allocation)
    Table A2 — H3 (attention)
    Table A3 — H4 (severity three-way interaction)
    Table A4 — FDR-adjusted p-values and JZS Bayes factors

Run from inside the replication/ folder:  python 02_tables.py
Requires: python-docx  (pip install python-docx)
"""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.integrate import quad
import math
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from olstools import ols_cluster

exec(open("00_data_prep.py").read())


def star(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""


# ============================================================
# 1. ESTIMATION
# ============================================================
df, subj = build_data()
sh = judgment_panel(df, subj)
al = allocation_panel(df, subj)
SIMS = [("same_gender", "Same gender"), ("age_gap_z", "Age gap (z)")]

# ---- Table 1: H1 (common sample across both columns) ----
h1_sample = sh.dropna(subset=["dswb", "neg", "same_gender", "age_gap_z"]).copy()
H1 = {}
for sv, lab in SIMS:
    d = h1_sample.copy()
    d["int"] = d["neg"] * d[sv]
    X = np.column_stack([np.ones(len(d)), d["neg"], d[sv], d["int"]])
    H1[lab] = ols_cluster(d["dswb"].values, X, d["SubjectID"].values,
                          ["const", "Negative", lab, f"Negative x {lab}"])

# ---- Table 1: H2 (common sample) ----
for s in ["cut10", "cut20", "demote"]:
    al[f"sk_{s}"] = (al["shock"] == s).astype(float)
SK = ["sk_cut10", "sk_cut20", "sk_demote"]
h2_sample = al.dropna(subset=["alloc", "same_gender", "age_gap_z"] + SK).copy()
H2 = {}
for sv, lab in SIMS:
    d = h2_sample.copy()
    X = np.column_stack([np.ones(len(d))] + [d[s].values for s in SK] + [d[sv].values])
    H2[lab] = ols_cluster(d["alloc"].values, X, d["SubjectID"].values, ["const"] + SK + [lab])

# ---- Table A2: H3 (attention) ----
ctx = ["age", "gender", "cld", "fml", "income", "health"]
sh["fix_context"] = sh[[f"fix_ttldrt_{e}" for e in ctx]].sum(axis=1)
sh["fix_shock"] = sh["fix_ttldrt_sk"]
sh["l_fix_context"] = np.log1p(sh["fix_context"])
sh["l_fix_shock"] = np.log1p(sh["fix_shock"])
H3 = {}
for dv, dvlab in [("l_fix_context", "Contextual profile"), ("l_fix_shock", "Shock text")]:
    for sv, lab in SIMS:
        d = sh.dropna(subset=[dv, "neg", sv]).copy()
        X = np.column_stack([np.ones(len(d)), d["neg"], d[sv]])
        H3[(dvlab, lab)] = ols_cluster(d[dv].values, X, d["SubjectID"].values,
                                       ["const", "Negative", lab])

# ---- Table A3: H4 (severity three-way, income shocks, common sample) ----
inc = sh[sh["treat_p1shock"].isin([2, 3, 6, 7])].copy()
inc["severe"] = inc["treat_p1shock"].isin([3, 7]).astype(float)
h4_sample = inc.dropna(subset=["dswb", "neg", "same_gender", "age_gap_z"]).copy()
H4 = {}
for sv, lab in SIMS:
    d = h4_sample.copy()
    d["ns"] = d["neg"] * d[sv]; d["nsev"] = d["neg"] * d["severe"]
    d["ssev"] = d[sv] * d["severe"]; d["triple"] = d["neg"] * d[sv] * d["severe"]
    cols = [np.ones(len(d)), d["neg"], d[sv], d["severe"], d["ns"], d["nsev"], d["ssev"], d["triple"]]
    names = ["const", "Negative", lab, "Severe", f"Neg×{lab}", "Neg×Severe",
             f"{lab}×Severe", f"Neg×{lab}×Severe"]
    H4[lab] = ols_cluster(d["dswb"].values, np.column_stack(cols), d["SubjectID"].values, names)

# ---- Table A4: FDR + Bayes factors ----
def bf01_from_t(t, n, r=0.707):
    dfree = n - 1
    def integrand(g):
        return ((1 + n*g*r**2)**(-0.5) *
                (1 + t**2/((1+n*g*r**2)*dfree))**(-(dfree+1)/2) *
                (2*math.pi)**(-0.5)*g**(-1.5)*math.exp(-1/(2*g)))
    num, _ = quad(integrand, 1e-8, np.inf)
    denom = (1 + t**2/dfree)**(-(dfree+1)/2)
    return 1/(num/denom)

primary = [
    ("H1 same-gender × neg", H1["Same gender"][0].loc["Negative x Same gender", "p"]),
    ("H1 age-gap × neg",     H1["Age gap (z)"][0].loc["Negative x Age gap (z)", "p"]),
    ("H2 same-gender",       H2["Same gender"][0].loc["Same gender", "p"]),
    ("H2 age-gap",           H2["Age gap (z)"][0].loc["Age gap (z)", "p"]),
    ("H3 same-gender (ctx)", H3[("Contextual profile", "Same gender")][0].loc["Same gender", "p"]),
    ("H3 age-gap (ctx)",     H3[("Contextual profile", "Age gap (z)")][0].loc["Age gap (z)", "p"]),
    ("H4 same-gender triple", H4["Same gender"][0].loc["Neg×Same gender×Severe", "p"]),
    ("H4 age-gap triple",     H4["Age gap (z)"][0].loc["Neg×Age gap (z)×Severe", "p"]),
]
labels = [x[0] for x in primary]; pvals = np.array([x[1] for x in primary])
order = np.argsort(pvals); m_t = len(pvals)
bh = pvals[order] * m_t / np.arange(1, m_t + 1)
bh_adj = np.minimum.accumulate(bh[::-1])[::-1]
adj = np.empty(m_t); adj[order] = np.clip(bh_adj, 0, 1)
FDR = {labels[i]: (pvals[i], adj[i]) for i in range(m_t)}
BF = {}
for key, res, name in [("H1 same-gender × neg", H1["Same gender"], "Negative x Same gender"),
                       ("H1 age-gap × neg", H1["Age gap (z)"], "Negative x Age gap (z)"),
                       ("H2 same-gender", H2["Same gender"], "Same gender"),
                       ("H2 age-gap", H2["Age gap (z)"], "Age gap (z)")]:
    r, m = res
    t = r.loc[name, "coef"] / r.loc[name, "se"]
    BF[key] = bf01_from_t(t, m["G"])

# ============================================================
# 2. WORD OUTPUT
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


def cs(res, name):
    r, m = res
    if name in r.index:
        return f"{r.loc[name,'coef']:.3f}{star(r.loc[name,'p'])}", f"({r.loc[name,'se']:.3f})"
    return "", ""


# ---------- Table 1 ----------
title("Table 1. Pre-registered tests of H1 and H2")
t = doc.add_table(rows=2, cols=5); t.alignment = WD_TABLE_ALIGNMENT.CENTER
h0 = t.rows[0].cells
setc(h0[0], "", bold=True, align="left")
setc(h0[1], "H1: ΔSWB", bold=True); setc(h0[2], "H1: ΔSWB", bold=True)
setc(h0[3], "H2: Allocation", bold=True); setc(h0[4], "H2: Allocation", bold=True)
h1r = t.rows[1].cells
setc(h1r[0], "Similarity measure", ital=True, align="left", size=8)
setc(h1r[1], "Same gender", ital=True, size=8); setc(h1r[2], "Age gap (z)", ital=True, size=8)
setc(h1r[3], "Same gender", ital=True, size=8); setc(h1r[4], "Age gap (z)", ital=True, size=8)

def pair_row(label, getters):
    cr = t.add_row().cells; setc(cr[0], label, align="left")
    sr = t.add_row().cells; setc(sr[0], "", align="left")
    for j, gtr in enumerate(getters):
        c, s = gtr
        setc(cr[j+1], c); setc(sr[j+1], s, size=8)

pair_row("Negative shock",
         [cs(H1["Same gender"], "Negative"), cs(H1["Age gap (z)"], "Negative"), ("", ""), ("", "")])
pair_row("Similarity (main)",
         [cs(H1["Same gender"], "Same gender"), cs(H1["Age gap (z)"], "Age gap (z)"),
          cs(H2["Same gender"], "Same gender"), cs(H2["Age gap (z)"], "Age gap (z)")])
pair_row("Similarity × Negative",
         [cs(H1["Same gender"], "Negative x Same gender"),
          cs(H1["Age gap (z)"], "Negative x Age gap (z)"), ("", ""), ("", "")])
rr = t.add_row().cells; setc(rr[0], "Shock-severity dummies", align="left", size=8)
setc(rr[1], "—", size=8); setc(rr[2], "—", size=8); setc(rr[3], "Yes", size=8); setc(rr[4], "Yes", size=8)
rr = t.add_row().cells; setc(rr[0], "Observations", align="left", size=8)
for j, res in enumerate([H1["Same gender"], H1["Age gap (z)"], H2["Same gender"], H2["Age gap (z)"]]):
    setc(rr[j+1], f"{int(res[1]['N']):,}", size=8)
rr = t.add_row().cells; setc(rr[0], "Participants", align="left", size=8)
for j, res in enumerate([H1["Same gender"], H1["Age gap (z)"], H2["Same gender"], H2["Age gap (z)"]]):
    setc(rr[j+1], f"{int(res[1]['G'])}", size=8)
note("Notes: Columns 1–2 estimate H1 on judged life satisfaction (dependent variable ΔSWB); the "
     "coefficient of interest is Similarity × Negative. Columns 3–4 estimate H2 on the support "
     "allocation (dependent variable = amount of $100 to the target). Both H1 columns and both H2 "
     "columns use a common estimation sample. Cluster-robust standard errors (by participant) in "
     "parentheses. * p<0.05, ** p<0.01, *** p<0.001.")
doc.add_page_break()

# ---------- Table A2 ----------
title("Table A2. Pre-registered test of H3")
t = doc.add_table(rows=1, cols=3); t.alignment = WD_TABLE_ALIGNMENT.CENTER
h = t.rows[0].cells
setc(h[0], "Similarity measure", bold=True, align="left")
setc(h[1], "Contextual-profile fixation", bold=True, size=9)
setc(h[2], "Shock-text fixation", bold=True, size=9)
for sv, lab in SIMS:
    cr = t.add_row().cells; setc(cr[0], lab, align="left")
    rc, mc = H3[("Contextual profile", lab)]
    rs, ms = H3[("Shock text", lab)]
    setc(cr[1], f"{rc.loc[lab,'coef']:.3f}{star(rc.loc[lab,'p'])} ({rc.loc[lab,'se']:.3f})", size=9)
    setc(cr[2], f"{rs.loc[lab,'coef']:.3f}{star(rs.loc[lab,'p'])} ({rs.loc[lab,'se']:.3f})", size=9)
rr = t.add_row().cells; setc(rr[0], "Observations", align="left", size=8)
setc(rr[1], f"{int(H3[('Contextual profile','Same gender')][1]['N']):,}", size=8)
setc(rr[2], f"{int(H3[('Shock text','Same gender')][1]['N']):,}", size=8)
note("Notes: Each cell is the coefficient on the similarity measure from a regression of log "
     "fixation duration on the negative-shock indicator and the similarity measure; cluster-robust "
     "standard errors in parentheses. * p<0.05, ** p<0.01, *** p<0.001.")
doc.add_page_break()

# ---------- Table A3 ----------
title("Table A3. Pre-registered test of H4")
t = doc.add_table(rows=1, cols=3); t.alignment = WD_TABLE_ALIGNMENT.CENTER
h = t.rows[0].cells
setc(h[0], "", bold=True, align="left"); setc(h[1], "Same gender", bold=True); setc(h[2], "Age gap (z)", bold=True)
rowspec = [("Negative shock", "Negative"), ("Similarity (main)", None), ("Severe", "Severe"),
           ("Similarity × Negative", None), ("Negative × Severe", "Neg×Severe"),
           ("Similarity × Severe", None), ("Similarity × Negative × Severe", None)]
def h4key(lab, disp):
    return {"Similarity (main)": lab, "Similarity × Negative": f"Neg×{lab}",
            "Similarity × Severe": f"{lab}×Severe",
            "Similarity × Negative × Severe": f"Neg×{lab}×Severe"}.get(disp)
for disp, fixed in rowspec:
    cr = t.add_row().cells; setc(cr[0], disp, align="left")
    sr = t.add_row().cells; setc(sr[0], "", align="left")
    for j, lab in enumerate(["Same gender", "Age gap (z)"]):
        key = fixed if fixed else h4key(lab, disp)
        c, s = cs(H4[lab], key)
        setc(cr[j+1], c); setc(sr[j+1], s, size=8)
rr = t.add_row().cells; setc(rr[0], "Observations", align="left", size=8)
setc(rr[1], f"{int(H4['Same gender'][1]['N']):,}", size=8)
setc(rr[2], f"{int(H4['Age gap (z)'][1]['N']):,}", size=8)
note("Notes: Estimated on the four income shocks (10% and 20% salary cut/raise). Severe = 20% "
     "change; moderate = 10% change. The coefficient of interest for H4 is Similarity × Negative × "
     "Severe. Cluster-robust standard errors in parentheses. * p<0.05, ** p<0.01, *** p<0.001.")
doc.add_page_break()

# ---------- Table A4 ----------
title("Table A4. Multiple-comparison correction and Bayesian evidence")
t = doc.add_table(rows=1, cols=4); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, txt in enumerate(["Test", "p", "FDR-adjusted p", "BF01"]):
    setc(t.rows[0].cells[j], txt, bold=True, align=("left" if j == 0 else "center"), size=9)
order_keys = ["H1 same-gender × neg", "H1 age-gap × neg", "H2 same-gender", "H2 age-gap",
              "H3 same-gender (ctx)", "H3 age-gap (ctx)", "H4 same-gender triple", "H4 age-gap triple"]
for k in order_keys:
    praw, padj = FDR[k]
    cr = t.add_row().cells; setc(cr[0], k, align="left", size=9)
    setc(cr[1], f"{praw:.3f}", size=9); setc(cr[2], f"{padj:.3f}", size=9)
    setc(cr[3], f"{BF[k]:.1f}" if k in BF else "—", size=9)
note("Notes: FDR-adjusted p-values use the Benjamini–Hochberg procedure across the eight primary "
     "H1–H4 tests. BF01 is the JZS Bayes factor (Cauchy prior, r = 0.707) quantifying evidence for "
     "the null relative to the alternative; values above 3 and 10 denote moderate and strong "
     "evidence for the null.")

import os
os.makedirs("output", exist_ok=True)
doc.save("output/02_prereg_tables.docx")
print("saved output/02_prereg_tables.docx")