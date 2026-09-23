from pathlib import Path
from collections import defaultdict
import hashlib
import shutil
import pandas as pd


# ==========================================
# Paths
# ==========================================

ROOT = Path("ml/data/paddy_raw")
TRAIN_DIR = ROOT / "train_images"
TEST_DIR = ROOT / "test_images"
CSV_PATH = ROOT / "train.csv"

OUTPUT_DIR = Path("ml/data/paddy_cleaned")
OUTPUT_TRAIN = OUTPUT_DIR / "train"


# ==========================================
# Helper
# ==========================================

def file_hash(path):
    hasher = hashlib.md5()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


# ==========================================
# Header
# ==========================================

print("\n==========================================")
print("KrushiSetu AI - Clean Paddy Dataset")
print("==========================================\n")


# ==========================================
# Load CSV
# ==========================================

df = pd.read_csv(CSV_PATH)

label_map = dict(
    zip(
        df["image_id"].astype(str),
        df["label"].astype(str)
    )
)


# ==========================================
# Collect training images
# ==========================================

train_images = [
    p
    for p in TRAIN_DIR.rglob("*")
    if p.is_file()
    and p.suffix.lower() in [".jpg", ".jpeg", ".png"]
]

print(f"Training images found : {len(train_images)}")


# ==========================================
# Hash training images
# ==========================================

print("\nHashing training images...")

train_hashes = defaultdict(list)

for image_path in train_images:

    h = file_hash(image_path)
    train_hashes[h].append(image_path)


print(f"Unique training images : {len(train_hashes)}")


# ==========================================
# Hash test images
# ==========================================

test_images = [
    p
    for p in TEST_DIR.rglob("*")
    if p.is_file()
    and p.suffix.lower() in [".jpg", ".jpeg", ".png"]
]

print(f"Test images found      : {len(test_images)}")

print("\nHashing test images...")

test_hashes = {}

for image_path in test_images:

    h = file_hash(image_path)
    test_hashes[h] = image_path


# ==========================================
# Find train/test leakage
# ==========================================

test_hash_set = set(test_hashes.keys())

leakage_hashes = set(train_hashes.keys()) & test_hash_set

print(f"\nTrain/Test leakage groups : {len(leakage_hashes)}")


# ==========================================
# Prepare output
# ==========================================

if OUTPUT_DIR.exists():

    print("\nRemoving previous paddy_cleaned directory...")

    shutil.rmtree(OUTPUT_DIR)


OUTPUT_TRAIN.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# Create clean dataset
# ==========================================

kept = 0
removed_duplicates = 0
removed_leakage = 0

kept_by_class = defaultdict(int)


for image_hash, paths in train_hashes.items():

    # --------------------------------------
    # Remove train/test leakage
    # --------------------------------------

    if image_hash in leakage_hashes:

        removed_leakage += len(paths)

        continue


    # --------------------------------------
    # Keep only ONE copy of duplicates
    # --------------------------------------

    source = paths[0]

    if len(paths) > 1:

        removed_duplicates += len(paths) - 1


    # --------------------------------------
    # Determine label
    # --------------------------------------

    label = label_map.get(source.name)

    if label is None:

        print(
            f"WARNING: No CSV label for {source.name}"
        )

        continue


    # --------------------------------------
    # Create class folder
    # --------------------------------------

    class_dir = OUTPUT_TRAIN / label

    class_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------
    # Copy image
    # --------------------------------------

    destination = class_dir / source.name

    shutil.copy2(
        source,
        destination
    )

    kept += 1
    kept_by_class[label] += 1


# ==========================================
# Save clean metadata
# ==========================================

clean_records = []

for label, count in sorted(kept_by_class.items()):

    clean_records.append(
        {
            "label": label,
            "count": count
        }
    )


clean_stats = pd.DataFrame(clean_records)

clean_stats.to_csv(
    OUTPUT_DIR / "class_counts.csv",
    index=False
)


# ==========================================
# Summary
# ==========================================

print("\n==========================================")
print("CLEANING SUMMARY")
print("==========================================")

print(f"Original training images : {len(train_images)}")
print(f"Unique training images   : {len(train_hashes)}")
print(f"Duplicate copies removed : {removed_duplicates}")
print(f"Leakage images removed   : {removed_leakage}")
print(f"Final clean images       : {kept}")

print("\nClass counts:")

for label, count in sorted(kept_by_class.items()):

    print(f"{label:<30} : {count}")


print("\nOutput:")
print(OUTPUT_TRAIN)

print("\nOriginal paddy_raw was NOT modified.")

print("\nClean dataset creation complete.")