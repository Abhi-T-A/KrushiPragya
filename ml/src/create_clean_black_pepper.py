from pathlib import Path
import hashlib
import shutil

SOURCE = Path("ml/data/spices_raw/black_pepper/BLACK_PEPPER_DATASET")
OUTPUT = Path("ml/data/black_pepper_cleaned")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

print("=" * 70)
print("KRUSHISETU AI — CLEAN BLACK PEPPER DATASET")
print("=" * 70)

hashes = set()
copied = 0
excluded = 0

class_counts = {}

for class_dir in sorted(SOURCE.iterdir()):

    if not class_dir.is_dir():
        continue

    output_class = OUTPUT / class_dir.name
    output_class.mkdir(parents=True, exist_ok=True)

    count = 0

    files = sorted([
        p for p in class_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ])

    for path in files:

        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()

        if file_hash in hashes:
            excluded += 1
            continue

        hashes.add(file_hash)

        destination = output_class / path.name

        # Extremely unlikely filename collision safeguard
        if destination.exists():
            stem = path.stem
            suffix = path.suffix
            i = 1

            while destination.exists():
                destination = output_class / f"{stem}_copy{i}{suffix}"
                i += 1

        shutil.copy2(path, destination)

        copied += 1
        count += 1

    class_counts[class_dir.name] = count


print("\nCLEAN DATASET COUNTS")
print("-" * 60)

for cls, count in class_counts.items():
    print(f"{cls:<25} {count}")

print("-" * 60)
print(f"TOTAL{' ':<19} {copied}")

print("\nFiles excluded:", excluded)

print("\n" + "=" * 70)
print("CLEANING COMPLETE")
print("=" * 70)

print(f"Source : {SOURCE}")
print(f"Output : {OUTPUT}")
print(f"Copied : {copied}")
print(f"Excluded: {excluded}")