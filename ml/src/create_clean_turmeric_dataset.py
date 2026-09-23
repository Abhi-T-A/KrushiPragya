from pathlib import Path
import shutil
import random

SOURCE = Path(
    "ml/data/spices_raw/turmeric/"
    "Image Dataset for Turmeric Plant Leaf Disease Detection/"
    "Original DataSet"
)

OUTPUT = Path("ml/data/turmeric_4class")

SEED = 42

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


random.seed(SEED)


print("=" * 70)
print("KRUSHISETU AI — TURMERIC CLEAN DATASET")
print("=" * 70)

print()
print("IMPORTANT:")
print("Using ORIGINAL images only.")
print("Augmented dataset is excluded to prevent hidden leakage.")
print()


# ============================================================
# VERIFY SOURCE
# ============================================================

if not SOURCE.exists():

    raise FileNotFoundError(
        f"Original dataset not found:\n{SOURCE}"
    )


# ============================================================
# VERIFY SPLIT RATIOS
# ============================================================

if abs(
    TRAIN_RATIO +
    VAL_RATIO +
    TEST_RATIO -
    1.0
) > 1e-6:

    raise ValueError(
        "Split ratios must add up to 1.0"
    )


# ============================================================
# REMOVE OLD OUTPUT
# ============================================================

if OUTPUT.exists():

    print(
        f"Removing existing output:\n{OUTPUT}"
    )

    shutil.rmtree(OUTPUT)


OUTPUT.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FIND CLASSES
# ============================================================

class_dirs = sorted(
    [
        p
        for p in SOURCE.iterdir()
        if p.is_dir()
    ],
    key=lambda x: x.name.lower()
)


print("Classes:")

for class_dir in class_dirs:

    print(
        f"  - {class_dir.name}"
    )

print()


# ============================================================
# CREATE SPLITS
# ============================================================

total_train = 0
total_val = 0
total_test = 0


for class_dir in class_dirs:

    images = [

        p
        for p in class_dir.rglob("*")

        if p.is_file()
        and p.suffix.lower()
        in IMAGE_EXTENSIONS
    ]


    random.shuffle(images)


    total = len(images)


    train_end = int(
        total * TRAIN_RATIO
    )

    val_end = (
        train_end +
        int(total * VAL_RATIO)
    )


    train_images = images[
        :train_end
    ]

    val_images = images[
        train_end:val_end
    ]

    test_images = images[
        val_end:
    ]


    # --------------------------------------------------------
    # COPY FILES
    # --------------------------------------------------------

    for split_name, split_images in [

        ("train", train_images),

        ("val", val_images),

        ("test", test_images)

    ]:

        destination = (
            OUTPUT /
            split_name /
            class_dir.name
        )


        destination.mkdir(
            parents=True,
            exist_ok=True
        )


        for image_path in split_images:

            shutil.copy2(

                image_path,

                destination /
                image_path.name
            )


    total_train += len(
        train_images
    )

    total_val += len(
        val_images
    )

    total_test += len(
        test_images
    )


    print(

        f"{class_dir.name:<20} "

        f"Train: {len(train_images):3d} | "

        f"Val: {len(val_images):3d} | "

        f"Test: {len(test_images):3d}"
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("-" * 70)

print(
    f"TOTAL TRAIN: {total_train}"
)

print(
    f"TOTAL VAL  : {total_val}"
)

print(
    f"TOTAL TEST : {total_test}"
)

print(
    f"TOTAL      : "
    f"{total_train + total_val + total_test}"
)


print()
print(
    "Augmented images excluded:"
)

print(
    "3,496 augmented images were NOT copied."
)

print()
print(
    f"Output: {OUTPUT}"
)


print()
print("=" * 70)
print("TURMERIC CLEAN DATASET CREATED")
print("=" * 70)