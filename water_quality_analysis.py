"""
Drinking-Water Quality Analysis Using Python, SQL and Excel
-----------------------------------------------------------
Checks 30 water samples (5 sources x 6 samples) against guideline limits for pH, TDS, hardness, chloride, nitrate
and fluoride:
  1. loads water_samples.csv into a SQLite database (water_quality.db) with pandas,
  2. runs the SQL queries in queries.sql: compliance per sample, summary per source, failures per parameter, worst samples,
  3. exports result CSVs and three PNG charts (matplotlib),
  4. builds an Excel workbook with live formulas (limits, pass/fail flags, AVERAGEIF/COUNTIFS summary) and native charts.

DATA NOTE: all values are SIMULATED (see generate_simulated_data.py). They are NOT real measurements.
The guideline limits are commonly used reference values (WHO drinking-water guidelines and taste thresholds);
always check the standard that applies where you live.

Install:  pip install pandas numpy matplotlib openpyxl
Run:      python generate_simulated_data.py      (only if water_samples.csv is missing)
          python water_quality_analysis.py
"""
import re
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.formatting.rule import CellIsRule

# Guideline limits (must match queries.sql and the Inputs sheet)
LIMITS = [("pH, lower limit", 6.5, "0.0", "Acceptable range 6.5 to 8.5"),
          ("pH, upper limit", 8.5, "0.0", ""),
          ("TDS (ppm)", 600, "0", "Total dissolved solids; above about 600 ppm taste becomes poor (WHO), 1000 ppm is unacceptable"),
          ("Total hardness (ppm CaCO3)", 300, "0", "Common scale: above 300 ppm = very hard (not a health limit)"),
          ("Chloride (ppm)", 250, "0", "Taste threshold (WHO)"),
          ("Nitrate (ppm as NO3)", 50, "0", "WHO guideline value"),
          ("Fluoride (ppm)", 1.5, "0.0", "WHO guideline value")]
COLORS = {"Bottled": "#70AD47", "Tap": "#2E75B6", "River": "#7F7F7F", "Borehole": "#ED7D31", "Well": "#C00000"}

# ---------- 1. Load data into SQLite ----------
df = pd.read_csv("water_samples.csv")
con = sqlite3.connect("water_quality.db")
df.to_sql("samples", con, if_exists="replace", index=False)

# ---------- 2. Run the SQL queries ----------
blocks = re.split(r"^-- name: (\w+)\s*$", open("queries.sql", encoding="utf-8").read(), flags=re.M)
Q = {blocks[i]: blocks[i + 1].strip().rstrip(";") for i in range(1, len(blocks), 2)}
con.execute("DROP VIEW IF EXISTS compliance")
con.execute(f"CREATE VIEW compliance AS {Q['compliance']}")
comp = pd.read_sql("SELECT * FROM compliance", con)
src = pd.read_sql(Q["source_summary"], con)
par = pd.read_sql(Q["parameter_failures"], con)
worst = pd.read_sql(Q["worst_samples"], con)
con.close()

comp.to_csv("sample_compliance.csv", index=False)
src.to_csv("source_summary.csv", index=False)
par.assign(pct_failing=(par.n_fail / len(comp) * 100).round(1)).to_csv("parameter_failures.csv", index=False)
worst.to_csv("worst_samples.csv", index=False)
n_pass = int((comp.status == "PASS").sum())
print(src.to_string(index=False)); print(par.to_string(index=False)); print(worst.to_string(index=False))
print(f"Samples passing every limit: {n_pass} of {len(comp)}")

# ---------- 3. Charts ----------
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
order = list(src.sort_values("mean_TDS").Source)
sd = df.groupby("Source").TDS_ppm.std().reindex(order)
mean = df.groupby("Source").TDS_ppm.mean().reindex(order)
fig, ax = plt.subplots(figsize=(7.5, 4.4))
ax.bar(order, mean, yerr=sd, capsize=4, color=[COLORS[s] for s in order], width=0.6, zorder=2)
ax.axhline(600, color="#C00000", ls="--", lw=1.2, label="TDS limit used: 600 ppm", zorder=3)
for k, v in enumerate(mean): ax.text(k, v + sd.iloc[k] + 12, f"{v:.0f}", ha="center", fontsize=9)
ax.set(ylabel="Mean TDS (ppm), error bar = 1 SD", title="Total dissolved solids by water source", ylim=(0, 950))
ax.legend(fontsize=8, loc="upper left"); ax.grid(alpha=0.3, axis="y", zorder=0)
fig.tight_layout(); fig.savefig("chart_tds_by_source.png", dpi=200); plt.close(fig)

s2 = src.sort_values("pct_failing")
fig, ax = plt.subplots(figsize=(7.5, 4.4))
ax.barh(s2.Source, s2.pct_failing, color=[COLORS[s] for s in s2.Source], height=0.6, zorder=2)
for k, (p, nf, ns) in enumerate(zip(s2.pct_failing, s2.n_failing, s2.n_samples)):
    ax.text(p + 1.5, k, f"{p:.0f} %  ({nf} of {ns})", va="center", fontsize=9)
