from pathlib import Path
from PIL import Image

DATASET_ROOT = Path(
    r"C:\Users\Teja\Downloads\agriculture_dataset\Arecanut_dataset\Arecanut_dataset"
)

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

total = 0
valid = 0
corrupt = []

for split in ["train", "test"]:
    split_dir = DATASET_ROOT / split

    for class_dir in sorted(split_dir.iterdir()):
        if not class_dir.is_dir():
            continue

        for image_path in class_dir.iterdir():
            if image_path.suffix.lower() not in VALID_EXTENSIONS:
                continue

            total += 1

            try:
                with Image.open(image_path) as img:
                    img.verify()

                valid += 1

            except Exception:
                corrupt.append(str(image_path))


print()
print("=" * 50)
print("KrushiSetu Dataset Integrity Check")
print("=" * 50)
print(f"Total images : {total}")
print(f"Valid images : {valid}")
print(f"Corrupt      : {len(corrupt)}")
print("=" * 50)

if corrupt:
    print("\nCORRUPT FILES:")
    for path in corrupt:
        print(path)
else:
    print("\n✅ No corrupt images found.")