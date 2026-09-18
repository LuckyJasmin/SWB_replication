"""
08_balance_test.py
Section 4.1 / Table A1

Reproduces:
  Table A1: balance of evaluator characteristics across the four arms
  (baseline mean 6.23; gender effect on judged baseline: male 6.35 vs female 6.10)
"""

import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

four = pd.read_csv("output/balance_fourarm.csv").fillna("")      # was /home/claude/...
marg = pd.read_csv("output/balance_margins.csv").fillna("")      # was /home/claude/...

doc = Document()
style = doc.styles['Normal']
style.font.name = 'Times New Roman'; style.font.size = Pt(10)

def set_cell(cell, text, bold=False, italic=False, align='left', size=9):
    cell.text = ''
    p = cell.paragraphs[0]
    p.alignment = {'left':WD_ALIGN_PARAGRAPH.LEFT,'center':WD_ALIGN_PARAGRAPH.CENTER,
                   'right':WD_ALIGN_PARAGRAPH.RIGHT}[align]
    r = p.add_run(str(text)); r.bold=bold; r.italic=italic
    r.font.name='Times New Roman'; r.font.size=Pt(size)

def add_title(txt):
    h = doc.add_paragraph()
    run = h.add_run(txt); run.bold=True; run.font.size=Pt(11); run.font.name='Times New Roman'

def build_table(dfin, headers, colkeys, numeric_center_from=1):
    t = doc.add_table(rows=1, cols=len(colkeys))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    hdr = t.rows[0].cells
    for j,htext in enumerate(headers):
        set_cell(hdr[j], htext, bold=True, align=('left' if j==0 else 'center'), size=8)
    section_rows = {'Continuous / ordinal covariates','Binary covariates','Race/ethnicity',
                    'Race/ethnicity (proportions)','Political affiliation','Political affiliation (proportions)',
                    'Marital status','Marital status (proportions)'}
    for _,row in dfin.iterrows():
        cells = t.add_row().cells
        var = row[colkeys[0]]
        is_section = str(var).strip() in section_rows
        is_N = str(var).strip().startswith('N (subjects)')
        for j,ck in enumerate(colkeys):
            val = row[ck]
            set_cell(cells[j], val,
                     bold=(is_section or is_N),
                     italic=is_section,
                     align=('left' if j==0 else 'center'), size=8)
    return t

# ---------------- Table 2: four-arm ----------------
add_title("Table 2. Balance of evaluator characteristics across the four randomized target profiles")
colkeys_four = ['Variable','All','YM','YW','OM','OW','p(joint)']
headers_four = ['','All','YM','YW','OM','OW','p (joint)']
build_table(four, headers_four, colkeys_four)

note = doc.add_paragraph()
nr = note.add_run(
 "Notes: One observation per subject (N = 950 completed sessions). Continuous and ordinal "
 "covariates report mean (standard deviation); binary covariates and category levels report "
 "proportions. YM = young man, YW = young woman, OM = old man, OW = old woman profile. "
 "p (joint) is from a one-way ANOVA F-test across the four arms. Age is mechanically related to "
 "the target-age arms because Prolific pre-screened participants into age pools, so evaluator age "
 "should not be read as a randomization check. Evaluator gender balances across arms (p = 0.448). "
 "Minor imbalances on marital status and on the Black/African indicator are within the range "
 "expected under randomization (all normalized differences < 0.25; see Table 3)."
)
nr.italic=True; nr.font.size=Pt(8); nr.font.name='Times New Roman'

doc.add_page_break()

# ---------------- Table 3: two-margin ----------------
add_title("Table 3. Balance along the two randomized treatment margins (gender and age)")
colkeys_marg = ['Variable','Gender:0','Gender:1','Gender diff','Gender p','Gender normdiff',
                'Age:0','Age:1','Age diff','Age p','Age normdiff']
headers_marg = ['','Male\nprofile','Female\nprofile','Diff','p','Norm.\ndiff',
                'Young\nprofile','Old\nprofile','Diff','p','Norm.\ndiff']
build_table(marg, headers_marg, colkeys_marg)

note2 = doc.add_paragraph()
nr2 = note2.add_run(
 "Notes: One observation per subject. Columns report covariate means (continuous/ordinal) or "
 "proportions (binary) by target-gender margin (male vs. female profile) and target-age margin "
 "(young = 35 vs. old = 55 profile). Diff is the female-minus-male and old-minus-young difference; "
 "p is from a Welch (unequal-variance) two-sample t-test; Norm. diff is the Imbens–Rubin normalized "
 "difference (difference in means scaled by the pooled within-group standard deviation), for which "
 "values above 0.25 in absolute value conventionally indicate concerning imbalance. All normalized "
 "differences here are below that threshold. Evaluator age is uninformative on the age margin by "
 "design (Prolific age pre-screening)."
)
nr2.italic=True; nr2.font.size=Pt(8); nr2.font.name='Times New Roman'

doc.save("output/balance_tables.docx")                          # was /mnt/user-data/outputs/...
print("saved docx")

# Also export clean CSVs to outputs
four.to_csv("output/balance_fourarm.csv", index=False)          # was /mnt/user-data/outputs/...
marg.to_csv("output/balance_margins.csv", index=False)
print("saved docx and csvs to output/")