ax.set(xlabel="Samples failing at least one limit (%)", title="Share of samples failing a guideline limit", xlim=(0, 120))
ax.grid(alpha=0.3, axis="x", zorder=0)
fig.tight_layout(); fig.savefig("chart_failure_rate.png", dpi=200); plt.close(fig)

slope, intercept = np.polyfit(df.TDS_ppm, df.Chloride_ppm, 1)
r = np.corrcoef(df.TDS_ppm, df.Chloride_ppm)[0, 1]
fig, ax = plt.subplots(figsize=(7.5, 4.4))
for s, g in df.groupby("Source"):
    ax.plot(g.TDS_ppm, g.Chloride_ppm, "o", color=COLORS[s], ms=6, label=s, zorder=3)
xs = np.array([df.TDS_ppm.min(), df.TDS_ppm.max()])
ax.plot(xs, slope * xs + intercept, color="#444444", lw=1.3, label=f"fit: slope {slope:.2f}, r = {r:.2f}", zorder=2)
ax.axhline(250, color="#C00000", ls="--", lw=1, zorder=1); ax.axvline(600, color="#C00000", ls="--", lw=1, zorder=1)
ax.set(xlabel="TDS (ppm)", ylabel="Chloride (ppm)", title="Chloride rises with total dissolved solids")
ax.legend(fontsize=8, loc="upper left"); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig("chart_tds_vs_chloride.png", dpi=200); plt.close(fig)
pd.Series({"TDS_Chloride_r": r, "TDS_Chloride_slope": slope, "samples_passing": n_pass, "samples_total": len(comp)}).round(4).to_csv("extra_stats.csv", header=["value"])

