from pathlib import Path
import json
import random
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, transforms, models
from torchvision.models import EfficientNet_B0_Weights
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)
from PIL import Image


# =========================================================
# CONFIG
# =========================================================

DATASET_ROOT = Path("ml/data/coconut_5class")
MODEL_DIR = Path("ml/models")
RESULTS_DIR = Path("ml/results/coconut")

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "krushisetu_coconut_efficientnet_b0_best.pth"

HISTORY_PATH = RESULTS_DIR / "coconut_training_history.json"
METRICS_PATH = RESULTS_DIR / "coconut_training_metrics.json"
CM_PATH = RESULTS_DIR / "coconut_confusion_matrix.png"

SEED = 42

IMAGE_SIZE = 224
BATCH_SIZE = 16

HEAD_EPOCHS = 3
MAX_EPOCHS = 25
PATIENCE = 6

LEARNING_RATE_HEAD = 1e-3
LEARNING_RATE_FINE = 1e-4

NUM_WORKERS = 0


# =========================================================
# EXPLICIT CLASS ORDER
# =========================================================


CLASS_NAMES = [
    "Bud Root Dropping",
    "Bud Rot",
    "Gray Leaf Spot",
    "Leaf Rot",
    "Stem Bleeding",
]

CLASS_DISPLAY_NAMES = {
    "Bud Root Dropping": "Bud Root Dropping",
    "Bud Rot": "Bud Rot",
    "Gray Leaf Spot": "Gray Leaf Spot",
    "Leaf Rot": "Leaf Rot",
    "Stem Bleeding": "Stem Bleeding",
}

# =========================================================
# REPRODUCIBILITY
# =========================================================

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


set_seed(SEED)


# =========================================================
# DEVICE
# =========================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("=" * 75)
print("KRUSHISETU AI — COCONUT DISEASE CLASSIFIER")
print("=" * 75)

print(f"\nDevice: {device}")
print(f"Dataset: {DATASET_ROOT}")
print(f"Model: EfficientNet-B0")
print(f"Classes: {len(CLASS_NAMES)}")


# =========================================================
# TRANSFORMS
# =========================================================

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(12),
    transforms.ColorJitter(
        brightness=0.15,
        contrast=0.15,
        saturation=0.15,
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


# =========================================================
# EXPLICIT DATASET
# =========================================================

class ExplicitImageFolder(Dataset):

    def __init__(self, root, transform=None):

        self.root = Path(root)
        self.transform = transform

        self.samples = []

        for class_index, class_name in enumerate(CLASS_NAMES):

            class_dir = self.root / class_name

            if not class_dir.exists():
                raise FileNotFoundError(
                    f"Missing class directory: {class_dir}"
                )

            files = sorted([
                p for p in class_dir.iterdir()
                if p.is_file()
                and p.suffix.lower() in {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".bmp",
                    ".webp",
                }
            ])

            for path in files:
                self.samples.append(
                    (path, class_index)
                )

        print(
            f"{self.root.name:<10} dataset: "
            f"{len(self.samples)} images"
        )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):

        path, label = self.samples[index]

        image = Image.open(path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label


# =========================================================
# LOAD DATASETS
# =========================================================

train_dataset = ExplicitImageFolder(
    DATASET_ROOT / "train",
    transform=train_transform,
)

val_dataset = ExplicitImageFolder(
    DATASET_ROOT / "val",
    transform=eval_transform,
)

test_dataset = ExplicitImageFolder(
    DATASET_ROOT / "test",
    transform=eval_transform,
)


# =========================================================
# VERIFY EXPECTED COUNTS
# =========================================================

expected_counts = {
    "train": 4013,
    "val": 858,
    "test": 864,
}

actual_counts = {
    "train": len(train_dataset),
    "val": len(val_dataset),
    "test": len(test_dataset),
}

print("\nDataset verification:")

for split in ["train", "val", "test"]:

    print(
        f"{split:<10}: "
        f"{actual_counts[split]} "
        f"(expected {expected_counts[split]})"
    )

    if actual_counts[split] != expected_counts[split]:
        raise RuntimeError(
            f"{split} dataset count mismatch."
        )


# =========================================================
# CLASS COUNTS
# =========================================================

train_counts = np.zeros(len(CLASS_NAMES), dtype=np.int64)

for _, label in train_dataset.samples:
    train_counts[label] += 1

print("\nTraining class counts:")

for i, count in enumerate(train_counts):
    print(
        f"{i}: "
        f"{CLASS_DISPLAY_NAMES[CLASS_NAMES[i]]:<22} "
        f"{count}"
    )


# =========================================================
# CLASS WEIGHTS
# =========================================================

total_train = train_counts.sum()

class_weights = total_train / (
    len(CLASS_NAMES) * train_counts
)

class_weights = torch.tensor(
    class_weights,
    dtype=torch.float32,
    device=device,
)

print("\nClass weights:")

for i, weight in enumerate(class_weights):
    print(
        f"{CLASS_DISPLAY_NAMES[CLASS_NAMES[i]]:<22} "
        f"{weight.item():.4f}"
    )


# =========================================================
# DATALOADERS
# =========================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
)


