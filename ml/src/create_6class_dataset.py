from pathlib import Path
import shutil

SOURCE_ROOT = Path("ml/data/cleaned")
OUTPUT_ROOT = Path("ml/data/arecanut_6class")

# These four classes will become one Healthy class
HEALTHY_CLASSES = {
    "Healthy_Leaf",
    "Healthy_Nut",
    "Healthy_Trunk",
    "healthy_foot",
}

# Exact folder names from your dataset
DISEASE_CLASSES = {
    "Mahali_Koleroga",
    "yellow leaf disease",
    "stem cracking",
    "Stem_bleeding",
    "bud borer",
}

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def copy_images(source_dir, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    copied = 0

    for image_path in source_dir.iterdir():

        if not image_path.is_file():
            continue

        if image_path.suffix.lower() not in VALID_EXTENSIONS:
            continue

        destination = output_dir / image_path.name

        # Avoid filename collision
        if destination.exists():
            destination = output_dir / (
                f"{source_dir.name}_{image_path.name}"
            )

        shutil.copy2(image_path, destination)
        copied += 1

    return copied


print("=" * 60)
print("KrushiSetu 6-Class Arecanut Dataset Creation")
print("=" * 60)


for split in ["train", "test"]:

    source_split = SOURCE_ROOT / split
    output_split = OUTPUT_ROOT / split

    print()
    print(f"[{split.upper()}]")
    print("-" * 60)

    # --------------------------------------------------
    # HEALTHY
    # --------------------------------------------------

    healthy_output = output_split / "Healthy"

    healthy_total = 0

    for class_name in sorted(HEALTHY_CLASSES):

        source_dir = source_split / class_name

        if not source_dir.exists():
            print(f"WARNING: Missing class: {source_dir}")
            continue

        count = copy_images(
            source_dir,
            healthy_output
        )

        print(
            f"{class_name:25} -> Healthy : {count}"
        )

        healthy_total += count

    print(
        f"{'Healthy TOTAL':25} : {healthy_total}"
    )

    # --------------------------------------------------
    # DISEASE CLASSES
    # --------------------------------------------------

    for class_name in sorted(DISEASE_CLASSES):

        source_dir = source_split / class_name

        if not source_dir.exists():
            print(
                f"WARNING: Missing class: {source_dir}"
            )
            continue

        output_dir = output_split / class_name

        count = copy_images(
            source_dir,
            output_dir
        )

        print(
            f"{class_name:25} : {count}"
        )


print()
print("=" * 60)
print("6-Class Dataset Creation Complete")
print("=" * 60)
print(f"Location: {OUTPUT_ROOT}")
print("=" * 60)