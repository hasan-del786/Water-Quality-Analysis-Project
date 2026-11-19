# Drinking-Water Quality Analysis Using Python, SQL and Excel

Checks 30 (simulated) drinking-water samples (6 each from bottled water, tap water, a river, a borehole and a well) against
guideline limits for pH, TDS, total hardness, chloride, nitrate and fluoride. Python loads the data into a SQLite database,
SQL queries flag each sample and summarise by source, and an Excel workbook repeats the checks with live formulas.
Also exports PNG charts and a PDF report.

**DATA NOTE: all values are simulated for learning and analysis, not real measurements.** Each source has a typical profile
(mean and spread per parameter); values are drawn at random (seed 42). The limits are commonly used reference values
(WHO guidelines and taste thresholds); check the standard that applies where you live.

## Files
| File | Purpose |
|---|---|
| generate_simulated_data.py | Creates water_samples.csv (5 source profiles + random variation) |
| water_samples.csv | Input: 30 samples x 6 parameters |
| queries.sql | The SQL: compliance flags, summary per source, failures per parameter, worst samples |
| water_quality_analysis.py | Main script: SQLite, queries, CSVs, charts, Excel |
| water_quality.db | SQLite database (tables/views: samples, compliance); open it with DB Browser for SQLite |
| water_quality_analysis.xlsx | Sheets: Inputs, Summary, Samples, Charts (all results are formulas) |
| sample_compliance.csv, source_summary.csv, parameter_failures.csv, worst_samples.csv, extra_stats.csv | Output tables |
| chart_tds_by_source.png, chart_failure_rate.png, chart_tds_vs_chloride.png | Figures |
| make_report_pdf.py / make_code_pdf.py | Build the PDF report / the report with the source code appended |
| Water_Quality_Analysis_Report.pdf | 4-page report |
| Water_Quality_Analysis_Report_with_Code.pdf | Same report plus the Python source |

## Run
    pip install -r requirements.txt
    python generate_simulated_data.py          # optional: regenerates the data
    python water_quality_analysis.py
    python make_report_pdf.py
    python make_code_pdf.py                    # optional
(sqlite3 is part of Python; nothing extra to install for SQL.)

## Key results
22 of 30 samples pass every limit. All 6 well samples fail (mean TDS 621 ppm); 2 of 6 borehole samples fail; bottled, tap and
river samples all pass. Limits exceeded: TDS 4 samples; pH, hardness, nitrate and fluoride 2 each; chloride none.
Chloride vs TDS: r = 0.80. The Excel summary matches the SQL summary exactly.

## Limits
Simulated data; only 6 samples per source; generic reference limits; no microbiology, metals or seasonal variation.
