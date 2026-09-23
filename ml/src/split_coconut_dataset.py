from pathlib import Path
import random
import shutil

SOURCE = Path("ml/data/coconut_cleaned")
DEST = Path("ml/data/coconut_5class")

SEED = 42

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ---------------------------------------------------------
# RESET OUTPUT
# ---------------------------------------------------------

if DEST.exists():
    shutil.rmtree(DEST)

for split in ["train", "val", "test"]:
    (DEST / split).mkdir(parents=True, exist_ok=True)

random.seed(SEED)

print("=" * 70)
print("KRUSHISETU AI — COCONUT TRAIN/VAL/TEST SPLIT")
print("=" * 70)

total_train = 0
total_val = 0
total_test = 0

# ---------------------------------------------------------
# PROCESS EACH CLASS INDEPENDENTLY
# ---------------------------------------------------------

class_dirs = sorted(
    p for p in SOURCE.iterdir()
    if p.is_dir()
)

for class_dir in class_dirs:

    class_name = class_dir.name

    files = [
        p for p in class_dir.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    ]

    # Deterministic shuffle
    files = sorted(files)
    random.shuffle(files)

    n = len(files)

    # 70 / 15 / 15
    train_end = int(n * 0.70)
    val_end = train_end + int(n * 0.15)

    train_files = files[:train_end]
    val_files = files[train_end:val_end]
    test_files = files[val_end:]

    # Create class directories
    train_dir = DEST / "train" / class_name
    val_dir = DEST / "val" / class_name
    test_dir = DEST / "test" / class_name

    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    # Copy files
    for src in train_files:
        shutil.copy2(src, train_dir / src.name)

    for src in val_files:
        shutil.copy2(src, val_dir / src.name)

    for src in test_files:
        shutil.copy2(src, test_dir / src.name)

    total_train += len(train_files)
    total_val += len(val_files)
    total_test += len(test_files)

    print(
        f"{class_name:<25} "
        f"Train: {len(train_files):>4} | "
        f"Val: {len(val_files):>4} | "
        f"Test: {len(test_files):>4}"
    )

# ---------------------------------------------------------
# FINAL SUMMARY
# ---------------------------------------------------------

print("\n" + "-" * 70)

total = total_train + total_val + total_test

print(f"{'TRAIN':<15} {total_train}")
print(f"{'VALIDATION':<15} {total_val}")
print(f"{'TEST':<15} {total_test}")
print(f"{'TOTAL':<15} {total}")

print("-" * 70)

print(f"\nOutput: {DEST}")
print(f"Random seed: {SEED}")

# ---------------------------------------------------------
# VERIFY COUNTS
# ---------------------------------------------------------

expected_total = 5735

if total != expected_total:
    raise RuntimeError(
        f"Expected {expected_total} images but got {total}"
    )

print("\nPASS — DATASET SPLIT CREATED")
print("=" * 70)