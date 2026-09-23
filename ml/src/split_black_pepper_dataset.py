from pathlib import Path
import shutil
import random

SOURCE = Path("ml/data/black_pepper_cleaned")
OUTPUT = Path("ml/data/black_pepper_3class")

SEED = 42
random.seed(SEED)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

print("=" * 70)
print("KRUSHISETU AI — BLACK PEPPER TRAIN/VAL/TEST SPLIT")
print("=" * 70)

total_train = 0
total_val = 0
total_test = 0

for class_dir in sorted(SOURCE.iterdir()):

    if not class_dir.is_dir():
        continue

    images = sorted([
        p for p in class_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ])

    random.shuffle(images)

    total = len(images)

    train_count = int(total * TRAIN_RATIO)
    val_count = int(total * VAL_RATIO)

    train_images = images[:train_count]
    val_images = images[train_count:train_count + val_count]
    test_images = images[train_count + val_count:]

    for split, split_images in [
        ("train", train_images),
        ("val", val_images),
        ("test", test_images)
    ]:

        destination = OUTPUT / split / class_dir.name
        destination.mkdir(parents=True, exist_ok=True)

        for image in split_images:
            shutil.copy2(image, destination / image.name)

    total_train += len(train_images)
    total_val += len(val_images)
    total_test += len(test_images)

    print(
        f"{class_dir.name:<20}"
        f"Train: {len(train_images):<5}"
        f"Val: {len(val_images):<5}"
        f"Test: {len(test_images)}"
    )

print("\n" + "-" * 60)

print(f"TRAIN      {total_train}")
print(f"VALIDATION {total_val}")
print(f"TEST       {total_test}")
print(f"TOTAL      {total_train + total_val + total_test}")

print("-" * 60)
print(f"\nOutput: {OUTPUT}")
print(f"Random seed: {SEED}")

print("\n" + "=" * 70)
print("PASS — DATASET SPLIT CREATED")
print("=" * 70)