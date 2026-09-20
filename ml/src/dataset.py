from pathlib import Path

import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from sklearn.model_selection import train_test_split


# ============================================================
# KrushiSetu AI - Dataset Pipeline
# ============================================================

DATASET_ROOT = Path("ml/data/arecanut_6class")

TRAIN_DIR = DATASET_ROOT / "train"
TEST_DIR = DATASET_ROOT / "test"

IMAGE_SIZE = 224
BATCH_SIZE = 32
VALIDATION_SIZE = 0.20
NUM_WORKERS = 0
SEED = 42


# ============================================================
# Transforms
# ============================================================

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(15),
    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2,
        saturation=0.2,
        hue=0.05
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


# ============================================================
# Dataset Pipeline
# ============================================================

def create_datasets():

    if not TRAIN_DIR.exists():
        raise FileNotFoundError(
            f"Training directory not found: {TRAIN_DIR}"
        )

    if not TEST_DIR.exists():
        raise FileNotFoundError(
            f"Test directory not found: {TEST_DIR}"
        )

    # Load training dataset without transforms first
    base_dataset = datasets.ImageFolder(TRAIN_DIR)

    # Load separate copies so train/validation can have
    # different transforms
    train_dataset_full = datasets.ImageFolder(
        TRAIN_DIR,
        transform=train_transform
    )

    validation_dataset_full = datasets.ImageFolder(
        TRAIN_DIR,
        transform=eval_transform
    )

    test_dataset = datasets.ImageFolder(
        TEST_DIR,
        transform=eval_transform
    )

    targets = base_dataset.targets

    indices = list(range(len(targets)))

    # --------------------------------------------------------
    # Stratified train/validation split
    # --------------------------------------------------------

    train_indices, validation_indices = train_test_split(
        indices,
        test_size=VALIDATION_SIZE,
        random_state=SEED,
        stratify=targets
    )

    train_dataset = Subset(
        train_dataset_full,
        train_indices
    )

    validation_dataset = Subset(
        validation_dataset_full,
        validation_indices
    )

    return (
        train_dataset,
        validation_dataset,
        test_dataset,
        base_dataset.classes
    )


# ============================================================
# DataLoaders
# ============================================================

def create_dataloaders():

    (
        train_dataset,
        validation_dataset,
        test_dataset,
        classes
    ) = create_datasets()

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available()
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available()
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available()
    )

    return (
        train_loader,
        validation_loader,
        test_loader,
        classes
    )


# ============================================================
# Main - Dataset Verification
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("KrushiSetu AI Dataset Pipeline")
    print("=" * 60)

    (
        train_loader,
        validation_loader,
        test_loader,
        classes
    ) = create_dataloaders()

    print()
    print("Classes:")

    for index, class_name in enumerate(classes):
        print(f"{index}: {class_name}")

    print()
    print("-" * 60)

    print(f"Training samples   : {len(train_loader.dataset)}")
    print(f"Validation samples : {len(validation_loader.dataset)}")
    print(f"Test samples       : {len(test_loader.dataset)}")

    print()
    print(f"Training batches   : {len(train_loader)}")
    print(f"Validation batches : {len(validation_loader)}")
    print(f"Test batches       : {len(test_loader)}")

    print()
    print(f"Batch size         : {BATCH_SIZE}")
    print(f"Image size         : {IMAGE_SIZE}x{IMAGE_SIZE}")

    print()
    print("=" * 60)
    print("Dataset pipeline ready.")
    print("=" * 60)