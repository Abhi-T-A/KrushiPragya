from pathlib import Path
import hashlib

DATASET = Path("ml/data/turmeric_4class")

SPLITS = [
    "train",
    "val",
    "test"
]


def get_hashes(split):

    hashes = {}

    split_dir = DATASET / split

    for path in split_dir.rglob("*"):

        if not path.is_file():
            continue

        digest = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()

        hashes[digest] = path

    return hashes


print("=" * 70)
print("KRUSHISETU AI — TURMERIC SPLIT LEAKAGE CHECK")
print("=" * 70)


split_hashes = {}


for split in SPLITS:

    split_hashes[split] = get_hashes(
        split
    )

    print(
        f"\n{split:<6}: "
        f"{len(split_hashes[split])} unique images"
    )


print()
print("-" * 60)


pairs = [
    ("train", "val"),
    ("train", "test"),
    ("val", "test")
]


leakage_found = False


for split_a, split_b in pairs:

    overlap = (
        set(split_hashes[split_a])
        &
        set(split_hashes[split_b])
    )

    print(
        f"{split_a} ↔ {split_b}: "
        f"{len(overlap)} overlapping images"
    )

    if overlap:
        leakage_found = True


print()
print("=" * 70)


if leakage_found:

    print(
        "FAIL — CROSS-SPLIT IMAGE LEAKAGE DETECTED"
    )

else:

    print(
        "PASS — ZERO CROSS-SPLIT IMAGE LEAKAGE"
    )


print("=" * 70)