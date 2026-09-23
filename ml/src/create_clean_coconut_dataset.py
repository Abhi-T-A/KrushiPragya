from pathlib import Path
from collections import defaultdict
import hashlib
import shutil

SOURCE = Path("ml/data/coconut_raw/Coconut Tree Disease Dataset")
DEST = Path("ml/data/coconut_cleaned")

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ---------------------------------------------------------
# RESET OUTPUT
# ---------------------------------------------------------

if DEST.exists():
    shutil.rmtree(DEST)

DEST.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("KRUSHISETU AI — CLEAN COCONUT DATASET")
print("=" * 70)

# ---------------------------------------------------------
# COLLECT FILES
# ---------------------------------------------------------

files = []

for class_dir in sorted(SOURCE.iterdir()):
    if not class_dir.is_dir():
        continue

    for path in sorted(class_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
            files.append(path)

print(f"\nRaw images: {len(files)}")

# ---------------------------------------------------------
# HASH ALL IMAGES
# ---------------------------------------------------------

hash_to_files = defaultdict(list)

for path in files:

    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)

    hash_to_files[sha256.hexdigest()].append(path)

# ---------------------------------------------------------
# IDENTIFY DUPLICATES
# ---------------------------------------------------------

conflicting_groups = []
same_class_groups = []

for image_hash, group in hash_to_files.items():

    classes = {p.parent.name for p in group}

    if len(group) > 1:

        if len(classes) > 1:
            # Same exact image has different labels.
            conflicting_groups.append(group)

        else:
            # Same exact image repeated within same class.
            same_class_groups.append(group)

print(f"Duplicate groups          : {len(conflicting_groups) + len(same_class_groups)}")
print(f"Cross-class conflicts     : {len(conflicting_groups)}")
print(f"Same-class duplicate groups: {len(same_class_groups)}")

# ---------------------------------------------------------
# BUILD EXCLUSION SET
# ---------------------------------------------------------

exclude = set()

# Cross-class conflicts:
# Remove EVERY copy because the correct label cannot
# be determined from the dataset itself.
for group in conflicting_groups:
    for path in group:
        exclude.add(path)

# Same-class duplicates:
# Keep the first deterministic copy, remove the rest.
for group in same_class_groups:
    for path in group[1:]:
        exclude.add(path)

print(f"\nFiles excluded: {len(exclude)}")

# ---------------------------------------------------------
# COPY CLEAN DATASET
# ---------------------------------------------------------

copied = 0

for path in files:

    if path in exclude:
        continue

    class_name = path.parent.name

    destination_dir = DEST / class_name
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination = destination_dir / path.name

    shutil.copy2(path, destination)

    copied += 1

# ---------------------------------------------------------
# FINAL COUNTS
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("CLEAN DATASET COUNTS")
print("=" * 70)

total = 0

for class_dir in sorted(DEST.iterdir()):

    if not class_dir.is_dir():
        continue

    count = sum(
        1 for p in class_dir.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    )

    total += count

    print(f"{class_dir.name:<25} {count}")

print("-" * 70)
print(f"{'TOTAL':<25} {total}")

print("\n" + "=" * 70)
print("CLEANING COMPLETE")
print("=" * 70)

print(f"Source : {SOURCE}")
print(f"Output : {DEST}")
print(f"Copied : {copied}")
print(f"Excluded: {len(exclude)}")