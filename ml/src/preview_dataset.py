from pathlib import Path
from PIL import Image, ImageDraw
import random
import math


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_ROOT = Path(
    r"C:\Users\Teja\Downloads\agriculture_dataset\Arecanut_dataset\Arecanut_dataset"
)

OUTPUT_PATH = Path("ml/results/dataset_preview.jpg")

SAMPLES_PER_CLASS = 4
IMAGE_SIZE = 220
LABEL_HEIGHT = 45
COLUMNS = 4

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

random.seed(42)


# ============================================================
# FIND CLASSES AUTOMATICALLY
# ============================================================

TRAIN_DIR = DATASET_ROOT / "train"

if not TRAIN_DIR.exists():
    raise FileNotFoundError(
        f"Training directory not found:\n{TRAIN_DIR}"
    )

CLASSES = sorted(
    folder.name
    for folder in TRAIN_DIR.iterdir()
    if folder.is_dir()
)

print()
print("=" * 60)
print("KrushiSetu Dataset Visual Audit")
print("=" * 60)

print("\nClasses found:")

for class_name in CLASSES:
    print(f" - {class_name}")


# ============================================================
# COLLECT SAMPLE IMAGES
# ============================================================

images = []

for class_name in CLASSES:

    class_dir = TRAIN_DIR / class_name

    files = [
        path
        for path in class_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in VALID_EXTENSIONS
    ]

    selected = random.sample(
        files,
        min(SAMPLES_PER_CLASS, len(files))
    )

    for image_path in selected:
        images.append((class_name, image_path))


# ============================================================
# CREATE CONTACT SHEET
# ============================================================

rows = math.ceil(len(images) / COLUMNS)

canvas = Image.new(
    "RGB",
    (
        COLUMNS * IMAGE_SIZE,
        rows * (IMAGE_SIZE + LABEL_HEIGHT)
    ),
    "white"
)

draw = ImageDraw.Draw(canvas)


# ============================================================
# ADD IMAGES
# ============================================================

for index, (class_name, image_path) in enumerate(images):

    try:

        image = Image.open(image_path).convert("RGB")

        image.thumbnail(
            (
                IMAGE_SIZE - 10,
                IMAGE_SIZE - 10
            )
        )

        x = (index % COLUMNS) * IMAGE_SIZE
        y = (index // COLUMNS) * (
            IMAGE_SIZE + LABEL_HEIGHT
        )

        image_x = (
            x
            + (IMAGE_SIZE - image.width) // 2
        )

        image_y = (
            y
            + (IMAGE_SIZE - image.height) // 2
        )

        canvas.paste(
            image,
            (image_x, image_y)
        )

        draw.text(
            (x + 5, y + IMAGE_SIZE),
            class_name,
            fill="black"
        )

    except Exception as error:

        print(
            f"Could not load image: "
            f"{image_path}"
        )

        print(error)


# ============================================================
# SAVE RESULT
# ============================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

canvas.save(
    OUTPUT_PATH,
    quality=95
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print()
print("=" * 60)
print("Visual audit created successfully")
print("=" * 60)

print(f"Classes sampled : {len(CLASSES)}")
print(f"Images sampled  : {len(images)}")
print(f"Output file     : {OUTPUT_PATH}")

print("=" * 60)