import os
import pandas as pd

# Paths
india_path = os.path.join("datasets", "metadata", "indian_snakes.csv")
sc_path = os.path.join("datasets", "metadata", "snakeclef_metadata.csv")

india_df = pd.read_csv(india_path)
sc_df = pd.read_csv(sc_path)

# Determine the species column
species_col = 'binomial_name' if 'binomial_name' in sc_df.columns else ('scientific_name' if 'scientific_name' in sc_df.columns else 'species')
sc_counts = sc_df[species_col].value_counts().to_dict()

# Extract binomial base name (Genus species) for subspecies matching
india_df['binomial_base'] = india_df['scientific_name'].apply(lambda x: " ".join(x.split()[:2]))

# Match priority: Exact scientific_name first, fallback to binomial_base
def get_count(row):
    exact = sc_counts.get(row['scientific_name'], 0)
    if exact > 0:
        return exact
    return sc_counts.get(row['binomial_base'], 0)

india_df['image_count'] = india_df.apply(get_count, axis=1)

# Tier categorization
def assign_status(count):
    if count >= 100: return "EXCELLENT (>=100)"
    elif count >= 30:  return "GOOD (30-99)"
    elif count >= 10:  return "LOW (10-29)"
    elif count > 0:   return "CRITICAL (1-9)"
    return "MISSING (0)"

india_df['coverage_status'] = india_df['image_count'].apply(assign_status)

# Save updated report
out_path = os.path.join("datasets", "metadata", "indian_snakes_coverage_report.csv")
india_df.sort_values(by="image_count", ascending=False).to_csv(out_path, index=False)

# Summary Display
print("=" * 65)
print("UPDATED INDIAN SNAKES COVERAGE (ZSI 2025 vs SnakeCLEF)")
print("=" * 65)
print(f"Total Target Taxa:     {len(india_df)}")
print(f"Taxa with Images (>0): {(india_df['image_count'] > 0).sum()} / {len(india_df)}")
print(f"Taxa with 0 Images:    {(india_df['image_count'] == 0).sum()} / {len(india_df)}")
print("-" * 65)
print("Coverage Breakdown by Tier:")
print(india_df["coverage_status"].value_counts().to_string())
print("-" * 65)

# Big 4 Specific Audit
print("BIG 4 AUDIT WITH TAXONOMIC MAPPING:")
big_four = ["Naja naja", "Daboia russelii", "Bungarus caeruleus", "Echis carinatus"]
for name in big_four:
    match = india_df[india_df["scientific_name"].str.contains(name, case=False, na=False)]
    for _, row in match.iterrows():
        print(f"  {row['scientific_name']:<35} | {row['image_count']:>5} images | {row['coverage_status']}")
print("=" * 65)