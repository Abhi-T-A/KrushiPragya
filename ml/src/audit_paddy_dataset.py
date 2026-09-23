from pathlib import Path
from PIL import Image
import pandas as pd
from collections import Counter
import hashlib


# ==============================
# Paths
# ==============================

ROOT = Path("ml/data/paddy_raw")
TRAIN_DIR = ROOT / "train_images"
CSV_PATH = ROOT / "train.csv"


# ==============================
# Load CSV
# ==============================

print("\n========================================")
print("KrushiSetu AI - Paddy Dataset Audit")
print("========================================\n")

df = pd.read_csv(CSV_PATH)

print("CSV columns:")
print(list(df.columns))

print(f"\nCSV labelled images : {len(df)}")
print(f"CSV classes         : {df['label'].nunique()}")


# ==============================
# Class distribution
# ==============================

print("\n----------------------------------------")
print("CLASS DISTRIBUTION")
print("----------------------------------------")

class_counts = df["label"].value_counts().sort_index()

for label, count in class_counts.items():
    print(f"{label:<30} : {count}")


# ==============================
# CSV ↔ Folder integrity
# ==============================

print("\n----------------------------------------")
print("CSV ↔ IMAGE INTEGRITY")
print("----------------------------------------")

csv_images = set(df["image_id"].astype(str))

folder_images = set()

for class_dir in TRAIN_DIR.iterdir():

    if not class_dir.is_dir():
        continue

    for image in class_dir.iterdir():

        if image.is_file():
            folder_images.add(image.name)

missing = csv_images - folder_images
extra = folder_images - csv_images

print(f"CSV images       : {len(csv_images)}")
print(f"Folder images    : {len(folder_images)}")
print(f"Missing images   : {len(missing)}")
print(f"Extra images     : {len(extra)}")

if missing:
    print("\nMissing examples:")
    for name in sorted(missing)[:10]:
        print(name)

if extra:
    print("\nExtra examples:")
    for name in sorted(extra)[:10]:
        print(name)


# ==============================
# Folder label verification
# ==============================

print("\n----------------------------------------")
print("FOLDER LABEL VERIFICATION")
print("----------------------------------------")

csv_label_map = dict(
    zip(
        df["image_id"].astype(str),
        df["label"].astype(str)
    )
)

label_mismatches = []

for class_dir in TRAIN_DIR.iterdir():

    if not class_dir.is_dir():
        continue

    folder_label = class_dir.name

    for image in class_dir.iterdir():

        if not image.is_file():
            continue

        csv_label = csv_label_map.get(image.name)

        if csv_label is None:
            continue

        if csv_label != folder_label:
            label_mismatches.append(
                (image.name, csv_label, folder_label)
            )

print(f"Label mismatches : {len(label_mismatches)}")

if label_mismatches:
    print("\nExamples:")
    for item in label_mismatches[:10]:
        print(item)


# ==============================
# Image integrity
# ==============================

print("\n----------------------------------------")
print("IMAGE INTEGRITY CHECK")
print("----------------------------------------")

image_files = []

for class_dir in TRAIN_DIR.iterdir():

    if not class_dir.is_dir():
        continue

    for image in class_dir.iterdir():

        if image.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            image_files.append(image)

bad_images = []

for index, image_path in enumerate(image_files, start=1):

    try:
        with Image.open(image_path) as img:
            img.verify()

    except Exception:
        bad_images.append(str(image_path))

    if index % 1000 == 0:
        print(f"Checked {index}/{len(image_files)}")


print(f"\nImages checked : {len(image_files)}")
print(f"Corrupt images : {len(bad_images)}")

if bad_images:
    print("\nCorrupt images:")
    for image in bad_images[:20]:
        print(image)


# ==============================
# Duplicate audit
# ==============================

print("\n----------------------------------------")
print("DUPLICATE IMAGE AUDIT")
print("----------------------------------------")

hash_map = {}

for index, image_path in enumerate(image_files, start=1):

    try:

        with open(image_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        hash_map.setdefault(file_hash, []).append(image_path)

    except Exception:
        pass

duplicate_groups = [
    paths
    for paths in hash_map.values()
    if len(paths) > 1
]

duplicate_files = sum(
    len(paths) - 1
    for paths in duplicate_groups
)

print(f"Unique image hashes : {len(hash_map)}")
print(f"Duplicate groups    : {len(duplicate_groups)}")
print(f"Extra duplicate files : {duplicate_files}")


# ==============================
# Summary
# ==============================

print("\n========================================")
print("AUDIT SUMMARY")
print("========================================")

print(f"Total CSV images       : {len(csv_images)}")
print(f"Total folder images    : {len(folder_images)}")
print(f"Missing images         : {len(missing)}")
print(f"Extra images           : {len(extra)}")
print(f"Label mismatches       : {len(label_mismatches)}")
print(f"Corrupt images         : {len(bad_images)}")
print(f"Duplicate groups       : {len(duplicate_groups)}")
print(f"Extra duplicate files  : {duplicate_files}")

print("\nAudit complete.")