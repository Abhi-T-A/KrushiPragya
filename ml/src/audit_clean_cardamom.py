from pathlib import Path
from collections import defaultdict
from PIL import Image
import hashlib


DATASET = Path("ml/data/cardamom_cleaned")

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


print("=" * 70)
print("KRUSHISETU AI — FINAL CLEAN CARDAMOM AUDIT")
print("=" * 70)


# =========================================================
# CLASS COUNTS
# =========================================================

class_dirs = sorted(
    [p for p in DATASET.iterdir() if p.is_dir()],
    key=lambda x: x.name.lower()
)

total = 0

print("\n[1] Class counts")
print("-" * 60)

for class_dir in class_dirs:

    count = sum(
        1
        for p in class_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    print(f"{class_dir.name:<25} {count}")
    total += count

print("-" * 60)
print(f"TOTAL{'':<20} {total}")


# =========================================================
# IMAGE INTEGRITY
# =========================================================

print("\n[2] Image integrity")
print("-" * 60)

corrupt = 0
checked = 0

for class_dir in class_dirs:

    for image_path in class_dir.rglob("*"):

        if not image_path.is_file():
            continue

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        checked += 1

        try:
            with Image.open(image_path) as img:
                img.verify()

        except Exception:
            corrupt += 1
            print(f"CORRUPT: {image_path}")


print(f"Checked : {checked}")
print(f"Corrupt : {corrupt}")


# =========================================================
# EXACT DUPLICATES
# =========================================================

print("\n[3] Exact duplicate check")
print("-" * 60)

hashes = defaultdict(list)


def get_hash(path):

    h = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


for class_dir in class_dirs:

    for image_path in class_dir.rglob("*"):

        if not image_path.is_file():
            continue

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        hashes[get_hash(image_path)].append(image_path)


duplicate_groups = [
    files
    for files in hashes.values()
    if len(files) > 1
]

print(f"Unique hashes    : {len(hashes)}")
print(f"Duplicate groups : {len(duplicate_groups)}")


# =========================================================
# IMAGE DIMENSIONS
# =========================================================

print("\n[4] Image dimensions")
print("-" * 60)

dimensions = defaultdict(int)

for class_dir in class_dirs:

    for image_path in class_dir.rglob("*"):

        if not image_path.is_file():
            continue

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        try:

            with Image.open(image_path) as img:
                dimensions[img.size] += 1

        except Exception:
            pass


for dimension, count in sorted(
    dimensions.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(f"{dimension}: {count}")


# =========================================================
# FINAL STATUS
# =========================================================

passed = (
    total == 1724
    and checked == 1724
    and corrupt == 0
    and len(duplicate_groups) == 0
)

print("\n" + "=" * 70)

if passed:
    print("PASS — CLEAN CARDAMOM DATASET VERIFIED")
else:
    print("FAIL — DATASET REQUIRES INVESTIGATION")

print("=" * 70)