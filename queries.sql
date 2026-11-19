-- SQL queries used by water_quality_analysis.py (SQLite). Each block starts with "-- name: <query name>".
-- Limits below must match the Inputs sheet of the Excel workbook:
--   pH 6.5-8.5, TDS 600, hardness 300, chloride 250, nitrate 50, fluoride 1.5  (all in ppm = mg/L, except pH)

-- name: compliance
-- One row per sample: 1 = the sample fails that limit, 0 = passes; plus the number of failures and PASS/FAIL.
SELECT Sample_ID, Source, pH, TDS_ppm, Hardness_ppm, Chloride_ppm, Nitrate_ppm, Fluoride_ppm,
       (pH < 6.5 OR pH > 8.5)  AS fail_pH,
       (TDS_ppm > 600)         AS fail_TDS,
       (Hardness_ppm > 300)    AS fail_Hardness,
       (Chloride_ppm > 250)    AS fail_Chloride,
       (Nitrate_ppm > 50)      AS fail_Nitrate,
       (Fluoride_ppm > 1.5)    AS fail_Fluoride,
       (pH < 6.5 OR pH > 8.5) + (TDS_ppm > 600) + (Hardness_ppm > 300)
         + (Chloride_ppm > 250) + (Nitrate_ppm > 50) + (Fluoride_ppm > 1.5) AS n_fail,
       CASE WHEN (pH < 6.5 OR pH > 8.5) + (TDS_ppm > 600) + (Hardness_ppm > 300)
                 + (Chloride_ppm > 250) + (Nitrate_ppm > 50) + (Fluoride_ppm > 1.5) = 0
            THEN 'PASS' ELSE 'FAIL' END AS status
FROM samples
ORDER BY Source, Sample_ID;

-- name: source_summary
-- Average of every parameter for each source, and how many of its samples fail at least one limit.
SELECT c.Source,
       COUNT(*)                          AS n_samples,
       ROUND(AVG(c.pH), 2)               AS mean_pH,
       ROUND(AVG(c.TDS_ppm), 1)          AS mean_TDS,
       ROUND(AVG(c.Hardness_ppm), 1)     AS mean_Hardness,
       ROUND(AVG(c.Chloride_ppm), 1)     AS mean_Chloride,
       ROUND(AVG(c.Nitrate_ppm), 1)      AS mean_Nitrate,
       ROUND(AVG(c.Fluoride_ppm), 2)     AS mean_Fluoride,
       SUM(c.status = 'FAIL')            AS n_failing,
       ROUND(100.0 * SUM(c.status = 'FAIL') / COUNT(*), 1) AS pct_failing
FROM compliance c
GROUP BY c.Source
ORDER BY pct_failing DESC, mean_TDS DESC;

-- name: parameter_failures
-- How many of the 30 samples exceed each limit.
SELECT 'pH' AS parameter, SUM(fail_pH) AS n_fail FROM compliance
UNION ALL SELECT 'TDS',       SUM(fail_TDS)      FROM compliance
UNION ALL SELECT 'Hardness',  SUM(fail_Hardness) FROM compliance
UNION ALL SELECT 'Chloride',  SUM(fail_Chloride) FROM compliance
UNION ALL SELECT 'Nitrate',   SUM(fail_Nitrate)  FROM compliance
UNION ALL SELECT 'Fluoride',  SUM(fail_Fluoride) FROM compliance;

-- name: worst_samples
-- The five samples with the most failed limits (ties broken by highest TDS).
SELECT Sample_ID, Source, n_fail, TDS_ppm, Hardness_ppm, Chloride_ppm, Nitrate_ppm, Fluoride_ppm
FROM compliance
ORDER BY n_fail DESC, TDS_ppm DESC
LIMIT 5;
