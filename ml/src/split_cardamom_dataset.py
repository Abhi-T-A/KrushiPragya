from pathlib import Path
import random
import shutil


SOURCE = Path("ml/data/cardamom_cleaned")
OUTPUT = Path("ml/data/cardamom_3class")

CLASSES = [
    "Blight1000",
    "Healthy_1000",
    "Phylosticta_LS_1000",
]

SEED = 42

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


print("=" * 70)
print("KRUSHISETU AI — CARDAMOM TRAIN/VAL/TEST SPLIT")
print("=" * 70)

random.seed(SEED)

if OUTPUT.exists():
    print("\nRemoving previous split...")
    shutil.rmtree(OUTPUT)

for split in ["train", "val", "test"]:
    for class_name in CLASSES:
        (OUTPUT / split / class_name).mkdir(
            parents=True,
            exist_ok=True
        )


total_counts = {
    "train": 0,
    "val": 0,
    "test": 0,
}


for class_name in CLASSES:

    source_dir = SOURCE / class_name

    images = [
        p
        for p in source_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    ]

    images.sort()

    random.shuffle(images)

    n = len(images)

    train_end = int(n * TRAIN_RATIO)
    val_end = train_end + int(n * VAL_RATIO)

    train_images = images[:train_end]
    val_images = images[train_end:val_end]
    test_images = images[val_end:]

    splits = {
        "train": train_images,
        "val": val_images,
        "test": test_images,
    }

    print(
        f"{class_name:<25}"
        f"Train: {len(train_images):>4}  "
        f"Val: {len(val_images):>4}  "
        f"Test: {len(test_images):>4}"
    )

    for split_name, split_images in splits.items():

        destination_dir = (
            OUTPUT / split_name / class_name
        )

        for image_path in split_images:

            shutil.copy2(
                image_path,
                destination_dir / image_path.name
            )

            total_counts[split_name] += 1


print("\n" + "-" * 60)

print(f"TRAIN      {total_counts['train']}")
print(f"VALIDATION {total_counts['val']}")
print(f"TEST       {total_counts['test']}")
print(
    f"TOTAL      "
    f"{sum(total_counts.values())}"
)

print("\n" + "-" * 60)

print(f"Output : {OUTPUT}")
print(f"Random seed: {SEED}")

print("\n" + "=" * 70)
print("PASS — DATASET SPLIT CREATED")
print("=" * 70)