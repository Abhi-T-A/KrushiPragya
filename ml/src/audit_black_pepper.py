from pathlib import Path
from PIL import Image
import hashlib
import json
from collections import defaultdict, Counter

ROOT = Path("ml/data/spices_raw/black_pepper/BLACK_PEPPER_DATASET")
RESULTS = Path("ml/results/spices")
RESULTS.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("KRUSHISETU AI — BLACK PEPPER DATASET AUDIT")
print("=" * 70)

classes = sorted([p.name for p in ROOT.iterdir() if p.is_dir()])

# ---------------------------------------------------------
# 1. CLASS COUNTS
# ---------------------------------------------------------
print("\n[1] Classes")
print("-" * 60)

class_counts = {}

for cls in classes:
    files = [
        p for p in (ROOT / cls).rglob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]

    class_counts[cls] = len(files)
    print(f"{cls:<25} {len(files)}")

total = sum(class_counts.values())

print("-" * 60)
print(f"TOTAL{' ':<19} {total}")

# ---------------------------------------------------------
# 2. IMAGE INTEGRITY
# ---------------------------------------------------------
print("\n[2] Checking image integrity...")
print("-" * 60)

corrupt = []
dimensions = Counter()
formats = Counter()

all_images = []

for cls in classes:
    for path in (ROOT / cls).rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue

        all_images.append((path, cls))

        try:
            with Image.open(path) as img:
                img.verify()

            with Image.open(path) as img:
                dimensions[img.size] += 1
                formats[path.suffix.lower()] += 1

        except Exception:
            corrupt.append(str(path))

print(f"Images checked : {len(all_images)}")
print(f"Corrupt images : {len(corrupt)}")

if corrupt:
    print("\nCorrupt files:")
    for p in corrupt[:20]:
        print(p)

# ---------------------------------------------------------
# 3. EXACT DUPLICATES
# ---------------------------------------------------------
print("\n[3] Checking exact duplicate images...")
print("-" * 60)

hash_groups = defaultdict(list)

for path, cls in all_images:
    try:
        data = path.read_bytes()
        h = hashlib.sha256(data).hexdigest()
        hash_groups[h].append((path, cls))
    except Exception:
        pass

duplicate_groups = [
    group for group in hash_groups.values()
    if len(group) > 1
]

duplicate_extra = sum(len(group) - 1 for group in duplicate_groups)

print(f"Unique image hashes : {len(hash_groups)}")
print(f"Duplicate groups    : {len(duplicate_groups)}")
print(f"Duplicate extra files: {duplicate_extra}")

# ---------------------------------------------------------
# 4. CROSS-CLASS DUPLICATES
# ---------------------------------------------------------
print("\n[4] Checking cross-class duplicate images...")
print("-" * 60)

cross_class_groups = []

for group in duplicate_groups:
    group_classes = set(cls for _, cls in group)

    if len(group_classes) > 1:
        cross_class_groups.append(group)

print(f"Cross-class duplicate groups: {len(cross_class_groups)}")

for i, group in enumerate(cross_class_groups[:20], 1):
    print(f"\nGROUP {i}")
    for path, cls in group:
        print(f"  {cls:<20} {path.name}")

# ---------------------------------------------------------
# 5. SAME-CLASS DUPLICATES
# ---------------------------------------------------------
same_class_groups = []

for group in duplicate_groups:
    group_classes = set(cls for _, cls in group)

    if len(group_classes) == 1:
        same_class_groups.append(group)

print("\nSame-class duplicate groups:", len(same_class_groups))

# ---------------------------------------------------------
# 6. DIMENSIONS
# ---------------------------------------------------------
print("\n[5] Image dimensions")
print("-" * 60)

for dim, count in dimensions.most_common():
    print(f"{dim}: {count}")

# ---------------------------------------------------------
# 7. FORMATS
# ---------------------------------------------------------
print("\n[6] Image formats")
print("-" * 60)

for fmt, count in formats.items():
    print(f"{fmt.upper():<10} {count}")

# ---------------------------------------------------------
# SAVE REPORT
# ---------------------------------------------------------
report = {
    "classes": class_counts,
    "total_images": total,
    "corrupt_images": len(corrupt),
    "unique_hashes": len(hash_groups),
    "duplicate_groups": len(duplicate_groups),
    "duplicate_extra_files": duplicate_extra,
    "cross_class_duplicate_groups": len(cross_class_groups),
    "same_class_duplicate_groups": len(same_class_groups),
    "dimensions": {
        str(k): v for k, v in dimensions.items()
    },
    "formats": dict(formats),
}

output = RESULTS / "black_pepper_dataset_audit.json"

with open(output, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)
print(f"Audit saved to: {output}")