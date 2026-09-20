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


def collect_images(directory, split_name):
    records = defaultdict(list)

    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
            class_name = path.parent.name
            image_id = image_hash(path)

            records[image_id].append({
                "split": split_name,
                "class": class_name,
                "path": str(path)
            })

    return records


print("=" * 65)
print("KrushiSetu Duplicate Label Audit")
print("=" * 65)

print("\nScanning TRAIN...")
train = collect_images(TRAIN_DIR, "TRAIN")

print("Scanning TEST...")
test = collect_images(TEST_DIR, "TEST")

all_hashes = set(train) | set(test)

cross_split_conflicts = []
cross_split_same_class = []

within_train_conflicts = []
within_test_conflicts = []

for image_id in all_hashes:

    train_records = train.get(image_id, [])
    test_records = test.get(image_id, [])

    train_classes = set(r["class"] for r in train_records)
    test_classes = set(r["class"] for r in test_records)

    # Same image exists in both train and test
    if train_records and test_records:

        if train_classes != test_classes or len(train_classes | test_classes) > 1:
            cross_split_conflicts.append(
                (image_id, train_records, test_records)
            )
        else:
            cross_split_same_class.append(
                (image_id, train_records, test_records)
            )

    # Duplicate image inside TRAIN with different labels
    if len(train_classes) > 1:
        within_train_conflicts.append(
            (image_id, train_records)
        )

    # Duplicate image inside TEST with different labels
    if len(test_classes) > 1:
        within_test_conflicts.append(
            (image_id, test_records)
        )


print("\n" + "=" * 65)
print("RESULT")
print("=" * 65)

print(
    f"Cross-split duplicate groups (same class) : "
    f"{len(cross_split_same_class)}"
)

print(
    f"Cross-split label conflicts               : "
    f"{len(cross_split_conflicts)}"
)

print(
    f"Train internal label conflicts             : "
    f"{len(within_train_conflicts)}"
)

print(
    f"Test internal label conflicts              : "
    f"{len(within_test_conflicts)}"
)


if cross_split_conflicts:

    print("\n" + "=" * 65)
    print("CROSS-SPLIT LABEL CONFLICTS")
    print("=" * 65)

    for image_id, train_records, test_records in cross_split_conflicts:

        print("\nHASH:", image_id)

        print("TRAIN:")
        for record in train_records:
            print(
                f"  {record['class']} -> {record['path']}"
            )

        print("TEST:")
        for record in test_records:
            print(
                f"  {record['class']} -> {record['path']}"
            )


if within_train_conflicts:

    print("\n" + "=" * 65)
    print("TRAIN INTERNAL LABEL CONFLICTS")
    print("=" * 65)

    for image_id, records in within_train_conflicts:

        print("\nHASH:", image_id)

        for record in records:
            print(
                f"  {record['class']} -> {record['path']}"
            )


if within_test_conflicts:

    print("\n" + "=" * 65)
    print("TEST INTERNAL LABEL CONFLICTS")
    print("=" * 65)

    for image_id, records in within_test_conflicts:

        print("\nHASH:", image_id)

        for record in records:
            print(
                f"  {record['class']} -> {record['path']}"
            )


print("\n" + "=" * 65)
print("LABEL AUDIT COMPLETE")
print("=" * 65)