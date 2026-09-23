from pathlib import Path
import random
import shutil
from PIL import Image


# ============================================================
# PATHS
# ============================================================

BASE = Path(r"C:\Users\Teja\scout\ml\data")

PADDY_CLEANED = BASE / "paddy_cleaned" / "train"

BPH_ROOT = BASE / "paddy_supplementary" / "BPH"

SHEATH_ROOT = (
    BASE
    / "paddy_supplementary"
    / "Sheath_Blight"
    / "RiceLeafDiseaseBD"
)

OUTPUT = BASE / "paddy_4class"

SEED = 42

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


# ============================================================
# FINAL TAXONOMY
# ============================================================

CLASSES = [
    "Blast",
    "Bacterial_Leaf_Blight",
    "Brown_Plant_Hopper",
    "Sheath_Blight",
]


# ============================================================
# HELPERS
# ============================================================

def get_images(folder):
    if not folder.exists():
        return []

    return [
        p
        for p in folder.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    ]


def clean_output():

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    for split in ["train", "val", "test"]:

        for cls in CLASSES:

            (
                OUTPUT
                / split
                / cls
            ).mkdir(
                parents=True,
                exist_ok=True
            )


def copy_image(src, dst):

    dst.mkdir(
        parents=True,
        exist_ok=True
    )

    target = dst / src.name

    if not target.exists():

        shutil.copy2(
            src,
            target
        )

        return

    counter = 1

    while True:

        target = (
            dst
            / f"{src.stem}_{counter}{src.suffix}"
        )

        if not target.exists():

            shutil.copy2(
                src,
                target
            )

            return

        counter += 1


def save_crop(
    image_path,
    label_path,
    output_path,
    target_class_id,
    prefix
):

    try:

        image = Image.open(
            image_path
        ).convert("RGB")

    except Exception as e:

        print(
            f"WARNING: Could not open {image_path}: {e}"
        )

        return 0

    width, height = image.size

    saved = 0

    try:

        with open(
            label_path,
            "r",
            encoding="utf-8"
        ) as f:

            lines = [
                line.strip()
                for line in f
                if line.strip()
            ]

    except Exception as e:

        print(
            f"WARNING: Could not read {label_path}: {e}"
        )

        return 0

    crop_index = 0

    for line in lines:

        parts = line.split()

        if len(parts) != 5:
            continue

        try:

            class_id = int(parts[0])

            x_center = float(parts[1])
            y_center = float(parts[2])
            box_width = float(parts[3])
            box_height = float(parts[4])

        except ValueError:

            continue

        if class_id != target_class_id:
            continue

        # YOLO normalized coordinates -> pixels

        x1 = int(
            (x_center - box_width / 2)
            * width
        )

        y1 = int(
            (y_center - box_height / 2)
            * height
        )

        x2 = int(
            (x_center + box_width / 2)
            * width
        )

        y2 = int(
            (y_center + box_height / 2)
            * height
        )

        # Clamp coordinates

        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(1, min(x2, width))
        y2 = max(1, min(y2, height))

        if x2 <= x1 or y2 <= y1:
            continue

        crop = image.crop(
            (x1, y1, x2, y2)
        )

        output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            output_path
            / f"{prefix}_{crop_index}.jpg"
        )

        crop.save(
            output_file,
            quality=95
        )

        crop_index += 1
        saved += 1

    return saved


# ============================================================
# PADDY DOCTOR
# ============================================================

