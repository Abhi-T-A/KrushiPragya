from pathlib import Path
from collections import Counter, defaultdict
import hashlib

from PIL import Image, ImageOps, ImageDraw


# ============================================================
# PATHS
# ============================================================

DATASET = Path(
    r"C:\Users\Teja\scout\ml\data\paddy_4class"
)

RESULTS = Path(
    r"C:\Users\Teja\scout\ml\results\paddy"
)

RESULTS.mkdir(
    parents=True,
    exist_ok=True
)


CLASSES = [
    "Blast",
    "Bacterial_Leaf_Blight",
    "Brown_Plant_Hopper",
    "Sheath_Blight",
]

SPLITS = [
    "train",
    "val",
    "test",
]

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


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


def sha256_file(path):

    h = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


# ============================================================
# 1. BASIC COUNT AUDIT
# ============================================================

def count_audit():

    print()
    print("=" * 70)
    print("1. CLASS / SPLIT COUNT AUDIT")
    print("=" * 70)

    grand_total = 0

    for split in SPLITS:

        print()
        print(split.upper())

        split_total = 0

        for cls in CLASSES:

            folder = DATASET / split / cls

            count = len(
                get_images(folder)
            )

            print(
                f"{cls:25} : {count}"
            )

            split_total += count

        print(
            f"{'TOTAL':25} : {split_total}"
        )

        grand_total += split_total

    print()
    print(
        f"ALL IMAGES : {grand_total}"
    )


# ============================================================
# 2. CORRUPTION AUDIT
# ============================================================

def corruption_audit():

    print()
    print("=" * 70)
    print("2. IMAGE INTEGRITY / CORRUPTION AUDIT")
    print("=" * 70)

    total = 0
    corrupt = []

    for split in SPLITS:

        for cls in CLASSES:

            folder = DATASET / split / cls

            images = get_images(folder)

            for image_path in images:

                total += 1

                try:

                    with Image.open(image_path) as img:

                        img.verify()

                except Exception as e:

                    corrupt.append(
                        (
                            str(image_path),
                            str(e)
                        )
                    )

    print(
        f"Images checked : {total}"
    )

    print(
        f"Corrupt images : {len(corrupt)}"
    )

    if corrupt:

        print()
        print("CORRUPT FILES:")

        for path, error in corrupt[:20]:

            print(path)
            print(error)

    else:

        print(
            "PASS: No corrupt images found."
        )

    return corrupt


# ============================================================
# 3. HASH DUPLICATE AUDIT
# ============================================================

def duplicate_audit():

    print()
    print("=" * 70)
    print("3. SHA256 DUPLICATE / LEAKAGE AUDIT")
    print("=" * 70)

    hashes = defaultdict(list)

    for split in SPLITS:

        for cls in CLASSES:

            folder = DATASET / split / cls

            for image_path in get_images(folder):

                file_hash = sha256_file(
                    image_path
                )

                hashes[file_hash].append(
                    (
                        split,
                        cls,
                        image_path
                    )
                )

    duplicate_groups = {
        h: files
        for h, files in hashes.items()
        if len(files) > 1
    }

    print(
        f"Unique image hashes : {len(hashes)}"
    )

    print(
        f"Duplicate groups    : "
        f"{len(duplicate_groups)}"
    )

    cross_split_groups = {}

    for h, files in duplicate_groups.items():

        splits_found = {
            item[0]
            for item in files
        }

        if len(splits_found) > 1:

            cross_split_groups[h] = files

    print(
        f"Cross-split duplicate groups : "
        f"{len(cross_split_groups)}"
    )

    # --------------------------------------------------------
    # Report duplicate groups
    # --------------------------------------------------------

    if duplicate_groups:

        print()
        print(
            "First duplicate groups:"
        )

        shown = 0

        for h, files in duplicate_groups.items():

            print()
            print(
                f"Hash: {h[:16]}..."
            )

            for split, cls, path in files:

                print(
                    f"  {split:5} | "
                    f"{cls:25} | "
                    f"{path.name}"
                )

            shown += 1

            if shown >= 10:
                break

    if cross_split_groups:

        print()
        print(
            "WARNING: CROSS-SPLIT DUPLICATES FOUND"
        )

        shown = 0

        for h, files in cross_split_groups.items():

            print()
            print(
                f"Hash: {h[:16]}..."
            )

            for split, cls, path in files:

                print(
                    f"  {split:5} | "
                    f"{cls:25} | "
                    f"{path.name}"
                )

            shown += 1

            if shown >= 10:
                break

    else:

        print()
        print(
            "PASS: No cross-split duplicate images found."
        )

    return duplicate_groups, cross_split_groups


