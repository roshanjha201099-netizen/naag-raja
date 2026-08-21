import os
import pandas as pd

df = pd.read_csv(os.path.join("datasets", "metadata", "indian_snakes_coverage_report.csv"))

big_four = [
    "Naja naja",           # Spectacled Cobra
    "Daboia russelii",     # Russell's Viper
    "Bungarus caeruleus",  # Common Krait
    "Echis carinatus"      # Saw-scaled Viper
]

print("=" * 65)
print("BIG 4 VENOMOUS COVERAGE CHECK")
print("=" * 65)
for name in big_four:
    match = df[df["scientific_name"].str.contains(name, case=False, na=False)]
    for _, row in match.iterrows():
        print(f"{row['scientific_name']:<35} | {row['image_count']:>5} images | {row['coverage_status']}")
print("=" * 65)