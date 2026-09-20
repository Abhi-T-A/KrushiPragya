from pathlib import Path
from hashlib import md5
import shutil

DATASET_ROOT = Path(
    r"C:\Users\Teja\Downloads\agriculture_dataset\Arecanut_dataset\Arecanut_dataset"
)

OUTPUT_ROOT = Path("ml/data/cleaned")

TRAIN_DIR = DATASET_ROOT / "train"
TEST_DIR = DATASET_ROOT / "test"

CLEAN_TRAIN = OUTPUT_ROOT / "train"
CLEAN_TEST = OUTPUT_ROOT / "test"

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def image_hash(path):
    hasher = md5()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def get_images(directory):
    return [
        p for p in directory.rglob("*")
        if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    ]


print("=" * 65)
print("KrushiSetu Clean Dataset Creation")
print("=" * 65)

# ---------------------------------------------------------
# Create output directories
# ---------------------------------------------------------

if OUTPUT_ROOT.exists():
    print("\nRemoving previous cleaned dataset...")
    shutil.rmtree(OUTPUT_ROOT)

CLEAN_TRAIN.mkdir(parents=True, exist_ok=True)
CLEAN_TEST.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# STEP 1: Clean TRAIN
# Keep only one copy of each exact image
# ---------------------------------------------------------

print("\n[1/3] Processing TRAIN...")

train_images = get_images(TRAIN_DIR)

train_hashes = set()

train_kept = 0
train_duplicates = 0

for image_path in train_images:

    image_id = image_hash(image_path)

    if image_id in train_hashes:
        train_duplicates += 1
        continue

    train_hashes.add(image_id)

    class_name = image_path.parent.name

    destination_dir = CLEAN_TRAIN / class_name
    destination_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(
        image_path,
        destination_dir / image_path.name
    )

    train_kept += 1

print(f"Original train images : {len(train_images)}")
print(f"Train images kept     : {train_kept}")
print(f"Train duplicates removed : {train_duplicates}")

# ---------------------------------------------------------
# STEP 2: Clean TEST
# Remove anything already present in TRAIN
# Also remove duplicate copies inside TEST
# ---------------------------------------------------------

print("\n[2/3] Processing TEST...")

test_images = get_images(TEST_DIR)

test_hashes = set()

test_kept = 0
test_duplicates = 0
test_leakage_removed = 0

for image_path in test_images:

    image_id = image_hash(image_path)

    # Remove if image already exists in TRAIN
    if image_id in train_hashes:
        test_leakage_removed += 1
        continue

    # Remove duplicate copies inside TEST
    if image_id in test_hashes:
        test_duplicates += 1
        continue

    test_hashes.add(image_id)

    class_name = image_path.parent.name

    destination_dir = CLEAN_TEST / class_name
    destination_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(
        image_path,
        destination_dir / image_path.name
    )

    test_kept += 1

print(f"Original test images  : {len(test_images)}")
print(f"Test images kept      : {test_kept}")
print(f"Cross-split leakage removed : {test_leakage_removed}")
print(f"Test duplicates removed      : {test_duplicates}")

# ---------------------------------------------------------
# STEP 3: Final summary
# ---------------------------------------------------------

print("\n[3/3] Cleaning complete.")

print("\n" + "=" * 65)
print("CLEAN DATASET SUMMARY")
print("=" * 65)

print(f"Clean train images : {train_kept}")
print(f"Clean test images  : {test_kept}")

print("\nLocation:")
print(OUTPUT_ROOT.resolve())

print("\n" + "=" * 65)
print("IMPORTANT")
print("=" * 65)

print("Original dataset was NOT modified.")
print("Clean dataset is ready for the next audit.")