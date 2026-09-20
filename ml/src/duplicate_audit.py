from pathlib import Path
from hashlib import md5
from collections import defaultdict

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


def collect_hashes(directory):
    hashes = defaultdict(list)

    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
            hashes[image_hash(path)].append(path)

    return hashes


print("=" * 65)
print("KrushiSetu Dataset Duplicate Audit")
print("=" * 65)

print("\nScanning TRAIN...")
train_hashes = collect_hashes(TRAIN_DIR)

print("Scanning TEST...")
test_hashes = collect_hashes(TEST_DIR)

train_files = sum(len(v) for v in train_hashes.values())
test_files = sum(len(v) for v in test_hashes.values())

train_duplicate_groups = sum(
    1 for v in train_hashes.values() if len(v) > 1
)

test_duplicate_groups = sum(
    1 for v in test_hashes.values() if len(v) > 1
)

train_duplicate_files = sum(
    len(v) - 1 for v in train_hashes.values() if len(v) > 1
)

test_duplicate_files = sum(
    len(v) - 1 for v in test_hashes.values() if len(v) > 1
)

cross_split_hashes = set(train_hashes) & set(test_hashes)

cross_split_train_files = sum(
    len(train_hashes[h]) for h in cross_split_hashes
)

cross_split_test_files = sum(
    len(test_hashes[h]) for h in cross_split_hashes
)

print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)

print(f"Train files                    : {train_files}")
print(f"Unique train images            : {len(train_hashes)}")
print(f"Train duplicate groups         : {train_duplicate_groups}")
print(f"Extra duplicate train files    : {train_duplicate_files}")

print()

print(f"Test files                     : {test_files}")
print(f"Unique test images             : {len(test_hashes)}")
print(f"Test duplicate groups          : {test_duplicate_groups}")
print(f"Extra duplicate test files     : {test_duplicate_files}")

print()

print(f"Cross-split duplicate groups   : {len(cross_split_hashes)}")
print(f"Train files affected           : {cross_split_train_files}")
print(f"Test files affected            : {cross_split_test_files}")

print("\n" + "=" * 65)
print("AUDIT COMPLETE")
print("=" * 65)

if cross_split_hashes:
    print("\nWARNING:")
    print("Exact duplicates exist between TRAIN and TEST.")
    print("Do NOT train on the current dataset yet.")
else:
    print("\nNo train/test exact duplicates found.")