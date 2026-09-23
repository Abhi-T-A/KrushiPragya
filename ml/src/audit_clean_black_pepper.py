from pathlib import Path
from PIL import Image
import hashlib
from collections import Counter

ROOT = Path("ml/data/black_pepper_cleaned")

print("=" * 70)
print("KRUSHISETU AI — FINAL CLEAN BLACK PEPPER AUDIT")
print("=" * 70)

files = [
    p for p in ROOT.rglob("*")
    if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
]

print(f"\nImages found: {len(files)}")

# ---------------------------------------------------------
# 1. CLASS COUNTS
# ---------------------------------------------------------
print("\n[1] Class counts")
print("-" * 60)

class_counts = {}

for class_dir in sorted([p for p in ROOT.iterdir() if p.is_dir()]):
    count = len([
        p for p in class_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ])

    class_counts[class_dir.name] = count
    print(f"{class_dir.name:<25} {count}")

print("-" * 60)
print(f"TOTAL{' ':<19} {len(files)}")

# ---------------------------------------------------------
# 2. IMAGE INTEGRITY
# ---------------------------------------------------------
print("\n[2] Image integrity")
print("-" * 60)

corrupt = 0
dimensions = Counter()

for path in files:
    try:
        with Image.open(path) as img:
            img.verify()

        with Image.open(path) as img:
            dimensions[img.size] += 1

    except Exception:
        corrupt += 1

print(f"Checked : {len(files)}")
print(f"Corrupt : {corrupt}")

# ---------------------------------------------------------
# 3. EXACT DUPLICATE CHECK
# ---------------------------------------------------------
print("\n[3] Exact duplicate check")
print("-" * 60)

hashes = []

for path in files:
    hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())

unique_hashes = len(set(hashes))
duplicate_groups = len(hashes) - unique_hashes

print(f"Unique hashes   : {unique_hashes}")
print(f"Duplicate extras: {duplicate_groups}")

# ---------------------------------------------------------
# 4. DIMENSIONS
# ---------------------------------------------------------
print("\n[4] Image dimensions")
print("-" * 60)

for dimension, count in dimensions.most_common():
    print(f"{dimension}: {count}")

# ---------------------------------------------------------
# FINAL RESULT
# ---------------------------------------------------------
print("\n" + "=" * 70)

if (
    len(files) == unique_hashes
    and corrupt == 0
):
    print("PASS — CLEAN BLACK PEPPER DATASET VERIFIED")
else:
    print("WARNING — DATASET NEEDS FURTHER REVIEW")

print("=" * 70)