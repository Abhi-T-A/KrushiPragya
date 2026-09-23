from pathlib import Path
import hashlib

ROOT = Path("ml/data/coconut_5class")

SPLITS = ["train", "val", "test"]
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

split_hashes = {}

print("=" * 70)
print("KRUSHISETU AI — COCONUT SPLIT LEAKAGE CHECK")
print("=" * 70)

for split in SPLITS:

    split_dir = ROOT / split
    hashes = {}

    for path in split_dir.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in VALID_EXTENSIONS:
            continue

        sha256 = hashlib.sha256()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)

        digest = sha256.hexdigest()

        hashes[digest] = path

    split_hashes[split] = hashes

    print(f"{split:<10}: {len(hashes)} unique images")

print("\n" + "-" * 70)

leakage_found = False

for i in range(len(SPLITS)):
    for j in range(i + 1, len(SPLITS)):

        a = SPLITS[i]
        b = SPLITS[j]

        overlap = set(split_hashes[a]) & set(split_hashes[b])

        print(f"{a} ↔ {b}: {len(overlap)} overlapping images")

        if overlap:
            leakage_found = True

print("-" * 70)

if leakage_found:
    print("FAIL — DATA LEAKAGE DETECTED")
else:
    print("PASS — ZERO CROSS-SPLIT IMAGE LEAKAGE")

print("=" * 70)