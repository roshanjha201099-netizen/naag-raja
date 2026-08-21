import os
import pandas as pd
from sklearn.model_selection import train_test_split

manifest_path = os.path.join("datasets", "metadata", "snakeclef_phase1_manifest.csv")
df = pd.read_csv(manifest_path)

# Map labels to unique integers (0 to N-1)
unique_classes = sorted(df["label"].unique())
class_to_idx = {cls: idx for idx, cls in enumerate(unique_classes)}
df["target"] = df["label"].map(class_to_idx)

# Save class-to-index mapping for inference
class_map_df = pd.DataFrame(list(class_to_idx.items()), columns=["class_name", "class_id"])
class_map_df.to_csv(os.path.join("datasets", "metadata", "class_mapping.csv"), index=False)

# Stratified 80/20 train/val split
train_df, val_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
    stratify=df["target"]
)

train_path = os.path.join("datasets", "metadata", "phase1_train.csv")
val_path = os.path.join("datasets", "metadata", "phase1_val.csv")

train_df.to_csv(train_path, index=False)
val_df.to_csv(val_path, index=False)

print("=" * 60)
print("PHASE 1 STRATIFIED DATA SPLIT")
print("=" * 60)
print(f"Total Phase 1 Classes: {len(unique_classes)}")
print(f"Training Samples:      {len(train_df):,} ({len(train_df)/len(df)*100:.1f}%)")
print(f"Validation Samples:    {len(val_df):,} ({len(val_df)/len(df)*100:.1f}%)")
print(f"Class mapping saved:   datasets/metadata/class_mapping.csv")
print("=" * 60)