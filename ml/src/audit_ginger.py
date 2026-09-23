from pathlib import Path
from collections import Counter, defaultdict
from PIL import Image
import hashlib
import json

DATASET = Path("ml/data/spices_raw/ginger/combined")
RESULTS = Path("ml/results/spices")
RESULTS.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

print("=" * 70)
print("KRUSHISETU AI — GINGER DATASET AUDIT")
print("=" * 70)

# Discover classes
class_dirs = sorted([p for p in DATASET.iterdir() if p.is_dir()], key=lambda x: x.name.lower())

print("\n[1] Classes")
print("-" * 60)

class_counts = {}
total = 0

for cls in class_dirs:
    count = sum(
        1 for p in cls.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    class_counts[cls.name] = count
    total += count
    print(f"{cls.name:<25} {count}")

print("-" * 60)
print(f"TOTAL{'':<20} {total}")

# Image integrity
print("\n[2] Checking image integrity...")
print("-" * 60)

corrupt = []
dimensions = Counter()
formats = Counter()
hash_groups = defaultdict(list)

checked = 0

for cls in class_dirs:
    for path in cls.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        checked += 1

        try:
            with Image.open(path) as img:
                img.verify()

            with Image.open(path) as img:
                dimensions[img.size] += 1

            formats[path.suffix.lower()] += 1

            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            hash_groups[digest].append((path, cls.name))

        except Exception:
            corrupt.append(str(path))

print(f"Images checked : {checked}")
print(f"Corrupt images : {len(corrupt)}")

# Duplicate analysis
duplicate_groups = [g for g in hash_groups.values() if len(g) > 1]
duplicate_extra = sum(len(g) - 1 for g in duplicate_groups)

cross_class = []
same_class = []

for g in duplicate_groups:
    labels = set(cls for _, cls in g)
    if len(labels) > 1:
        cross_class.append(g)
    else:
        same_class.append(g)

print("\n[3] Exact duplicate images")
print("-" * 60)
print(f"Unique image hashes : {len(hash_groups)}")
print(f"Duplicate groups    : {len(duplicate_groups)}")
print(f"Duplicate extra files: {duplicate_extra}")

print("\n[4] Cross-class duplicates")
print("-" * 60)
print(f"Cross-class duplicate groups : {len(cross_class)}")
print(f"Same-class duplicate groups  : {len(same_class)}")

print("\n[5] Image dimensions")
print("-" * 60)
for dim, count in dimensions.most_common():
    print(f"{dim}: {count}")

print("\n[6] Image formats")
print("-" * 60)
for ext, count in formats.items():
    print(f"{ext:<8} {count}")

report = {
    "class_counts": class_counts,
    "total_images": total,
    "corrupt_images": len(corrupt),
    "duplicate_groups": len(duplicate_groups),
    "duplicate_extra_files": duplicate_extra,
    "cross_class_duplicate_groups": len(cross_class),
    "same_class_duplicate_groups": len(same_class),
}

with open(RESULTS / "ginger_dataset_audit.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)