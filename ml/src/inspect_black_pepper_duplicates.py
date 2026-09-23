from pathlib import Path
import hashlib
from collections import defaultdict

ROOT = Path("ml/data/spices_raw/black_pepper/BLACK_PEPPER_DATASET")

hash_groups = defaultdict(list)

for class_dir in ROOT.iterdir():
    if not class_dir.is_dir():
        continue

    for path in class_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue

        h = hashlib.sha256(path.read_bytes()).hexdigest()
        hash_groups[h].append((path, class_dir.name))

duplicates = [
    group for group in hash_groups.values()
    if len(group) > 1
]

print("=" * 70)
print("BLACK PEPPER DUPLICATE INSPECTION")
print("=" * 70)

print(f"Duplicate groups: {len(duplicates)}")

for i, group in enumerate(duplicates, 1):

    print(f"\nGROUP {i}")
    print("-" * 50)

    for path, cls in group:
        print(f"Class: {cls}")
        print(f"File : {path.name}")

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)