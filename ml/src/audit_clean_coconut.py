from pathlib import Path
from PIL import Image, ImageFile
from collections import Counter
import hashlib

ImageFile.LOAD_TRUNCATED_IMAGES = False

ROOT = Path("ml/data/coconut_cleaned")

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

print("=" * 70)
print("KRUSHISETU AI — FINAL CLEAN COCONUT AUDIT")
print("=" * 70)

files = []

# ---------------------------------------------------------
# COLLECT FILES
# ---------------------------------------------------------

for class_dir in sorted(ROOT.iterdir()):

    if not class_dir.is_dir():
        continue

    for path in class_dir.rglob("*"):

        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
            files.append(path)

print(f"\nImages found: {len(files)}")

# ---------------------------------------------------------
# CLASS COUNTS
# ---------------------------------------------------------

print("\n[1] Class counts")
print("-" * 70)

class_counts = Counter()

for path in files:
    class_counts[path.parent.name] += 1

for name, count in sorted(class_counts.items()):
    print(f"{name:<25} {count}")

print("-" * 70)
print(f"{'TOTAL':<25} {len(files)}")

# ---------------------------------------------------------
# IMAGE VALIDITY
# ---------------------------------------------------------

print("\n[2] Image integrity")
print("-" * 70)

corrupt = []
dimensions = Counter()

for path in files:

    try:
        with Image.open(path) as img:
            img.verify()

        with Image.open(path) as img:
            dimensions[img.size] += 1

    except Exception as e:
        corrupt.append((path, str(e)))

print(f"Checked : {len(files)}")
print(f"Corrupt : {len(corrupt)}")

if corrupt:
    print("\nCorrupt files:")
    for path, error in corrupt[:20]:
        print(path)
        print(error)

# ---------------------------------------------------------
# EXACT DUPLICATES
# ---------------------------------------------------------

print("\n[3] Exact duplicate check")
print("-" * 70)

hashes = {}

for path in files:

    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)

    digest = sha256.hexdigest()

    if digest not in hashes:
        hashes[digest] = []

    hashes[digest].append(path)

duplicate_groups = [
    group for group in hashes.values()
    if len(group) > 1
]

print(f"Unique hashes   : {len(hashes)}")
print(f"Duplicate groups: {len(duplicate_groups)}")

# ---------------------------------------------------------
# DIMENSIONS
# ---------------------------------------------------------

print("\n[4] Image dimensions")
print("-" * 70)

for dimension, count in dimensions.most_common():
    print(f"{dimension}: {count}")

# ---------------------------------------------------------
# FINAL STATUS
# ---------------------------------------------------------

print("\n" + "=" * 70)

if (
    len(files) == 5735
    and len(corrupt) == 0
    and len(duplicate_groups) == 0
):
    print("PASS — CLEAN COCONUT DATASET VERIFIED")
else:
    print("REVIEW REQUIRED")

print("=" * 70)