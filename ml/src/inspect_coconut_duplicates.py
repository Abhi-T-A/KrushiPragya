from pathlib import Path
from collections import defaultdict
import hashlib

ROOT = Path("ml/data/coconut_raw/Coconut Tree Disease Dataset")

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

hash_to_files = defaultdict(list)

for class_dir in ROOT.iterdir():
    if not class_dir.is_dir():
        continue

    for path in class_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in VALID_EXTENSIONS:
            continue

        sha256 = hashlib.sha256()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)

        hash_to_files[sha256.hexdigest()].append(path)

duplicate_groups = [
    files for files in hash_to_files.values()
    if len(files) > 1
]

print("=" * 70)
print("COCONUT DUPLICATE INSPECTION")
print("=" * 70)

print(f"Duplicate groups: {len(duplicate_groups)}")
print()

for i, files in enumerate(duplicate_groups, 1):

    print(f"GROUP {i}")
    print("-" * 50)

    for path in files:
        print(f"Class: {path.parent.name}")
        print(f"File : {path.name}")
        print()

    print("=" * 70)