# ---------- 4. Excel workbook (live formulas) ----------
F = "Arial"
base = Font(name=F); blue = Font(name=F, color="0000FF"); note = Font(name=F, italic=True, size=9)
hf, hfill = Font(name=F, bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1F4E79")
thin = Side(style="thin", color="999999"); box = Border(left=thin, right=thin, top=thin, bottom=thin)
ctr = Alignment(horizontal="center", vertical="center", wrap_text=True)
def header(ws, row, labels):
    for j, h in enumerate(labels, 1):
        c = ws.cell(row, j, h); c.font, c.fill, c.border, c.alignment = hf, hfill, box, ctr

wb = Workbook()
wi = wb.active; wi.title = "Inputs"
header(wi, 1, ["Guideline limit", "Value", "Note"])
for r_, (p, v, nf, t) in enumerate(LIMITS, 2):
    wi.cell(r_, 1, p).font = base; c = wi.cell(r_, 2, v); c.font, c.number_format = blue, nf; wi.cell(r_, 3, t).font = base
    for j in (1, 2, 3): wi.cell(r_, j).border = box
    wi.cell(r_, 2).alignment = Alignment(horizontal="center")
wi.cell(10, 1, "Legend: blue = inputs you can edit; black = formulas. Limits are commonly used reference values; check your local standard. All data are simulated.").font = note
for col, w in zip("ABC", [32, 10, 84]): wi.column_dimensions[col].width = w

wd = wb.create_sheet("Samples"); n = len(df); last = n + 1
header(wd, 1, ["Sample ID", "Source", "pH", "TDS (ppm)", "Hardness (ppm)", "Chloride (ppm)", "Nitrate (ppm)", "Fluoride (ppm)",
               "Fail pH", "Fail TDS", "Fail hardness", "Fail chloride", "Fail nitrate", "Fail fluoride", "Failures", "Status"])
fmts = ["@", "@", "0.00", "0", "0", "0", "0.0", "0.00"]
cols = ["Sample_ID", "Source", "pH", "TDS_ppm", "Hardness_ppm", "Chloride_ppm", "Nitrate_ppm", "Fluoride_ppm"]
for k in range(n):
    r_ = k + 2
    for j, (cn, nf) in enumerate(zip(cols, fmts), 1):
        v = df[cn].iloc[k]; v = v if isinstance(v, str) else float(v)
        c = wd.cell(r_, j, v); c.font, c.number_format = blue, nf
    wd.cell(r_, 9, f"=IF(OR(C{r_}<Inputs!$B$2,C{r_}>Inputs!$B$3),1,0)")
    wd.cell(r_, 10, f"=IF(D{r_}>Inputs!$B$4,1,0)")
    wd.cell(r_, 11, f"=IF(E{r_}>Inputs!$B$5,1,0)")
    wd.cell(r_, 12, f"=IF(F{r_}>Inputs!$B$6,1,0)")
    wd.cell(r_, 13, f"=IF(G{r_}>Inputs!$B$7,1,0)")
    wd.cell(r_, 14, f"=IF(H{r_}>Inputs!$B$8,1,0)")
    wd.cell(r_, 15, f"=SUM(I{r_}:N{r_})")
    wd.cell(r_, 16, f'=IF(O{r_}=0,"PASS","FAIL")')
    for j in range(1, 17):
        cc = wd.cell(r_, j); cc.border = box; cc.alignment = Alignment(horizontal="center")
        if j > 8: cc.font = base
wd.conditional_formatting.add(f"P2:P{last}", CellIsRule(operator="equal", formula=['"FAIL"'], fill=PatternFill("solid", bgColor="F8CBAD")))
wd.conditional_formatting.add(f"P2:P{last}", CellIsRule(operator="equal", formula=['"PASS"'], fill=PatternFill("solid", bgColor="C6E0B4")))
wd.cell(last + 3, 1, "Legend: blue = test results (edit these); black = formulas. 1 = limit exceeded. Data are simulated (seed 42), not real measurements.").font = note
for j, w in enumerate([10, 10, 7, 10, 12, 12, 12, 12, 8, 8, 10, 10, 10, 10, 9, 9], 1):
    wd.column_dimensions[wd.cell(1, j).column_letter].width = w
wd.row_dimensions[1].height = 32; wd.freeze_panes = "C2"

sm = wb.create_sheet("Summary", 1)
header(sm, 1, ["Source", "Samples", "Mean pH", "Mean TDS", "Mean hardness", "Mean chloride", "Mean nitrate", "Mean fluoride",
               "Samples failing", "% failing"])
S = "Samples!"; rng_ = lambda c: f"{S}${c}$2:${c}${last}"
sources = list(src.sort_values("pct_failing", ascending=False).Source)
for r_, s in enumerate(sources, 2):
    sm.cell(r_, 1, s)
    sm.cell(r_, 2, f"=COUNTIF({rng_('B')},A{r_})")
    for j, col in enumerate("CDEFGH", 3):
        sm.cell(r_, j, f"=AVERAGEIF({rng_('B')},$A{r_},{rng_(col)})")
    sm.cell(r_, 9, f'=COUNTIFS({rng_("B")},A{r_},{rng_("P")},"FAIL")')
    sm.cell(r_, 10, f"=I{r_}/B{r_}*100")
tot = len(sources) + 2
sm.cell(tot, 1, "All samples"); sm.cell(tot, 2, f"=SUM(B2:B{tot-1})")
for j, col in enumerate("CDEFGH", 3): sm.cell(tot, j, f"=AVERAGE({rng_(col)})")
sm.cell(tot, 9, f"=SUM(I2:I{tot-1})"); sm.cell(tot, 10, f"=I{tot}/B{tot}*100")
for r_ in range(2, tot + 1):
    for j, nf in enumerate(["@", "0", "0.00", "0.0", "0.0", "0.0", "0.0", "0.00", "0", "0.0"], 1):
        c = sm.cell(r_, j); c.font, c.border, c.number_format = base, box, nf; c.alignment = Alignment(horizontal="center")
    if r_ == tot:
        for j in range(1, 11): sm.cell(r_, j).font = Font(name=F, bold=True)
fr = tot + 2
header(sm, fr, ["Limit exceeded", "Samples", "% of samples"])
for k, (lab, col) in enumerate([("pH", "I"), ("TDS", "J"), ("Hardness", "K"), ("Chloride", "L"), ("Nitrate", "M"), ("Fluoride", "N")], 1):
    r_ = fr + k
    sm.cell(r_, 1, lab); sm.cell(r_, 2, f"=SUM({rng_(col)})"); sm.cell(r_, 3, f"=B{r_}/COUNTA({rng_('A')})*100")
    for j, nf in enumerate(["@", "0", "0.0"], 1):
        c = sm.cell(r_, j); c.font, c.border, c.number_format = base, box, nf; c.alignment = Alignment(horizontal="center")
sm.cell(fr + 8, 1, "Every value is a formula reading the 'Samples' and 'Inputs' sheets; results match the SQL queries. Data are simulated.").font = note
for j, w in enumerate([16, 10, 10, 11, 13, 13, 12, 13, 14, 11], 1): sm.column_dimensions[sm.cell(1, j).column_letter].width = w
sm.row_dimensions[1].height = 32

wc = wb.create_sheet("Charts")
def bar(title, col, yt, anchor):
    ch = BarChart(); ch.type = "col"; ch.title = title; ch.style = 10; ch.legend = None
    ch.add_data(Reference(sm, min_col=col, min_row=1, max_row=tot - 1), titles_from_data=True)
    ch.set_categories(Reference(sm, min_col=1, min_row=2, max_row=tot - 1))
    ch.y_axis.title = yt; ch.x_axis.delete = False; ch.y_axis.delete = False
    ch.width, ch.height = 18, 9; wc.add_chart(ch, anchor)
bar("Mean TDS by source (ppm)", 4, "ppm", "A1")
bar("Samples failing a limit (%)", 10, "%", "A21")
wb.save("water_quality_analysis.xlsx")
print("Saved CSVs, water_quality.db, 3 PNG charts, water_quality_analysis.xlsx")
