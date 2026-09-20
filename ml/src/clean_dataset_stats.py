from pathlib import Path

DATASET_ROOT = Path("ml/data/cleaned")
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

print("=" * 60)
print("KrushiSetu Clean Dataset Statistics")
print("=" * 60)

for split in ["train", "test"]:

    split_dir = DATASET_ROOT / split

    print()
    print("=" * 60)
    print(f"{split.upper()} DATASET")
    print("=" * 60)

    total = 0

    if not split_dir.exists():
        print(f"ERROR: Folder not found: {split_dir}")
        continue

    for class_dir in sorted(split_dir.iterdir()):

        if not class_dir.is_dir():
            continue

        count = 0

        for image_path in class_dir.iterdir():
            if (
                image_path.is_file()
                and image_path.suffix.lower() in VALID_EXTENSIONS
            ):
                count += 1

        print(f"{class_dir.name:25} : {count}")
        total += count

    print("-" * 60)
    print(f"TOTAL                     : {total}")

print()
print("=" * 60)
print("Clean dataset statistics complete.")
print("=" * 60)