"""
01_loss_asymmetry.py
Section 4.1 / Figure 2 — Third-person loss asymmetry.

Reproduces:
  - mean ΔSWB for negative shocks (-2.00, SD 1.42) and positive shocks (+0.82, SD 1.21)
  - magnitude ratio ~2.46 (reported as "roughly 2.5")
  - paired magnitude test on |ΔSWB| (t = 23.9, p < 0.001)
  - Figure 2 panel (a) distributions and panel (b) mean change by shock
"""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib as mpl

exec(open("00_data_prep.py").read())

df, subj = build_data()
sh = judgment_panel(df, subj).dropna(subset=["dswb", "neg"])

neg = sh.loc[sh["neg"] == 1, "dswb"]
pos = sh.loc[sh["neg"] == 0, "dswb"]

print("=== Section 4.1: Loss asymmetry ===")
print(f"Negative shocks: mean={neg.mean():.4f}  SD={neg.std():.4f}  N={len(neg)}")
print(f"Positive shocks: mean={pos.mean():.4f}  SD={pos.std():.4f}  N={len(pos)}")
print(f"Ratio of magnitudes (unrounded means): {abs(neg.mean())/abs(pos.mean()):.4f}")

# paired magnitude test on |ΔSWB| (within-participant: each rated both valences)
sh["absd"] = sh["dswb"].abs()
pair = sh.groupby(["SubjectID", "neg"])["absd"].mean().unstack().dropna()
tP, pP = stats.ttest_rel(pair[1], pair[0])
print(f"Paired magnitude test |ΔSWB| neg vs pos: mean {pair[1].mean():.3f} vs {pair[0].mean():.3f}")
print(f"  paired t = {tP:.2f}, p = {pP:.2e}, N pairs = {len(pair)}")

# ---- Figure 2 ----
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

mpl.rcParams.update({
    'font.family':'serif','font.serif':['DejaVu Serif'],
    'font.size':11,'axes.spines.top':False,'axes.spines.right':False,
    'axes.grid':True,'grid.alpha':0.25,'grid.linewidth':0.6,
    'figure.dpi':130,'savefig.dpi':200,'savefig.bbox':'tight',
})
NEG='#C1443C'; POS='#2E6E8E'

df = pd.read_stata("data/cleaneddta_panelall.dta", convert_categoricals=False)   # relative path
subj = df.sort_values('SubjectID').groupby('SubjectID',as_index=False).first()
bl = subj[['SubjectID','swb_bl']].rename(columns={'swb_bl':'baseline'}).dropna()
sh = df[df['ETPage_Code']==2].copy().merge(bl,on='SubjectID',how='left')
sh['dswb']=sh['swb_sk']-sh['baseline']
sh=sh.dropna(subset=['dswb','treat_p1shock'])
sh['neg']=sh['treat_p1shock_neg']
neg=sh[sh['neg']==1]['dswb']; pos=sh[sh['neg']==0]['dswb']

name={1:'Back pain\nworsened',2:'10% salary\ncut',3:'20% salary\ncut',4:'Demotion',
      5:'Promotion',6:'10% salary\nraise',7:'20% salary\nraise',8:'Back pain\nrecovery'}
sh['label']=sh['treat_p1shock'].map(name)

fig,axes=plt.subplots(1,2,figsize=(13.4,4.6))

ax=axes[0]
bins=np.arange(-8.25,8.5,0.5)
ax.hist(neg,bins=bins,color=NEG,alpha=0.6,edgecolor='white',linewidth=0.4,density=True)
ax.hist(pos,bins=bins,color=POS,alpha=0.6,edgecolor='white',linewidth=0.4,density=True)
ax.axvline(0,color='k',lw=1)
ax.axvline(neg.mean(),color=NEG,lw=1.6,ls='--')
ax.axvline(pos.mean(),color=POS,lw=1.6,ls='--')
ax.set_xlabel('Change in judged life satisfaction (post-shock − baseline)')
ax.set_ylabel('Density')
ax.set_title('(a) By shock valence',fontsize=12,loc='center',weight='bold',pad=14)
handlesA=[Patch(color=NEG,alpha=0.6,label='Negative shocks'),
          Patch(color=POS,alpha=0.6,label='Positive shocks'),
          Line2D([0],[0],color='k',lw=1,label='No change (0)'),
          Line2D([0],[0],color=NEG,lw=1.6,ls='--',label='Mean, negative shocks'),
          Line2D([0],[0],color=POS,lw=1.6,ls='--',label='Mean, positive shocks'),
          Line2D([0],[0],color='none',label='')]
ax.legend(handles=handlesA,frameon=False,loc='upper center',
          bbox_to_anchor=(0.5,-0.20),ncol=2,columnspacing=2.0,handletextpad=0.8)

ax=axes[1]
g=sh.groupby(['treat_p1shock','label','neg'])['dswb'].agg(['mean','std','count']).reset_index()
g['se']=g['std']/np.sqrt(g['count']); g=g.sort_values('mean')
colors=[NEG if n==1 else POS for n in g['neg']]
y=np.arange(len(g))
ax.barh(y,g['mean'],xerr=1.96*g['se'],color=colors,alpha=0.85,
        edgecolor='white',error_kw=dict(ecolor='#333',lw=1,capsize=2))
ax.axvline(0,color='k',lw=1)
ax.set_yticks(y); ax.set_yticklabels([l.replace('\n',' ') for l in g['label']])
ax.set_xlabel('Mean change in judged life satisfaction (95% CI)')
ax.set_title('(b) By individual shock',fontsize=12,loc='center',weight='bold',pad=14)
handlesB=[Patch(color=NEG,label='Negative'),Patch(color=POS,label='Positive')]
ax.legend(handles=handlesB,frameon=False,loc='upper center',
          bbox_to_anchor=(0.5,-0.20),ncol=2)

fig.subplots_adjust(wspace=0.75,bottom=0.30,top=0.88)

fig.savefig("output/figure2_loss_asymmetry.png")
print("saved output/figure2_loss_asymmetry.png")
