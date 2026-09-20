from pathlib import Path
from hashlib import md5

DATASET_ROOT = Path(
    r"C:\Users\Teja\Downloads\agriculture_dataset\Arecanut_dataset\Arecanut_dataset"
)

TRAIN_DIR = DATASET_ROOT / "train"
TEST_DIR = DATASET_ROOT / "test"

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def image_hash(path):
    hasher = md5()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


print("=" * 60)
print("KrushiSetu Dataset Duplicate Check")
print("=" * 60)

train_hashes = {}
test_hashes = {}

print("\nScanning TRAIN images...")

for path in TRAIN_DIR.rglob("*"):
    if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
        train_hashes[image_hash(path)] = str(path)

print(f"Train images scanned : {len(train_hashes)}")

print("\nScanning TEST images...")

for path in TEST_DIR.rglob("*"):
    if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
        test_hashes[image_hash(path)] = str(path)

print(f"Test images scanned  : {len(test_hashes)}")

duplicates = set(train_hashes.keys()) & set(test_hashes.keys())

print("\n" + "=" * 60)
print("RESULT")
print("=" * 60)

print(f"Exact duplicates     : {len(duplicates)}")

if duplicates:
    print("\nDuplicate images found:")
    print("-" * 60)

    for h in duplicates:
        print("TRAIN:", train_hashes[h])
        print("TEST :", test_hashes[h])
        print("-" * 60)
else:
    print("\nNo exact duplicates found.")

print("\nDuplicate check complete.")