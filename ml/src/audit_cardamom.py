from pathlib import Path
from collections import Counter, defaultdict
from PIL import Image
import hashlib
import json


# =========================================================
# CONFIG
# =========================================================

DATASET = Path(
    "ml/data/spices_raw/cardamom/Cardamom_Plant_Dataset_Chinnahalli_1724"
)

RESULTS_DIR = Path("ml/results/spices")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = RESULTS_DIR / "cardamom_dataset_audit.json"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


# =========================================================
# HEADER
# =========================================================

print("=" * 70)
print("KRUSHISETU AI — CARDAMOM DATASET AUDIT")
print("=" * 70)


# =========================================================
# DISCOVER CLASSES
# =========================================================

class_dirs = [
    p for p in DATASET.iterdir()
    if p.is_dir()
]

class_dirs.sort(key=lambda x: x.name.lower())

class_names = [p.name for p in class_dirs]

print("\n[1] Classes")
print("-" * 60)

total_images = 0
class_counts = {}

for class_dir in class_dirs:

    count = sum(
        1
        for p in class_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    class_counts[class_dir.name] = count
    total_images += count

    print(f"{class_dir.name:<30} {count}")


print("-" * 60)
print(f"TOTAL{'':<25} {total_images}")


# =========================================================
# IMAGE INTEGRITY
# =========================================================

print("\n[2] Checking image integrity...")
print("-" * 60)

corrupt_images = []
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
            corrupt_images.append(str(image_path))


print(f"Images checked : {checked}")
print(f"Corrupt images : {len(corrupt_images)}")


if corrupt_images:

    print("\nCorrupt files:")

    for path in corrupt_images[:20]:
        print(path)


# =========================================================
# EXACT DUPLICATES
# =========================================================

print("\n[3] Checking exact duplicate images...")
print("-" * 60)


hash_to_files = defaultdict(list)


def file_hash(path):

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

        digest = file_hash(image_path)

        hash_to_files[digest].append(
            image_path
        )


duplicate_groups = [
    files
    for files in hash_to_files.values()
    if len(files) > 1
]

duplicate_extra_files = sum(
    len(files) - 1
    for files in duplicate_groups
)


print(
    f"Unique image hashes : {len(hash_to_files)}"
)

print(
    f"Duplicate groups    : {len(duplicate_groups)}"
)

print(
    f"Duplicate extra files: {duplicate_extra_files}"
)


# =========================================================
# CROSS-CLASS DUPLICATES
# =========================================================

print("\n[4] Checking cross-class duplicate images...")
print("-" * 60)


cross_class_groups = []
same_class_groups = []

for files in duplicate_groups:

    classes = set(
        path.parent.name
        for path in files
    )

    if len(classes) > 1:

        cross_class_groups.append(files)

    else:

        same_class_groups.append(files)


print(
    f"Cross-class duplicate groups : "
    f"{len(cross_class_groups)}"
)

print(
    f"Same-class duplicate groups  : "
    f"{len(same_class_groups)}"
)


if cross_class_groups:

    print("\nCross-class duplicate groups:")

    for i, files in enumerate(
        cross_class_groups[:20],
        start=1
    ):

        print(f"\nGROUP {i}")

        for path in files:
            print(
                f"  {path.parent.name} -> {path.name}"
            )


# =========================================================
# IMAGE DIMENSIONS
# =========================================================

print("\n[5] Image dimensions")
print("-" * 60)

dimensions = Counter()

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


for dimension, count in dimensions.most_common():

    print(
        f"{dimension}: {count}"
    )


# =========================================================
# IMAGE FORMATS
# =========================================================

print("\n[6] Image formats")
print("-" * 60)

formats = Counter()

for class_dir in class_dirs:

    for image_path in class_dir.rglob("*"):

        if not image_path.is_file():
            continue

        formats[
            image_path.suffix.lower()
        ] += 1


for extension, count in formats.items():

    print(
        f"{extension:<10} {count}"
    )


# =========================================================
# SAVE REPORT
# =========================================================

audit = {
    "dataset": str(DATASET),
    "classes": class_names,
    "class_counts": class_counts,
    "total_images": total_images,
    "images_checked": checked,
    "corrupt_images": corrupt_images,
    "unique_image_hashes": len(hash_to_files),
    "duplicate_groups": len(duplicate_groups),
    "duplicate_extra_files": duplicate_extra_files,
    "cross_class_duplicate_groups": len(
        cross_class_groups
    ),
    "same_class_duplicate_groups": len(
        same_class_groups
    ),
    "dimensions": {
        str(k): v
        for k, v in dimensions.items()
    },
    "formats": dict(formats),
}


with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        audit,
        f,
        indent=2
    )


# =========================================================
# COMPLETE
# =========================================================

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)

print(
    f"Audit saved to: {OUTPUT_JSON}"
)