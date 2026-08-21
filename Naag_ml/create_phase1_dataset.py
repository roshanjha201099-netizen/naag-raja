import os
import pandas as pd

# Paths
cov_path = os.path.join("datasets", "metadata", "indian_snakes_coverage_report.csv")
sc_path = os.path.join("datasets", "metadata", "snakeclef_metadata.csv")

cov_df = pd.read_csv(cov_path)
sc_df = pd.read_csv(sc_path)

# 1. Filter Phase 1 Species (>= 30 images)
phase1_taxa = cov_df[cov_df["image_count"] >= 30].copy()
phase1_out = os.path.join("datasets", "metadata", "phase1_species.csv")
phase1_taxa.to_csv(phase1_out, index=False)

# 2. Extract valid species/binomial names
valid_names = set(phase1_taxa["scientific_name"]).union(set(phase1_taxa["binomial_base"]))

# 3. Filter SnakeCLEF metadata down to only Phase 1 Indian snakes
species_col = 'binomial_name' if 'binomial_name' in sc_df.columns else ('scientific_name' if 'scientific_name' in sc_df.columns else 'species')
phase1_images_df = sc_df[sc_df[species_col].isin(valid_names)].copy()

# Add a clean label column mapped to ZSI taxonomy
phase1_images_df["label"] = phase1_images_df[species_col]

# Save filtered training image manifest
manifest_out = os.path.join("datasets", "metadata", "snakeclef_phase1_manifest.csv")
phase1_images_df.to_csv(manifest_out, index=False)

print("=" * 65)
print("PHASE 1 DATASET MANIFEST GENERATED")
print("=" * 65)
print(f"Phase 1 Classes (Taxa):        {len(phase1_taxa)}")
print(f"Total Filtered Training Images: {len(phase1_images_df):,}")
print(f"Saved Species List to:         {phase1_out}")
print(f"Saved Image Manifest to:        {manifest_out}")
print("=" * 65)