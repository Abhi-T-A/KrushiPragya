from pathlib import Path
import shutil


SOURCE = Path(
    "ml/data/spices_raw/cardamom/Cardamom_Plant_Dataset_Chinnahalli_1724"
)

OUTPUT = Path("ml/data/cardamom_cleaned")

CLASSES = [
    "Blight1000",
    "Healthy_1000",
    "Phylosticta_LS_1000",
]

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


print("=" * 70)
print("KRUSHISETU AI — CLEAN CARDAMOM DATASET")
print("=" * 70)

if OUTPUT.exists():
    print("\nRemoving previous clean dataset...")
    shutil.rmtree(OUTPUT)

OUTPUT.mkdir(
    parents=True,
    exist_ok=True
)

total_copied = 0


for class_name in CLASSES:

    source_dir = SOURCE / class_name
    output_dir = OUTPUT / class_name

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    copied = 0

    for image_path in source_dir.rglob("*"):

        if not image_path.is_file():
            continue

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        destination = output_dir / image_path.name

        shutil.copy2(
            image_path,
            destination
        )

        copied += 1
        total_copied += 1

    print(
        f"{class_name:<25} {copied}"
    )


print("-" * 70)
print(f"TOTAL COPIED{'':<17} {total_copied}")

print("\n" + "=" * 70)
print("CLEANING COMPLETE")
print("=" * 70)

print(f"\nSource : {SOURCE}")
print(f"Output : {OUTPUT}")
print(f"Copied : {total_copied}")