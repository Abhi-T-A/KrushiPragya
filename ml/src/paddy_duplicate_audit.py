from pathlib import Path
from collections import defaultdict
import hashlib
import pandas as pd


# ==========================================
# Paths
# ==========================================

ROOT = Path("ml/data/paddy_raw")
TRAIN_DIR = ROOT / "train_images"
TEST_DIR = ROOT / "test_images"
CSV_PATH = ROOT / "train.csv"


# ==========================================
# Helper: file hash
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
print("KrushiSetu AI - Paddy Duplicate Audit")
print("==========================================\n")


# ==========================================
# Load labels
# ==========================================

df = pd.read_csv(CSV_PATH)

label_map = dict(
    zip(
        df["image_id"].astype(str),
        df["label"].astype(str)
    )
)


# ==========================================
# Collect TRAIN images
# ==========================================

train_images = [
    p
    for p in TRAIN_DIR.rglob("*")
    if p.is_file()
    and p.suffix.lower() in [".jpg", ".jpeg", ".png"]
]

print(f"Training images found : {len(train_images)}")


# ==========================================
# Hash TRAIN images
# ==========================================

print("\nHashing training images...")

train_hashes = defaultdict(list)

for index, image_path in enumerate(train_images, start=1):

    try:
        h = file_hash(image_path)
        train_hashes[h].append(image_path)

    except Exception as e:
        print(f"Hash error: {image_path} -> {e}")

    if index % 1000 == 0:
        print(f"Processed {index}/{len(train_images)}")


# ==========================================
# Duplicate groups
# ==========================================

duplicate_groups = [
    paths
    for paths in train_hashes.values()
    if len(paths) > 1
]

print("\n------------------------------------------")
print("TRAIN DUPLICATES")
print("------------------------------------------")

print(f"Unique hashes      : {len(train_hashes)}")
print(f"Duplicate groups   : {len(duplicate_groups)}")
print(
    f"Extra duplicate files : "
    f"{sum(len(group) - 1 for group in duplicate_groups)}"
)


# ==========================================
# Duplicate label conflicts
# ==========================================

conflicting_groups = []

for group in duplicate_groups:

    labels = set()

    for image_path in group:
        label = label_map.get(image_path.name)

        if label is not None:
            labels.add(label)

    if len(labels) > 1:
        conflicting_groups.append((group, labels))


print(f"Duplicate label conflicts : {len(conflicting_groups)}")


if conflicting_groups:

    print("\nWARNING: Duplicate images have different labels!")

    for group, labels in conflicting_groups[:10]:

        print("\nLabels:", labels)

        for image_path in group:
            print(
                f"  {image_path.name} -> "
                f"{label_map.get(image_path.name)}"
            )


# ==========================================
# Cross train/test leakage
# ==========================================

print("\n------------------------------------------")
print("TRAIN ↔ TEST LEAKAGE")
print("------------------------------------------")

test_images = [
    p
    for p in TEST_DIR.rglob("*")
    if p.is_file()
    and p.suffix.lower() in [".jpg", ".jpeg", ".png"]
]

print(f"Test images found : {len(test_images)}")
print("\nHashing test images...")


test_hashes = {}

for index, image_path in enumerate(test_images, start=1):

    try:
        h = file_hash(image_path)
        test_hashes[h] = image_path

    except Exception as e:
        print(f"Hash error: {image_path} -> {e}")

    if index % 1000 == 0:
        print(f"Processed {index}/{len(test_images)}")


# Hash overlap

train_hash_set = set(train_hashes.keys())
test_hash_set = set(test_hashes.keys())

overlap = train_hash_set & test_hash_set


print(f"\nTrain unique hashes : {len(train_hash_set)}")
print(f"Test unique hashes  : {len(test_hash_set)}")
print(f"Train/Test overlap  : {len(overlap)}")


if overlap:

    print("\nWARNING: TRAIN/TEST LEAKAGE FOUND!")

    for h in list(overlap)[:10]:

        print("\nTrain:")
        for p in train_hashes[h]:
            print(f"  {p}")

        print("Test:")
        print(f"  {test_hashes[h]}")


# ==========================================
# Final summary
# ==========================================

print("\n==========================================")
print("DUPLICATE / LEAKAGE SUMMARY")
print("==========================================")

print(f"Training images             : {len(train_images)}")
print(f"Unique training images      : {len(train_hashes)}")
print(f"Duplicate groups            : {len(duplicate_groups)}")
print(
    f"Extra duplicate files      : "
    f"{sum(len(group) - 1 for group in duplicate_groups)}"
)
print(f"Duplicate label conflicts   : {len(conflicting_groups)}")
print(f"Test images                 : {len(test_images)}")
print(f"Train/Test leakage groups   : {len(overlap)}")

print("\nAudit complete.")