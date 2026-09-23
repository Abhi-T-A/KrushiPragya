from pathlib import Path
import json
import random
import time

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from torchvision.models import EfficientNet_B0_Weights


# =========================================================
# CONFIG
# =========================================================

DATASET = Path("ml/data/black_pepper_3class")
MODEL_DIR = Path("ml/models")
RESULTS_DIR = Path("ml/results/spices")

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "krushisetu_black_pepper_efficientnet_b0_best.pth"
METRICS_PATH = RESULTS_DIR / "black_pepper_training_metrics.json"
HISTORY_PATH = RESULTS_DIR / "black_pepper_training_history.json"
CONFUSION_PATH = RESULTS_DIR / "black_pepper_confusion_matrix.png"

SEED = 42
BATCH_SIZE = 16
HEAD_EPOCHS = 3
MAX_EPOCHS = 25
PATIENCE = 6
LEARNING_RATE_HEAD = 1e-3
LEARNING_RATE_FINE = 1e-4
WEIGHT_DECAY = 1e-4
NUM_WORKERS = 0


# =========================================================
# REPRODUCIBILITY
# =========================================================

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# =========================================================
# HEADER
# =========================================================

print("=" * 70)
print("KRUSHISETU AI — BLACK PEPPER DISEASE CLASSIFIER")
print("=" * 70)

print(f"\nDevice  : {device}")
print(f"Dataset : {DATASET}")
print("Model   : EfficientNet-B0")
print("Classes : 3")


# =========================================================
# TRANSFORMS
# =========================================================

weights = EfficientNet_B0_Weights.DEFAULT

train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2,
        saturation=0.2,
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=weights.transforms().mean,
        std=weights.transforms().std,
    ),
])

eval_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=weights.transforms().mean,
        std=weights.transforms().std,
    ),
])


# =========================================================
# DATASETS
# =========================================================

train_dataset = datasets.ImageFolder(
    DATASET / "train",
    transform=train_transform,
)

val_dataset = datasets.ImageFolder(
    DATASET / "val",
    transform=eval_transform,
)

test_dataset = datasets.ImageFolder(
    DATASET / "test",
    transform=eval_transform,
)


# =========================================================
# VERIFY CLASS MAPPING
# =========================================================

EXPECTED_CLASSES = [
    "Footrot",
    "Pollu_Disease",
    "Slow-Decline",
]

print("\nImageFolder class mapping:")
print(train_dataset.class_to_idx)

if train_dataset.classes != EXPECTED_CLASSES:
    raise RuntimeError(
        f"\nCLASS MAPPING ERROR!\n"
        f"Expected: {EXPECTED_CLASSES}\n"
        f"Found   : {train_dataset.classes}\n"
    )

if val_dataset.classes != EXPECTED_CLASSES:
    raise RuntimeError("Validation class mapping mismatch.")

if test_dataset.classes != EXPECTED_CLASSES:
    raise RuntimeError("Test class mapping mismatch.")

print("\nClass mapping VERIFIED:")
for idx, name in enumerate(EXPECTED_CLASSES):
    print(f"  {idx} -> {name}")


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


print("\nDataset sizes:")
print(f"  Train      : {len(train_dataset)}")
print(f"  Validation : {len(val_dataset)}")
print(f"  Test       : {len(test_dataset)}")


# =========================================================
# CLASS WEIGHTS
# =========================================================

train_targets = np.array(train_dataset.targets)

class_counts = np.bincount(
    train_targets,
    minlength=len(EXPECTED_CLASSES),
)

class_weights = len(train_targets) / (
    len(EXPECTED_CLASSES) * class_counts
)

class_weights = torch.tensor(
    class_weights,
    dtype=torch.float32,
    device=device,
)

print("\nTraining class counts:")
for idx, count in enumerate(class_counts):
    print(f"  {EXPECTED_CLASSES[idx]:<20}: {count}")

print("\nClass weights:")
for idx, weight in enumerate(class_weights):
    print(f"  {EXPECTED_CLASSES[idx]:<20}: {weight.item():.4f}")


# =========================================================
# MODEL
# =========================================================

model = models.efficientnet_b0(
    weights=EfficientNet_B0_Weights.DEFAULT
)

num_features = model.classifier[1].in_features

model.classifier[1] = nn.Linear(
    num_features,
    len(EXPECTED_CLASSES),
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

def train_one_epoch(model, loader, optimizer):
    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)

        predictions = outputs.argmax(dim=1)

        correct += (
            predictions == labels
        ).sum().item()

        total += labels.size(0)

    return (
        running_loss / total,
        correct / total,
    )


