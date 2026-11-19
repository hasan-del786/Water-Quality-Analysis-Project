"""Builds Water_Quality_Analysis_Report.pdf. Run water_quality_analysis.py first.
Install: pip install reportlab pandas"""
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

comp = pd.read_csv("sample_compliance.csv")
src = pd.read_csv("source_summary.csv")
par = pd.read_csv("parameter_failures.csv")
worst = pd.read_csv("worst_samples.csv")
X = pd.read_csv("extra_stats.csv", index_col=0)["value"]
N, n_pass = len(comp), int((comp.status == "PASS").sum())
FAILCOLS = {"pH": "fail_pH", "TDS": "fail_TDS", "hardness": "fail_Hardness", "chloride": "fail_Chloride",
            "nitrate": "fail_Nitrate", "fluoride": "fail_Fluoride"}
def fails_of(source):
    g = comp[comp.Source == source]
    return [k for k, c in FAILCOLS.items() if g[c].sum() > 0]
row = lambda s: src[src.Source == s].iloc[0]
well, bore = row("Well"), row("Borehole")

ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["Normal"], fontName="Helvetica", fontSize=10, leading=14.5, spaceAfter=6)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=14, textColor=colors.HexColor("#1F4E79"), spaceBefore=10, spaceAfter=6)
title = ParagraphStyle("t", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=colors.HexColor("#1F4E79"))
sub = ParagraphStyle("s", parent=body, alignment=TA_CENTER, textColor=colors.HexColor("#444444"))
small = ParagraphStyle("sm", parent=body, fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"))
bullet = ParagraphStyle("bl", parent=body, leftIndent=14, bulletIndent=2, spaceAfter=3)
cap = ParagraphStyle("cap", parent=small, alignment=TA_CENTER, spaceAfter=10)

def table(rows, widths, fs=9):
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), fs), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3F8")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t

def footer(c, d):
    c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#666666"))
    c.drawString(2 * cm, 1.2 * cm, "Drinking-Water Quality Analysis - simulated data for learning and analysis")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {d.page}"); c.restoreState()

def img(f, w=14.5): return Image(f, width=w * cm, height=w * cm * 4.4 / 7.5)

S = [Spacer(1, 0.4 * cm), Paragraph("Drinking-Water Quality Analysis Using Python, SQL and Excel", title),
     Paragraph("Comparing five water sources with guideline limits for pH, TDS, hardness, chloride, nitrate and fluoride", sub),
     Paragraph("Environmental chemistry data-analysis project", sub), Spacer(1, 0.3 * cm)]

S += [Paragraph("1. Aim", h1),
      Paragraph(f"To check {N} drinking-water samples (6 each from bottled water, tap water, a river, a borehole and a well) against guideline limits, "
                "find which sources have samples that fail, and see which parameters cause the failures.", body),
      Paragraph("<b>Data note.</b> All values are <b>simulated for learning and analysis. They are not real measurements.</b> "
                "Each source was given a typical profile (mean and spread for each parameter); the values were drawn at random from "
                "normal distributions (seed 42) and rounded like laboratory results. The patterns found therefore reflect the profiles chosen, "
                "not the real water of any place.", body)]

S += [Paragraph("2. Methods", h1),
      Paragraph("<b>Tools.</b> Python (pandas) loads the CSV file into a SQLite database. SQL queries (file queries.sql) flag each sample and "
                "summarise the results. Python (matplotlib) draws the charts. Excel repeats the same calculations with live formulas "
                "(IF, SUM, COUNTIFS, AVERAGEIF), so the two tools can be checked against each other.", body),
      Paragraph("<b>Limits used</b> (commonly used reference values; check the standard that applies where you live):", body)]
lim = [["Parameter", "Limit used", "Basis"],
       ["pH", "6.5 to 8.5", "acceptable range"], ["TDS", "600 ppm", "above this, taste becomes poor (WHO)"],
       ["Total hardness", "300 ppm CaCO3", "common scale: very hard; not a health limit"],
       ["Chloride", "250 ppm", "taste threshold (WHO)"], ["Nitrate", "50 ppm as NO3", "WHO guideline value"],
       ["Fluoride", "1.5 ppm", "WHO guideline value"]]
S += [table(lim, [3.6*cm, 4*cm, 8.4*cm]), Spacer(1, 0.3 * cm),
      Paragraph("<b>Flags.</b> A sample fails a limit when its value is outside the limit (pH outside the range, the others above the limit). "
                "A sample <b>passes</b> only if it fails none of the six. ppm (parts per million) here means mg/L.", body),
      Paragraph("<b>SQL.</b> Four queries: <i>compliance</i> (one row per sample with 0/1 flags and PASS/FAIL), <i>source_summary</i> "
                "(GROUP BY source: averages and the share failing), <i>parameter_failures</i> (UNION ALL of counts) and <i>worst_samples</i> "
                "(ORDER BY failures, LIMIT 5).", body)]

S += [PageBreak(), Paragraph("3. Results", h1),
      Paragraph(f"<b>{n_pass} of {N} samples pass every limit; {N - n_pass} fail at least one.</b> Summary by source (from the SQL query):", body)]