# ============================================================
# 4. CLASS MAPPING AUDIT
# ============================================================

def class_mapping_audit():

    print()
    print("=" * 70)
    print("4. FINAL CLASS MAPPING")
    print("=" * 70)

    mapping = {
        0: "Blast",
        1: "Bacterial_Leaf_Blight",
        2: "Brown_Plant_Hopper",
        3: "Sheath_Blight",
    }

    for index, name in mapping.items():

        print(
            f"{index} -> {name}"
        )

    print()
    print(
        "This is the taxonomy used for model training."
    )


# ============================================================
# 5. VISUAL PREVIEW
# ============================================================

def visual_preview():

    print()
    print("=" * 70)
    print("5. VISUAL PREVIEW")
    print("=" * 70)

    preview_images = []

    for cls in CLASSES:

        folder = (
            DATASET
            / "train"
            / cls
        )

        images = get_images(
            folder
        )

        if images:

            # deterministic selection
            images = sorted(
                images,
                key=lambda x: x.name
            )

            # Pick up to 4 per class
            preview_images.extend(
                [
                    (cls, image)
                    for image in images[:4]
                ]
            )

    tile_width = 300
    tile_height = 270

    columns = 4

    rows = (
        len(preview_images)
        + columns
        - 1
    ) // columns

    canvas = Image.new(
        "RGB",
        (
            columns * tile_width,
            rows * tile_height
        ),
        "white"
    )

    draw = ImageDraw.Draw(
        canvas
    )

    for index, (cls, image_path) in enumerate(
        preview_images
    ):

        try:

            img = Image.open(
                image_path
            ).convert("RGB")

            img = ImageOps.contain(
                img,
                (
                    tile_width - 20,
                    tile_height - 55
                )
            )

            x = (
                index % columns
            ) * tile_width

            y = (
                index // columns
            ) * tile_height

            image_x = (
                x
                + (
                    tile_width
                    - img.width
                ) // 2
            )

            image_y = y + 10

            canvas.paste(
                img,
                (
                    image_x,
                    image_y
                )
            )

            draw.text(
                (
                    x + 10,
                    tile_height
                    * (
                        index // columns
                    )
                    + tile_height
                    - 35
                ),
                cls,
                fill="black"
            )

        except Exception:
            pass

    preview_path = (
        RESULTS
        / "paddy_4class_preview.jpg"
    )

    canvas.save(
        preview_path,
        quality=95
    )

    print(
        f"Preview saved to:"
    )

    print(
        preview_path
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("KRUSHISETU AI — PADDY 4-CLASS DATASET AUDIT")
    print("=" * 70)

    count_audit()

    corrupt = corruption_audit()

    duplicates, cross_split = duplicate_audit()

    class_mapping_audit()

    visual_preview()

    print()
    print("=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)

    if corrupt:

        print(
            "RESULT: REVIEW REQUIRED — corrupt images found."
        )

    elif cross_split:

        print(
            "RESULT: REVIEW REQUIRED — "
            "cross-split duplicates found."
        )

    else:

        print(
            "RESULT: PASS — dataset ready for training."
        )

    print()