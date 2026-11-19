"""
Generates water_samples.csv: SIMULATED drinking-water test results for 30 samples (6 from each of 5 sources).
Each source has its own typical profile (mean and spread for pH, TDS, hardness, chloride, nitrate, fluoride);
values are drawn from normal distributions (seed 42), clipped to realistic minimums and rounded like lab results.
These are NOT real measurements.
Run: python generate_simulated_data.py
"""
import numpy as np
import pandas as pd

SEED, N_PER_SOURCE = 42, 6
PARAMS = ["pH", "TDS_ppm", "Hardness_ppm", "Chloride_ppm", "Nitrate_ppm", "Fluoride_ppm"]
DECIMALS = {"pH": 2, "TDS_ppm": 0, "Hardness_ppm": 0, "Chloride_ppm": 0, "Nitrate_ppm": 1, "Fluoride_ppm": 2}
# source: (code, {parameter: (mean, SD)})
PROFILES = {
    "Bottled":  ("B", {"pH": (7.2, 0.3), "TDS_ppm": (90, 25),   "Hardness_ppm": (45, 12),  "Chloride_ppm": (10, 4),   "Nitrate_ppm": (3, 1.5),  "Fluoride_ppm": (0.20, 0.08)}),
    "Tap":      ("T", {"pH": (7.4, 0.2), "TDS_ppm": (220, 40),  "Hardness_ppm": (120, 25), "Chloride_ppm": (40, 10),  "Nitrate_ppm": (8, 3),    "Fluoride_ppm": (0.40, 0.10)}),
    "River":    ("R", {"pH": (7.6, 0.4), "TDS_ppm": (340, 70),  "Hardness_ppm": (180, 35), "Chloride_ppm": (70, 20),  "Nitrate_ppm": (15, 6),   "Fluoride_ppm": (0.50, 0.20)}),
    "Borehole": ("H", {"pH": (7.8, 0.4), "TDS_ppm": (520, 120), "Hardness_ppm": (250, 50), "Chloride_ppm": (120, 40), "Nitrate_ppm": (22, 9),   "Fluoride_ppm": (1.30, 0.50)}),
    "Well":     ("W", {"pH": (7.0, 0.4), "TDS_ppm": (650, 150), "Hardness_ppm": (320, 60), "Chloride_ppm": (180, 50), "Nitrate_ppm": (38, 14),  "Fluoride_ppm": (0.90, 0.40)}),
}

if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    rows = []
    for source, (code, prof) in PROFILES.items():
        for k in range(1, N_PER_SOURCE + 1):
            row = {"Sample_ID": f"{code}{k:02d}", "Source": source}
            for p in PARAMS:
                mean, sd = prof[p]
                row[p] = round(max(rng.normal(mean, sd), 0.0), DECIMALS[p]) + 0.0
            rows.append(row)
    pd.DataFrame(rows).to_csv("water_samples.csv", index=False)
    print(f"Saved water_samples.csv ({len(rows)} samples)")