t = [["Source", "n", "pH", "TDS", "Hardness", "Chloride", "Nitrate", "Fluoride", "Failing"]]
for r in src.itertuples():
    t.append([r.Source, r.n_samples, f"{r.mean_pH:.2f}", f"{r.mean_TDS:.0f}", f"{r.mean_Hardness:.0f}", f"{r.mean_Chloride:.0f}",
              f"{r.mean_Nitrate:.1f}", f"{r.mean_Fluoride:.2f}", f"{r.n_failing} of {r.n_samples}"])
S += [table(t, [2.4*cm, 1*cm, 1.4*cm, 1.6*cm, 2*cm, 2*cm, 1.8*cm, 2*cm, 2.2*cm]),
      Paragraph("Table 1. Mean values per source (ppm except pH).", cap),
      img("chart_tds_by_source.png", 13.5),
      Paragraph("Figure 1. Mean TDS by source with the 600 ppm limit.", cap),
      img("chart_failure_rate.png", 13.5),
      Paragraph("Figure 2. Share of samples in each source failing at least one limit.", cap)]

S += [PageBreak(), Paragraph("4. Interpretation", h1)]
pf = ", ".join(f"{r.parameter} ({r.n_fail})" for r in par.itertuples() if r.n_fail > 0)
pts = [
    f"<b>Well water is the problem source.</b> All {int(well.n_samples)} well samples fail at least one limit (failures seen: {', '.join(fails_of('Well'))}), "
    f"and its mean TDS ({well.mean_TDS:.0f} ppm) is above the 600 ppm limit.",
    f"<b>Borehole water is mixed.</b> {int(bore.n_failing)} of {int(bore.n_samples)} samples fail ({', '.join(fails_of('Borehole'))}). "
    f"Its average ({bore.mean_TDS:.0f} ppm TDS) passes, but individual samples do not, so a mean alone can hide failures.",
    "<b>Bottled, tap and river water all pass</b> in this dataset; bottled water has the lowest TDS, hardness, chloride, nitrate and fluoride.",
    f"<b>Which limits fail.</b> Counts of samples failing each limit: {pf}. No sample exceeds the chloride limit.",
    f"<b>Chloride and TDS move together</b> (r = {X.TDS_Chloride_r:.2f}, slope {X.TDS_Chloride_slope:.2f} ppm chloride per ppm TDS), "
    "as expected because chloride is one of the dissolved salts that make up TDS. Some borehole samples break the trend, "
    "which is consistent with TDS also including ions other than chloride.",
    "<b>Why these patterns appear.</b> They were built into the simulation, so they show that the code and formulas work, not that real wells are worse than real taps.",
]
S += [Paragraph(p, bullet, bulletText="•") for p in pts]
S += [img("chart_tds_vs_chloride.png", 11),
      Paragraph("Figure 3. Chloride against TDS for all 30 samples; dashed lines are the limits.", cap)]
S += [Paragraph("5. Limitations", h1)]
lims = ["The data are simulated; no water was tested.",
        "Only 6 samples per source, so percentages jump in steps of about 17 points and carry large uncertainty.",
        "Limits are generic reference values; a real assessment follows the local regulation and adds microbiological tests, lead, arsenic and others.",
        "Hardness and TDS limits are taste and use guidelines, not health limits."]
S += [Paragraph(p, bullet, bulletText="•") for p in lims]
S += [Paragraph("6. Files and reuse", h1),
      Paragraph("The zip contains the data generator, the SQL file, the analysis script, the SQLite database, the Excel workbook (sheets Inputs, Summary, Samples, Charts), "
                "the charts and this report. Edit water_samples.csv or the blue cells in Excel to analyse new data.", body),
      Paragraph("<b>Suggested CV / portfolio wording (accurate):</b> \"Drinking-water quality analysis (simulated dataset of 30 samples): loaded data into SQLite, "
                "wrote SQL queries (GROUP BY, CASE, UNION ALL) to flag samples against guideline limits, and rebuilt the checks with Excel formulas; "
                "visualised results with Python (pandas, matplotlib) and wrote a report.\"", body)]

S += [PageBreak(), Paragraph("Appendix. Simulated water samples and flags", h1)]
rows = [["ID", "Source", "pH", "TDS", "Hard.", "Chlor.", "Nitr.", "Fluor.", "Fails", "Status"]]
for r in comp.itertuples():
    rows.append([r.Sample_ID, r.Source, f"{r.pH:.2f}", f"{r.TDS_ppm:.0f}", f"{r.Hardness_ppm:.0f}", f"{r.Chloride_ppm:.0f}",
                 f"{r.Nitrate_ppm:.1f}", f"{r.Fluoride_ppm:.2f}", r.n_fail, r.status])
tb = table(rows, [1.4*cm, 2.2*cm, 1.3*cm, 1.3*cm, 1.4*cm, 1.4*cm, 1.4*cm, 1.4*cm, 1.2*cm, 1.6*cm], fs=7.5)
for i, r in enumerate(comp.itertuples(), 1):
    if r.status == "FAIL": tb.setStyle(TableStyle([("TEXTCOLOR", (9, i), (9, i), colors.HexColor("#C00000")), ("FONTNAME", (9, i), (9, i), "Helvetica-Bold")]))
S += [tb]

SimpleDocTemplate("Water_Quality_Analysis_Report.pdf", pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=1.8*cm,
                  bottomMargin=2*cm, title="Drinking-Water Quality Analysis Using Python, SQL and Excel",
                  author="Hasan Ali").build(S, onFirstPage=footer, onLaterPages=footer)
print("Saved Water_Quality_Analysis_Report.pdf")