def prepare_paddy_doctor():

    print()
    print("=" * 60)
    print("PADDY DOCTOR")
    print("=" * 60)

    random.seed(SEED)

    mappings = {
        "blast": "Blast",
        "bacterial_leaf_blight":
            "Bacterial_Leaf_Blight",
    }

    total = 0

    for source_class, final_class in mappings.items():

        source_dir = (
            PADDY_CLEANED
            / source_class
        )

        images = get_images(
            source_dir
        )

        if not images:

            raise RuntimeError(
                f"No images found:\n{source_dir}"
            )

        random.shuffle(images)

        n = len(images)

        train_end = int(
            n * 0.80
        )

        val_end = int(
            n * 0.90
        )

        train_images = images[:train_end]

        val_images = images[
            train_end:val_end
        ]

        test_images = images[
            val_end:
        ]

        print()
        print(
            f"{source_class}: {n} images"
        )

        print(
            f"  Train: {len(train_images)}"
        )

        print(
            f"  Val  : {len(val_images)}"
        )

        print(
            f"  Test : {len(test_images)}"
        )

        for image in train_images:

            copy_image(
                image,
                OUTPUT
                / "train"
                / final_class
            )

        for image in val_images:

            copy_image(
                image,
                OUTPUT
                / "val"
                / final_class
            )

        for image in test_images:

            copy_image(
                image,
                OUTPUT
                / "test"
                / final_class
            )

        total += n

    print()
    print(
        f"Paddy Doctor source images used: {total}"
    )


# ============================================================
# BROWN PLANT HOPPER
# ============================================================

def prepare_bph():

    print()
    print("=" * 60)
    print("BROWN PLANT HOPPER")
    print("=" * 60)

    # BPH class ID in the Roboflow dataset
    # is 0 = brown plant hopper.

    split_map = {
        "train": "train",
        "valid": "val",
        "test": "test",
    }

    total_crops = 0

    for source_split, final_split in split_map.items():

        images_dir = (
            BPH_ROOT
            / source_split
            / "images"
        )

        labels_dir = (
            BPH_ROOT
            / source_split
            / "labels"
        )

        images = get_images(
            images_dir
        )

        split_crops = 0

        for image_path in images:

            label_path = (
                labels_dir
                / f"{image_path.stem}.txt"
            )

            if not label_path.exists():
                continue

            count = save_crop(
                image_path,
                label_path,
                OUTPUT
                / final_split
                / "Brown_Plant_Hopper",
                0,
                image_path.stem
            )

            split_crops += count

        total_crops += split_crops

        print(
            f"{final_split.capitalize():5}: "
            f"{split_crops}"
        )

    print()
    print(
        f"Total BPH crops: {total_crops}"
    )

    if total_crops == 0:

        raise RuntimeError(
            "No BPH crops were generated."
        )


# ============================================================
# SHEATH BLIGHT
# ============================================================

