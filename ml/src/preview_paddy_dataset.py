from pathlib import Path
from PIL import Image, ImageDraw
import random
import math


ROOT = Path("ml/data/paddy_cleaned/train")
OUTPUT = Path("ml/results/paddy/paddy_clean_preview.jpg")

SAMPLES_PER_CLASS = 4
IMAGE_SIZE = 180


print("\n========================================")
print("KrushiSetu AI - Paddy Visual Audit")
print("========================================\n")


classes = sorted(
    [
        p.name
        for p in ROOT.iterdir()
        if p.is_dir()
    ]
)

print("Classes found:")
for c in classes:
    print(" -", c)


samples = {}

for class_name in classes:

    files = [
        p
        for p in (ROOT / class_name).iterdir()
        if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
    ]

    random.shuffle(files)

    samples[class_name] = files[:SAMPLES_PER_CLASS]


columns = SAMPLES_PER_CLASS
rows = len(classes)

canvas_width = columns * IMAGE_SIZE
canvas_height = rows * (IMAGE_SIZE + 35)

canvas = Image.new(
    "RGB",
    (canvas_width, canvas_height),
    "white"
)

draw = ImageDraw.Draw(canvas)


for row, class_name in enumerate(classes):

    for col, image_path in enumerate(samples[class_name]):

        try:

            image = Image.open(image_path).convert("RGB")
            image.thumbnail(
                (IMAGE_SIZE - 10, IMAGE_SIZE - 10)
            )

            x = col * IMAGE_SIZE + 5
            y = row * (IMAGE_SIZE + 35) + 5

            canvas.paste(
                image,
                (
                    x + (IMAGE_SIZE - image.width) // 2,
                    y + (IMAGE_SIZE - image.height) // 2
                )
            )

        except Exception as e:

            print(
                f"Could not open {image_path}: {e}"
            )

    label_y = row * (IMAGE_SIZE + 35) + IMAGE_SIZE

    draw.text(
        (5, label_y),
        class_name,
        fill="black"
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

canvas.save(
    OUTPUT,
    quality=95
)

print("\nPreview created:")
print(OUTPUT)

print("\nVisual audit complete.")