# =========================================================
# MODEL
# =========================================================

print("\nLoading pretrained EfficientNet-B0...")

weights = EfficientNet_B0_Weights.DEFAULT

model = models.efficientnet_b0(weights=weights)

in_features = model.classifier[1].in_features

model.classifier[1] = nn.Linear(
    in_features,
    len(CLASS_NAMES),
)

model = model.to(device)


# =========================================================
# LOSS
# =========================================================

criterion = nn.CrossEntropyLoss(
    weight=class_weights
)


# =========================================================
# TRAIN / VALIDATION FUNCTIONS
# =========================================================

def run_epoch(model, loader, optimizer=None):

    is_training = optimizer is not None

    if is_training:
        model.train()
    else:
        model.eval()

    running_loss = 0.0
    all_targets = []
    all_predictions = []

    for images, targets in loader:

        images = images.to(device)
        targets = targets.to(device)

        if is_training:
            optimizer.zero_grad()

        with torch.set_grad_enabled(is_training):

            outputs = model(images)

            loss = criterion(
                outputs,
                targets
            )

            if is_training:
                loss.backward()
                optimizer.step()

        running_loss += (
            loss.item() * images.size(0)
        )

        predictions = outputs.argmax(dim=1)

        all_targets.extend(
            targets.cpu().numpy()
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )

    epoch_loss = running_loss / len(loader.dataset)

    accuracy = accuracy_score(
        all_targets,
        all_predictions,
    )

    macro_f1 = precision_recall_fscore_support(
        all_targets,
        all_predictions,
        average="macro",
        zero_division=0,
    )[2]

    weighted_f1 = precision_recall_fscore_support(
        all_targets,
        all_predictions,
        average="weighted",
        zero_division=0,
    )[2]

    return (
        epoch_loss,
        accuracy,
        macro_f1,
        weighted_f1,
    )


# =========================================================
# PHASE 1 — HEAD TRAINING
# =========================================================

print("\n" + "=" * 75)
print("PHASE 1 — CLASSIFIER HEAD TRAINING")
print("=" * 75)

for parameter in model.features.parameters():
    parameter.requires_grad = False

for parameter in model.classifier.parameters():
    parameter.requires_grad = True


optimizer = torch.optim.AdamW(
    model.classifier.parameters(),
    lr=LEARNING_RATE_HEAD,
    weight_decay=1e-4,
)


# =========================================================
# PHASE 2 WILL START AFTER HEAD EPOCHS
# =========================================================

history = []

best_val_loss = float("inf")
best_val_f1 = -1.0

epochs_without_improvement = 0


# =========================================================
# TRAINING LOOP
# =========================================================