def prepare_sheath_blight():

    print()
    print("=" * 60)
    print("SHEATH BLIGHT")
    print("=" * 60)

    # --------------------------------------------------------
    # Automatically locate the actual Sheath Blight folders
    # --------------------------------------------------------

    label_candidates = []

    for folder in SHEATH_ROOT.rglob("labels"):

        if folder.is_dir():

            # We specifically want the labels folder
            # belonging to Sheath blight.
            if "sheath blight" in str(folder).lower():

                label_candidates.append(folder)

    image_candidates = []

    for folder in SHEATH_ROOT.rglob("*"):

        if folder.is_dir():

            if (
                folder.name.lower() == "sheath blight"
                and "original images" in str(folder).lower()
            ):

                image_candidates.append(folder)

    if not label_candidates:

        raise RuntimeError(
            "Could not automatically locate "
            "Sheath Blight labels folder."
        )

    if not image_candidates:

        raise RuntimeError(
            "Could not automatically locate "
            "Sheath Blight original images folder."
        )

    labels_dir = label_candidates[0]

    originals_dir = image_candidates[0]

    print()
    print(
        f"Labels : {labels_dir}"
    )

    print(
        f"Images : {originals_dir}"
    )

    # --------------------------------------------------------
    # Build original-image lookup
    # --------------------------------------------------------

    original_images = get_images(
        originals_dir
    )

    print()
    print(
        f"Original Sheath Blight images found: "
        f"{len(original_images)}"
    )

    if not original_images:

        raise RuntimeError(
            "No Sheath Blight original images found."
        )

    image_lookup = {}

    for image in original_images:

        image_lookup[
            image.stem.lower()
        ] = image

    # --------------------------------------------------------
    # Find label files
    # --------------------------------------------------------

    label_files = list(
        labels_dir.rglob("*.txt")
    )

    print(
        f"Sheath Blight label files found: "
        f"{len(label_files)}"
    )

    if not label_files:

        raise RuntimeError(
            "No Sheath Blight YOLO label files found."
        )

    # --------------------------------------------------------
    # Match labels to original images
    # --------------------------------------------------------

    pairs = []

    for label_file in label_files:

        image_path = image_lookup.get(
            label_file.stem.lower()
        )

        if image_path is not None:

            pairs.append(
                (
                    image_path,
                    label_file
                )
            )

    print(
        f"Matched image/label pairs: "
        f"{len(pairs)}"
    )

    if not pairs:

        raise RuntimeError(
            "No Sheath Blight image/label pairs matched."
        )

    # --------------------------------------------------------
    # Split by SOURCE IMAGE
    #
    # This is important:
    # crops from the same source image must never
    # appear in different splits.
    # --------------------------------------------------------

    random.seed(SEED)

    random.shuffle(
        pairs
    )

    n = len(pairs)

    train_end = int(
        n * 0.70
    )

    val_end = int(
        n * 0.85
    )

    split_pairs = {

        "train":
            pairs[:train_end],

        "val":
            pairs[
                train_end:val_end
            ],

        "test":
            pairs[
                val_end:
            ],
    }

    # --------------------------------------------------------
    # Extract Sheath Blight crops
    # --------------------------------------------------------

    total_crops = 0

    for split, split_data in split_pairs.items():

        split_crops = 0

        for image_path, label_path in split_data:

            count = save_crop(

                image_path,

                label_path,

                OUTPUT
                / split
                / "Sheath_Blight",

                4,

                image_path.stem
            )

            split_crops += count

        total_crops += split_crops

        print(
            f"{split.capitalize():5}: "
            f"{split_crops}"
        )

    print()
    print(
        f"Total Sheath Blight crops: "
        f"{total_crops}"
    )

    if total_crops == 0:

        raise RuntimeError(
            "No Sheath Blight crops were generated."
        )

# ============================================================
# FINAL COUNTS
# ============================================================

def count_images(folder):

    return len(
        get_images(folder)
    )


def print_final_counts():

    print()
    print("=" * 60)
    print("FINAL PADDY 4-CLASS DATASET")
    print("=" * 60)

    grand_total = 0

    for split in [
        "train",
        "val",
        "test"
    ]:

        print()
        print(
            split.upper()
        )

        split_total = 0

        for cls in CLASSES:

            count = count_images(
                OUTPUT
                / split
                / cls
            )

            print(
                f"{cls:25}: {count}"
            )

            split_total += count

        print(
            f"{'TOTAL':25}: "
            f"{split_total}"
        )

        grand_total += split_total

    print()
    print(
        f"ALL SPLITS TOTAL: "
        f"{grand_total}"
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("DATASET VALIDATION")
    print("=" * 60)

    failed = False

    for split in [
        "train",
        "val",
        "test"
    ]:

        for cls in CLASSES:

            count = count_images(
                OUTPUT
                / split
                / cls
            )

            if count == 0:

                print(
                    f"ERROR: "
                    f"{split}/{cls} is EMPTY"
                )

                failed = True

    if failed:

        raise RuntimeError(
            "Dataset validation failed."
        )

    print(
        "All 4 classes exist "
        "in train, val and test."
    )

    print()
    print("=" * 60)
    print("DATASET PREPARATION COMPLETE")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("Paddy 4-Class Dataset Preparation")
    print("=" * 60)

    clean_output()

    prepare_paddy_doctor()

    prepare_bph()

    prepare_sheath_blight()

    print_final_counts()