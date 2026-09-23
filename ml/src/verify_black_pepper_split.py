from pathlib import Path
import hashlib

ROOT = Path("ml/data/black_pepper_3class")

splits = {
    "train": set(),
    "val": set(),
    "test": set(),
}

for split in splits:
    files = [
        p for p in (ROOT / split).rglob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]

    for path in files:
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        splits[split].add(file_hash)

print("=" * 70)
print("KRUSHISETU AI — BLACK PEPPER SPLIT LEAKAGE CHECK")
print("=" * 70)

print(f"\ntrain : {len(splits['train'])} unique images")
print(f"val   : {len(splits['val'])} unique images")
print(f"test  : {len(splits['test'])} unique images")

train_val = splits["train"] & splits["val"]
train_test = splits["train"] & splits["test"]
val_test = splits["val"] & splits["test"]

print("\n" + "-" * 60)

print(f"train ↔ val : {len(train_val)} overlapping images")
print(f"train ↔ test: {len(train_test)} overlapping images")
print(f"val ↔ test  : {len(val_test)} overlapping images")

print("\n" + "=" * 70)

if not train_val and not train_test and not val_test:
    print("PASS — ZERO CROSS-SPLIT IMAGE LEAKAGE")
else:
    print("WARNING — CROSS-SPLIT LEAKAGE DETECTED")

print("=" * 70)