for epoch in range(1, MAX_EPOCHS + 1):

    epoch_start = time.time()

    # -----------------------------------------------------
    # Switch to full fine-tuning
    # -----------------------------------------------------

    if epoch == HEAD_EPOCHS + 1:

        print("\n" + "-" * 75)
        print("Switching to FULL FINE-TUNING")
        print("-" * 75)

        for parameter in model.features.parameters():
            parameter.requires_grad = True

        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=LEARNING_RATE_FINE,
            weight_decay=1e-4,
        )

    # -----------------------------------------------------
    # Train
    # -----------------------------------------------------

    train_loss, train_acc, train_macro_f1, train_weighted_f1 = run_epoch(
        model,
        train_loader,
        optimizer,
    )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    val_loss, val_acc, val_macro_f1, val_weighted_f1 = run_epoch(
        model,
        val_loader,
    )

    epoch_time = time.time() - epoch_start

    history.append({
        "epoch": epoch,
        "train_loss": train_loss,
        "train_accuracy": train_acc,
        "train_macro_f1": train_macro_f1,
        "train_weighted_f1": train_weighted_f1,
        "val_loss": val_loss,
        "val_accuracy": val_acc,
        "val_macro_f1": val_macro_f1,
        "val_weighted_f1": val_weighted_f1,
        "time_seconds": epoch_time,
    })

    print(
        f"\nEpoch {epoch:02d}/{MAX_EPOCHS} | "
        f"{epoch_time:.1f}s"
    )

    print(
        f"Train | "
        f"Loss {train_loss:.4f} | "
        f"Acc {train_acc:.4f} | "
        f"Macro-F1 {train_macro_f1:.4f}"
    )

    print(
        f"Val   | "
        f"Loss {val_loss:.4f} | "
        f"Acc {val_acc:.4f} | "
        f"Macro-F1 {val_macro_f1:.4f}"
    )

    # -----------------------------------------------------
    # BEST MODEL
    # -----------------------------------------------------

    improved = (
        val_loss < best_val_loss
        or (
            abs(val_loss - best_val_loss) < 1e-6
            and val_macro_f1 > best_val_f1
        )
    )

    if improved:

        best_val_loss = val_loss
        best_val_f1 = val_macro_f1
        epochs_without_improvement = 0

        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "class_names": CLASS_NAMES,
                "class_display_names": CLASS_DISPLAY_NAMES,
                "image_size": IMAGE_SIZE,
                "model": "EfficientNet-B0",
                "best_val_loss": best_val_loss,
                "best_val_macro_f1": best_val_f1,
                "seed": SEED,
            },
            MODEL_PATH,
        )

        print(
            f"✓ BEST MODEL SAVED "
            f"(Val Loss={val_loss:.4f}, "
            f"Val Macro-F1={val_macro_f1:.4f})"
        )

    else:

        epochs_without_improvement += 1

        print(
            f"No improvement "
            f"({epochs_without_improvement}/{PATIENCE})"
        )

    if epochs_without_improvement >= PATIENCE:

        print("\nEarly stopping triggered.")

        break


# =========================================================
# SAVE TRAINING HISTORY
# =========================================================

with open(
    HISTORY_PATH,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        history,
        f,
        indent=2,
    )


# =========================================================
# LOAD BEST MODEL
# =========================================================

print("\n" + "=" * 75)
print("LOADING BEST VALIDATION CHECKPOINT")
print("=" * 75)

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()


# =========================================================
# FINAL TEST EVALUATION
# =========================================================

print("\n" + "=" * 75)
print("FINAL TEST EVALUATION")
print("=" * 75)

all_targets = []
all_predictions = []

test_loss = 0.0

with torch.no_grad():

    for images, targets in test_loader:

        images = images.to(device)
        targets = targets.to(device)

        outputs = model(images)

        loss = criterion(
            outputs,
            targets,
        )

        test_loss += (
            loss.item() * images.size(0)
        )

        predictions = outputs.argmax(dim=1)

        all_targets.extend(
            targets.cpu().numpy()
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )


test_loss /= len(test_loader.dataset)

test_accuracy = accuracy_score(
    all_targets,
    all_predictions,
)

precision, recall, f1, support = precision_recall_fscore_support(
    all_targets,
    all_predictions,
    labels=list(range(len(CLASS_NAMES))),
    zero_division=0,
)

macro_f1 = np.mean(f1)