@torch.no_grad()
def evaluate(model, loader):

    model.eval()

    running_loss = 0.0
    all_labels = []
    all_predictions = []

    for images, labels in loader:

        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)

        predictions = outputs.argmax(dim=1)

        all_labels.extend(labels.cpu().numpy())
        all_predictions.extend(predictions.cpu().numpy())

    loss = running_loss / len(loader.dataset)

    accuracy = accuracy_score(
        all_labels,
        all_predictions,
    )

    macro_f1 = f1_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0,
    )

    weighted_f1 = f1_score(
        all_labels,
        all_predictions,
        average="weighted",
        zero_division=0,
    )

    return (
        loss,
        accuracy,
        macro_f1,
        weighted_f1,
        all_labels,
        all_predictions,
    )


# =========================================================
# PHASE 1 — TRAIN CLASSIFIER HEAD
# =========================================================

for parameter in model.features.parameters():
    parameter.requires_grad = False

optimizer = torch.optim.AdamW(
    model.classifier.parameters(),
    lr=LEARNING_RATE_HEAD,
    weight_decay=WEIGHT_DECAY,
)


print("\n" + "=" * 70)
print("PHASE 1 — CLASSIFIER HEAD TRAINING")
print("=" * 70)


history = []

best_val_f1 = -1.0
best_epoch = 0
patience_counter = 0
total_start = time.time()


for epoch in range(1, HEAD_EPOCHS + 1):

    start = time.time()

    train_loss, train_acc = train_one_epoch(
        model,
        train_loader,
        optimizer,
    )

    (
        val_loss,
        val_acc,
        val_macro_f1,
        val_weighted_f1,
        _,
        _,
    ) = evaluate(
        model,
        val_loader,
    )

    elapsed = time.time() - start

    print(
        f"Epoch {epoch:02d}/{MAX_EPOCHS} | "
        f"Train Loss {train_loss:.4f} | "
        f"Train Acc {train_acc:.4f} | "
        f"Val Loss {val_loss:.4f} | "
        f"Val Acc {val_acc:.4f} | "
        f"Val Macro-F1 {val_macro_f1:.4f} | "
        f"Time {elapsed:.1f}s"
    )

    history.append({
        "epoch": epoch,
        "phase": "head",
        "train_loss": train_loss,
        "train_accuracy": train_acc,
        "val_loss": val_loss,
        "val_accuracy": val_acc,
        "val_macro_f1": val_macro_f1,
        "val_weighted_f1": val_weighted_f1,
    })


# =========================================================
# PHASE 2 — FINE-TUNE ENTIRE MODEL
# =========================================================

for parameter in model.features.parameters():
    parameter.requires_grad = True

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE_FINE,
    weight_decay=WEIGHT_DECAY,
)

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=2,
)


print("\n" + "=" * 70)
print("PHASE 2 — FULL MODEL FINE-TUNING")
print("=" * 70)


for epoch in range(HEAD_EPOCHS + 1, MAX_EPOCHS + 1):

    start = time.time()

    train_loss, train_acc = train_one_epoch(
        model,
        train_loader,
        optimizer,
    )

    (
        val_loss,
        val_acc,
        val_macro_f1,
        val_weighted_f1,
        _,
        _,
    ) = evaluate(
        model,
        val_loader,
    )

    scheduler.step(val_macro_f1)

    elapsed = time.time() - start

    print(
        f"Epoch {epoch:02d}/{MAX_EPOCHS} | "
        f"Train Loss {train_loss:.4f} | "
        f"Train Acc {train_acc:.4f} | "
        f"Val Loss {val_loss:.4f} | "
        f"Val Acc {val_acc:.4f} | "
        f"Val Macro-F1 {val_macro_f1:.4f} | "
        f"Time {elapsed:.1f}s"
    )

    history.append({
        "epoch": epoch,
        "phase": "fine_tune",
        "train_loss": train_loss,
        "train_accuracy": train_acc,
        "val_loss": val_loss,
        "val_accuracy": val_acc,
        "val_macro_f1": val_macro_f1,
        "val_weighted_f1": val_weighted_f1,
    })

    # -----------------------------------------------------
    # BEST MODEL
    # -----------------------------------------------------

    if val_macro_f1 > best_val_f1:

        best_val_f1 = val_macro_f1
        best_epoch = epoch
        patience_counter = 0

        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "class_names": EXPECTED_CLASSES,
                "class_to_idx": train_dataset.class_to_idx,
                "model_name": "efficientnet_b0",
                "best_val_macro_f1": best_val_f1,
                "best_epoch": best_epoch,
            },
            MODEL_PATH,
        )

        print(
            f"  ✓ Best model saved "
            f"(Val Macro-F1: {best_val_f1:.4f})"
        )

    else:
        patience_counter += 1

        if patience_counter >= PATIENCE:
            print(
                f"\nEarly stopping at epoch {epoch}."
            )
            break


