from pathlib import Path
from PIL import Image, ImageFile
from collections import Counter, defaultdict
import hashlib
import json

ImageFile.LOAD_TRUNCATED_IMAGES = False

ROOT = Path("ml/data/coconut_raw/Coconut Tree Disease Dataset")
RESULTS = Path("ml/results/coconut")
RESULTS.mkdir(parents=True, exist_ok=True)

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

print("=" * 70)
print("KRUSHISETU AI — COCONUT DATASET AUDIT")
print("=" * 70)

# ---------------------------------------------------------
# 1. CLASS COUNTS
# ---------------------------------------------------------

class_dirs = sorted([p for p in ROOT.iterdir() if p.is_dir()])

print("\n[1] Classes")
print("-" * 70)

class_counts = {}

for class_dir in class_dirs:
    count = sum(
        1 for p in class_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    )

    class_counts[class_dir.name] = count
    print(f"{class_dir.name:<25} {count}")

total_images = sum(class_counts.values())

print("-" * 70)
print(f"{'TOTAL':<25} {total_images}")

# ---------------------------------------------------------
# 2. IMAGE VALIDITY + DIMENSIONS
# ---------------------------------------------------------

print("\n[2] Checking image integrity...")
print("-" * 70)

corrupt = []
dimensions = Counter()
format_counts = Counter()

all_files = []

for class_dir in class_dirs:
    for path in class_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in VALID_EXTENSIONS:
            continue

        all_files.append(path)

        try:
            with Image.open(path) as img:
                img.verify()

            with Image.open(path) as img:
                dimensions[img.size] += 1
                format_counts[img.format] += 1

        except Exception as e:
            corrupt.append({
                "file": str(path),
                "error": str(e)
            })

print(f"Images checked : {len(all_files)}")
print(f"Corrupt images: {len(corrupt)}")

if corrupt:
    print("\nCorrupt files:")
    for item in corrupt[:20]:
        print(item["file"])

# ---------------------------------------------------------
# 3. EXACT DUPLICATE AUDIT
# ---------------------------------------------------------

print("\n[3] Checking exact duplicate images...")
print("-" * 70)

hash_to_files = defaultdict(list)

for i, path in enumerate(all_files, 1):

    try:
        sha256 = hashlib.sha256()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)

        hash_to_files[sha256.hexdigest()].append(path)

    except Exception as e:
        print(f"Hash failed: {path} -> {e}")

duplicate_groups = {
    h: files
    for h, files in hash_to_files.items()
    if len(files) > 1
}

duplicate_extra = sum(
    len(files) - 1
    for files in duplicate_groups.values()
)

print(f"Unique image hashes : {len(hash_to_files)}")
print(f"Duplicate groups    : {len(duplicate_groups)}")
print(f"Duplicate extra files: {duplicate_extra}")

if duplicate_groups:
    print("\nFirst duplicate groups:")

    for files in list(duplicate_groups.values())[:10]:
        print("\nGROUP:")
        for f in files:
            print(f"  {f}")

# ---------------------------------------------------------
# 4. CLASS DISTRIBUTION
# ---------------------------------------------------------

print("\n[4] Class distribution")
print("-" * 70)

for name, count in sorted(
    class_counts.items(),
    key=lambda x: x[1],
    reverse=True
):
    percentage = (count / total_images) * 100
    print(f"{name:<25} {count:>5} ({percentage:>6.2f}%)")

# ---------------------------------------------------------
# 5. DIMENSION DISTRIBUTION
# ---------------------------------------------------------

print("\n[5] Image dimensions")
print("-" * 70)

for dimension, count in dimensions.most_common(20):
    print(f"{str(dimension):<15} {count}")

# ---------------------------------------------------------
# 6. IMAGE FORMAT DISTRIBUTION
# ---------------------------------------------------------

print("\n[6] Image formats")
print("-" * 70)

for fmt, count in format_counts.items():
    print(f"{fmt:<10} {count}")

# ---------------------------------------------------------
# 7. SAVE AUDIT JSON
# ---------------------------------------------------------

audit = {
    "dataset": "Coconut Tree Disease Dataset",
    "total_images": total_images,
    "classes": class_counts,
    "corrupt_images": len(corrupt),
    "corrupt_files": corrupt,
    "unique_hashes": len(hash_to_files),
    "duplicate_groups": len(duplicate_groups),
    "duplicate_extra_files": duplicate_extra,
    "dimensions": {
        f"{w}x{h}": count
        for (w, h), count in dimensions.items()
    },
    "formats": dict(format_counts)
}

output_file = RESULTS / "coconut_dataset_audit.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2)

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)
print(f"Audit saved to: {output_file}")