weighted_f1 = np.average(
    f1,
    weights=support,
)


# =========================================================
# PRINT RESULTS
# =========================================================

print(f"\nTest Loss      : {test_loss:.4f}")
print(f"Test Accuracy  : {test_accuracy:.4f}")
print(f"Test Macro-F1  : {macro_f1:.4f}")
print(f"Test Weighted-F1: {weighted_f1:.4f}")

print("\nPer-class metrics:")
print("-" * 75)

for i, class_name in enumerate(CLASS_NAMES):

    print(
        f"{CLASS_DISPLAY_NAMES[class_name]:<22} "
        f"Precision: {precision[i]:.4f} | "
        f"Recall: {recall[i]:.4f} | "
        f"F1: {f1[i]:.4f} | "
        f"Support: {support[i]}"
    )


# =========================================================
# CONFUSION MATRIX
# =========================================================

cm = confusion_matrix(
    all_targets,
    all_predictions,
    labels=list(range(len(CLASS_NAMES))),
)

print("\nConfusion Matrix:")
print(cm)


# =========================================================
# CLASSIFICATION REPORT
# =========================================================

report = classification_report(
    all_targets,
    all_predictions,
    labels=list(range(len(CLASS_NAMES))),
    target_names=[
        CLASS_DISPLAY_NAMES[x]
        for x in CLASS_NAMES
    ],
    zero_division=0,
)

print("\nClassification Report:")
print(report)


# =========================================================
# SAVE METRICS
# =========================================================

metrics = {
    "model": "EfficientNet-B0",
    "dataset": "coconut_5class",
    "seed": SEED,
    "device": str(device),
    "classes": CLASS_NAMES,
    "class_display_names": CLASS_DISPLAY_NAMES,
    "train_images": len(train_dataset),
    "validation_images": len(val_dataset),
    "test_images": len(test_dataset),
    "best_validation_loss": best_val_loss,
    "best_validation_macro_f1": best_val_f1,
    "test_loss": test_loss,
    "test_accuracy": test_accuracy,
    "test_macro_f1": macro_f1,
    "test_weighted_f1": weighted_f1,
    "per_class": {
        CLASS_DISPLAY_NAMES[CLASS_NAMES[i]]: {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }
        for i in range(len(CLASS_NAMES))
    },
    "confusion_matrix": cm.tolist(),
}

with open(
    METRICS_PATH,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        metrics,
        f,
        indent=2,
    )


# =========================================================
# SAVE CONFUSION MATRIX IMAGE
# =========================================================

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 7))

im = ax.imshow(cm)

ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("Coconut Disease — EfficientNet-B0 Confusion Matrix")

ax.set_xticks(range(len(CLASS_NAMES)))
ax.set_yticks(range(len(CLASS_NAMES)))

ax.set_xticklabels([
    CLASS_DISPLAY_NAMES[x]
    for x in CLASS_NAMES
], rotation=45, ha="right")

ax.set_yticklabels([
    CLASS_DISPLAY_NAMES[x]
    for x in CLASS_NAMES
])

for i in range(len(CLASS_NAMES)):
    for j in range(len(CLASS_NAMES)):
        ax.text(
            j,
            i,
            cm[i, j],
            ha="center",
            va="center",
        )

fig.colorbar(im, ax=ax)

plt.tight_layout()

plt.savefig(
    CM_PATH,
    dpi=200,
    bbox_inches="tight",
)

plt.close()


# =========================================================
# FINAL
# =========================================================

print("\n" + "=" * 75)
print("COCONUT TRAINING COMPLETE")
print("=" * 75)

print(f"\nBest model:")
print(MODEL_PATH)

print(f"\nTraining history:")
print(HISTORY_PATH)

print(f"\nMetrics:")
print(METRICS_PATH)

print(f"\nConfusion matrix:")
print(CM_PATH)

print("\nClass mapping:")
for i, class_name in enumerate(CLASS_NAMES):
    print(
        f"{i} -> {CLASS_DISPLAY_NAMES[class_name]}"
    )

print("\n" + "=" * 75)