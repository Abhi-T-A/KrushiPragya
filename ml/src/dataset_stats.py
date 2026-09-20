from pathlib import Path
from collections import Counter

DATASET_ROOT = Path(
    r"C:\Users\Teja\Downloads\agriculture_dataset\Arecanut_dataset\Arecanut_dataset"
)

for split in ["train", "test"]:
    split_dir = DATASET_ROOT / split

    counts = Counter()

    for class_dir in sorted(split_dir.iterdir()):
        if not class_dir.is_dir():
            continue

        count = sum(
            1 for p in class_dir.iterdir()
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )

        counts[class_dir.name] = count

    print("\n" + "=" * 50)
    print(f"{split.upper()} DATASET")
    print("=" * 50)

    total = 0

    for class_name, count in counts.items():
        print(f"{class_name:25} : {count}")
        total += count

    print("-" * 50)
    print(f"TOTAL                     : {total}")

print("\nDataset statistics complete.")