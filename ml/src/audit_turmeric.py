from pathlib import Path
from collections import Counter, defaultdict
from PIL import Image
import hashlib
import json

SOURCE = Path("ml/data/spices_raw/turmeric")
RESULTS = Path("ml/results/spices")

RESULTS.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


print("=" * 70)
print("KRUSHISETU AI — TURMERIC DATASET AUDIT")
print("=" * 70)


# ============================================================
# FIND ALL IMAGES
# ============================================================

images = [
    p for p in SOURCE.rglob("*")
    if p.is_file()
    and p.suffix.lower() in IMAGE_EXTENSIONS
]


print()
print(f"Total images found: {len(images)}")


# ============================================================
# DIRECTORY STRUCTURE
# ============================================================

print()
print("=" * 70)
print("DIRECTORY STRUCTURE")
print("=" * 70)

directory_counts = Counter()

for image in images:

    relative = image.relative_to(SOURCE)

    parts = relative.parts

    if len(parts) >= 2:
        key = str(Path(*parts[:-1]))
    else:
        key = "(root)"

    directory_counts[key] += 1


for directory, count in sorted(directory_counts.items()):

    print(
        f"{directory:<60} {count}"
    )


# ============================================================
# CLASS DETECTION
# ============================================================

print()
print("=" * 70)
print("POSSIBLE CLASS DIRECTORIES")
print("=" * 70)

class_counts = Counter()

for image in images:

    relative = image.relative_to(SOURCE)

    parts = relative.parts

    if len(parts) >= 2:

        # Assume immediate parent directory is class
        class_name = parts[-2]

    else:

        class_name = "(root)"

    class_counts[class_name] += 1


for class_name, count in sorted(
    class_counts.items(),
    key=lambda x: x[0].lower()
):

    print(
        f"{class_name:<30} {count}"
    )


# ============================================================
# IMAGE INTEGRITY
# ============================================================

print()
print("=" * 70)
print("IMAGE INTEGRITY CHECK")
print("=" * 70)

corrupt = []

dimensions = Counter()

formats = Counter()

hash_groups = defaultdict(list)


for index, image_path in enumerate(images, 1):

    try:

        with Image.open(image_path) as img:

            img.verify()

        with Image.open(image_path) as img:

            dimensions[img.size] += 1

        formats[
            image_path.suffix.lower()
        ] += 1

        digest = hashlib.sha256(
            image_path.read_bytes()
        ).hexdigest()

        hash_groups[digest].append(
            image_path
        )

    except Exception as e:

        corrupt.append(
            {
                "path": str(image_path),
                "error": str(e)
            }
        )


print(
    f"Images checked : {len(images)}"
)

print(
    f"Corrupt images : {len(corrupt)}"
)


# ============================================================
# EXACT DUPLICATE ANALYSIS
# ============================================================

duplicate_groups = [
    group
    for group in hash_groups.values()
    if len(group) > 1
]

duplicate_extra = sum(
    len(group) - 1
    for group in duplicate_groups
)


print()
print("=" * 70)
print("EXACT DUPLICATE ANALYSIS")
print("=" * 70)

print(
    f"Unique hashes       : {len(hash_groups)}"
)

print(
    f"Duplicate groups    : {len(duplicate_groups)}"
)

print(
    f"Duplicate extra files: {duplicate_extra}"
)


# ============================================================
# CROSS-CLASS DUPLICATES
# ============================================================

cross_class = []

same_class = []


for group in duplicate_groups:

    parent_classes = set()

    for path in group:

        parent_classes.add(
            path.parent.name
        )

    if len(parent_classes) > 1:

        cross_class.append(group)

    else:

        same_class.append(group)


print()
print("=" * 70)
print("CROSS-CLASS DUPLICATES")
print("=" * 70)

print(
    f"Cross-class duplicate groups: "
    f"{len(cross_class)}"
)

print(
    f"Same-class duplicate groups : "
    f"{len(same_class)}"
)


# ============================================================
# DIMENSIONS
# ============================================================

print()
print("=" * 70)
print("IMAGE DIMENSIONS")
print("=" * 70)

for dimension, count in dimensions.most_common():

    print(
        f"{dimension}: {count}"
    )


# ============================================================
# FORMATS
# ============================================================

print()
print("=" * 70)
print("IMAGE FORMATS")
print("=" * 70)

for extension, count in formats.most_common():

    print(
        f"{extension:<8} {count}"
    )


# ============================================================
# DUPLICATE EXAMPLES
# ============================================================

if duplicate_groups:

    print()
    print("=" * 70)
    print("DUPLICATE EXAMPLES")
    print("=" * 70)

    for index, group in enumerate(
        duplicate_groups[:10],
        1
    ):

        print()
        print(f"Group {index}:")

        for path in group:

            print(
                f"  {path.relative_to(SOURCE)}"
            )


# ============================================================
# SAVE REPORT
# ============================================================

report = {

    "total_images":
        len(images),

    "class_counts":
        dict(class_counts),

    "corrupt_images":
        len(corrupt),

    "unique_hashes":
        len(hash_groups),

    "duplicate_groups":
        len(duplicate_groups),

    "duplicate_extra_files":
        duplicate_extra,

    "cross_class_duplicate_groups":
        len(cross_class),

    "same_class_duplicate_groups":
        len(same_class),

    "dimensions":
        {
            str(k): v
            for k, v in dimensions.items()
        },

    "formats":
        dict(formats),

    "directory_counts":
        dict(directory_counts)
}


with open(
    RESULTS / "turmeric_dataset_audit.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        report,
        f,
        indent=2
    )


print()
print("=" * 70)
print("TURMERIC AUDIT COMPLETE")
print("=" * 70)

print(
    f"Report saved: "
    f"{RESULTS / 'turmeric_dataset_audit.json'}"
)