# =========================================================
# LOAD BEST MODEL
# =========================================================

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
)

model.load_state_dict(
    checkpoint["model_state_dict"]
)


# =========================================================
# FINAL TEST EVALUATION
# =========================================================

print("\n" + "=" * 70)
print("FINAL HELD-OUT TEST EVALUATION")
print("=" * 70)

(
    test_loss,
    test_accuracy,
    test_macro_f1,
    test_weighted_f1,
    test_labels,
    test_predictions,
) = evaluate(
    model,
    test_loader,
)


print(f"\nTest Loss       : {test_loss:.4f}")
print(f"Test Accuracy   : {test_accuracy:.4f}")
print(f"Test Macro-F1   : {test_macro_f1:.4f}")
print(f"Test Weighted-F1: {test_weighted_f1:.4f}")


# =========================================================
# CLASSIFICATION REPORT
# =========================================================

report = classification_report(
    test_labels,
    test_predictions,
    target_names=EXPECTED_CLASSES,
    output_dict=True,
    zero_division=0,
)

print("\nPer-class results:")
print(
    classification_report(
        test_labels,
        test_predictions,
        target_names=EXPECTED_CLASSES,
        zero_division=0,
    )
)


# =========================================================
# CONFUSION MATRIX
# =========================================================

cm = confusion_matrix(
    test_labels,
    test_predictions,
)

print("Confusion Matrix:")
print(cm)


try:
    import matplotlib.pyplot as plt

    plt.figure(figsize=(7, 6))

    plt.imshow(cm)

    plt.title("Black Pepper Disease — Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")

    plt.xticks(
        range(len(EXPECTED_CLASSES)),
        EXPECTED_CLASSES,
        rotation=30,
        ha="right",
    )

    plt.yticks(
        range(len(EXPECTED_CLASSES)),
        EXPECTED_CLASSES,
    )

    for i in range(len(EXPECTED_CLASSES)):
        for j in range(len(EXPECTED_CLASSES)):
            plt.text(
                j,
                i,
                cm[i, j],
                ha="center",
                va="center",
            )

    plt.tight_layout()
    plt.savefig(CONFUSION_PATH, dpi=200)
    plt.close()

    print(
        f"\nConfusion matrix saved to: {CONFUSION_PATH}"
    )

except Exception as e:
    print(
        f"\nCould not save confusion matrix: {e}"
    )


# =========================================================
# SAVE METRICS
# =========================================================

metrics = {
    "model": "EfficientNet-B0",
    "dataset": "black_pepper_3class",
    "seed": SEED,
    "device": str(device),
    "class_names": EXPECTED_CLASSES,
    "class_to_idx": train_dataset.class_to_idx,
    "train_size": len(train_dataset),
    "validation_size": len(val_dataset),
    "test_size": len(test_dataset),
    "best_epoch": best_epoch,
    "best_validation_macro_f1": best_val_f1,
    "test_loss": test_loss,
    "test_accuracy": test_accuracy,
    "test_macro_f1": test_macro_f1,
    "test_weighted_f1": test_weighted_f1,
    "classification_report": report,
    "confusion_matrix": cm.tolist(),
    "model_path": str(MODEL_PATH),
}

with open(METRICS_PATH, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

with open(HISTORY_PATH, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2)


# =========================================================
# FINAL
# =========================================================

total_time = time.time() - total_start

print("\n" + "=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)

print(f"Best epoch       : {best_epoch}")
print(f"Best Val Macro-F1: {best_val_f1:.4f}")
print(f"Test Accuracy    : {test_accuracy:.4f}")
print(f"Test Macro-F1    : {test_macro_f1:.4f}")
print(f"Test Weighted-F1 : {test_weighted_f1:.4f}")

print(f"\nModel saved to:")
print(MODEL_PATH)

print(f"\nMetrics saved to:")
print(METRICS_PATH)

print(f"\nTraining time: {total_time / 60:.2f} minutes")

print("=" * 70)