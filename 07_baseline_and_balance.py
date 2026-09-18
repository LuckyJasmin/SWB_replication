"""
07_baseline_and_balance.py
Section 4.1 / Figure A1

Reproduces:
  Figure A1: distribution of judged baseline life satisfaction (0-10)
"""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib as mpl

exec(open("00_data_prep.py").read())
df, subj = build_data()
s = subj[subj["baseline0"].notna()].copy()

print("=== Figure A1: judged baseline life satisfaction (0-10) ===")
b = s["baseline0"]
print(f"Mean={b.mean():.3f} SD={b.std():.3f} median={b.median():.0f} N={len(b)}")

# gender / age effects on judged baseline (a treatment effect on the outcome)
tg, pg = stats.ttest_ind(s.loc[s["treat_female"] == 1, "baseline0"],
                         s.loc[s["treat_female"] == 0, "baseline0"], equal_var=False)
ta, pa = stats.ttest_ind(s.loc[s["treat_old"] == 1, "baseline0"],
                         s.loc[s["treat_old"] == 0, "baseline0"], equal_var=False)
print(f"Target gender: male={s.loc[s['treat_female']==0,'baseline0'].mean():.3f} "
      f"female={s.loc[s['treat_female']==1,'baseline0'].mean():.3f} t={tg:.2f} p={pg:.4f}")
print(f"Target age: young={s.loc[s['treat_old']==0,'baseline0'].mean():.3f} "
      f"old={s.loc[s['treat_old']==1,'baseline0'].mean():.3f} t={ta:.2f} p={pa:.4f}")

mpl.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"],
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "savefig.dpi": 200, "savefig.bbox": "tight"})
from matplotlib.lines import Line2D
GREY, LINE = "#8C8C8C", "#444444"
fig, ax = plt.subplots(figsize=(6.8, 4.6))
vals = np.arange(0, 11)
pct = [100 * (b == v).sum() / len(b) for v in vals]
ax.bar(vals, pct, color=GREY, edgecolor="white")
ax.axvline(b.mean(), color=LINE, lw=1.6, ls="--")
ax.set_xticks(vals)
ax.set_xlabel("Judged baseline life satisfaction (0-10)")
ax.set_ylabel("Percentage of evaluators (%)")
ax.legend(handles=[Line2D([0], [0], color=LINE, lw=1.6, ls="--", label="Mean")],
          frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16))
fig.subplots_adjust(bottom=0.2)
fig.savefig("output/figureA1_baseline_distribution.png")
print("saved output/figureA1_baseline_distribution.png")

