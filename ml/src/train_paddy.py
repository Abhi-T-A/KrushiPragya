from pathlib import Path
import copy
import json
import time

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score,
)

import matplotlib.pyplot as plt


# ============================================================
# CONFIG
# ============================================================

DATASET_DIR = Path(r"C:\Users\Teja\scout\ml\data\paddy_4class")
MODEL_DIR = Path(r"C:\Users\Teja\scout\ml\models")
RESULT_DIR = Path(r"C:\Users\Teja\scout\ml\results\paddy")

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

NUM_CLASSES = 4
IMAGE_SIZE = 224

BATCH_SIZE = 16
NUM_EPOCHS = 25

HEAD_EPOCHS = 3
LEARNING_RATE_HEAD = 1e-3
LEARNING_RATE_FINE = 1e-4

PATIENCE = 6

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 70)
print("KRUSHISETU AI — PADDY 4-CLASS TRAINING")
print("=" * 70)

print(f"\nDevice: {DEVICE}")
print(f"Dataset: {DATASET_DIR}")

if DEVICE.type == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")


# ============================================================
# CLASS ORDER — LOCKED
# ============================================================

EXPECTED_CLASSES = [
    "Blast",
    "Bacterial_Leaf_Blight",
    "Brown_Plant_Hopper",
    "Sheath_Blight",
]

print("\nExpected classes:")
for i, name in enumerate(EXPECTED_CLASSES):
    print(f"  {i} -> {name}")


# ============================================================
# DATA TRANSFORMS
# ============================================================

imagenet_mean = [0.485, 0.456, 0.406]
imagenet_std = [0.229, 0.224, 0.225]

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2,
        saturation=0.2,
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        imagenet_mean,
        imagenet_std
    ),
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        imagenet_mean,
        imagenet_std
    ),
])


# ============================================================
# DATASETS
# ============================================================

train_dataset = datasets.ImageFolder(
    DATASET_DIR / "train",
    transform=train_transform,
)

val_dataset = datasets.ImageFolder(
    DATASET_DIR / "val",
    transform=eval_transform,
)

test_dataset = datasets.ImageFolder(
    DATASET_DIR / "test",
    transform=eval_transform,
)


# ============================================================
# VERIFY CLASS MAPPING
# ============================================================

print("\nDetected ImageFolder classes:")

print("Train:", train_dataset.class_to_idx)
print("Val  :", val_dataset.class_to_idx)
print("Test :", test_dataset.class_to_idx)

# ImageFolder assigns class indices from the folder names.
# The actual alphabetical mapping is:
EXPECTED_MAPPING = {
    "Bacterial_Leaf_Blight": 0,
    "Blast": 1,
    "Brown_Plant_Hopper": 2,
    "Sheath_Blight": 3,
}

print("\nVerified ImageFolder mapping:")

for name, index in EXPECTED_MAPPING.items():
    print(f"  {index} -> {name}")


if train_dataset.class_to_idx != EXPECTED_MAPPING:
    raise RuntimeError(
        "\nERROR: Train class mapping is unexpected.\n"
        f"Expected: {EXPECTED_MAPPING}\n"
        f"Found:    {train_dataset.class_to_idx}"
    )

if val_dataset.class_to_idx != EXPECTED_MAPPING:
    raise RuntimeError(
        "\nERROR: Validation class mapping is unexpected."
    )

if test_dataset.class_to_idx != EXPECTED_MAPPING:
    raise RuntimeError(
        "\nERROR: Test class mapping is unexpected."
    )


# ============================================================
# DATA COUNTS
# ============================================================

train_targets = torch.tensor(train_dataset.targets)

class_counts = torch.bincount(
    train_targets,
    minlength=NUM_CLASSES
).float()

print("\nTraining class counts:")

for i, count in enumerate(class_counts):
    print(
        f"  {EXPECTED_CLASSES[i]:25s}: "
        f"{int(count.item())}"
    )

print(f"\nTrain total: {len(train_dataset)}")
print(f"Val total  : {len(val_dataset)}")
print(f"Test total : {len(test_dataset)}")


# ============================================================
# CLASS WEIGHTS
# ============================================================

class_weights = class_counts.sum() / (
    NUM_CLASSES * class_counts
)

class_weights = class_weights.to(DEVICE)

print("\nClass weights:")

for i, weight in enumerate(class_weights):
    print(
        f"  {EXPECTED_CLASSES[i]:25s}: "
        f"{weight.item():.4f}"
    )


# ============================================================
# DATALOADERS
# ============================================================

NUM_WORKERS = 0

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
)


# ============================================================
# MODEL
# ============================================================

print("\nLoading pretrained EfficientNet-B0...")

weights = models.EfficientNet_B0_Weights.DEFAULT

model = models.efficientnet_b0(
    weights=weights
)

in_features = model.classifier[1].in_features

model.classifier[1] = nn.Linear(
    in_features,
    NUM_CLASSES
)

model = model.to(DEVICE)


# ============================================================
# PHASE 1 — CLASSIFIER HEAD
# ============================================================

for parameter in model.features.parameters():
    parameter.requires_grad = False

print("\nBackbone frozen.")
print("Phase 1: training classifier head.")


criterion = nn.CrossEntropyLoss(
    weight=class_weights
)

optimizer = optim.AdamW(
    model.classifier.parameters(),
    lr=LEARNING_RATE_HEAD,
    weight_decay=1e-4,
)


# ============================================================
# TRAINING FUNCTION
# ============================================================

def run_epoch(model, loader, criterion, optimizer=None):

    is_training = optimizer is not None

    if is_training:
        model.train()
    else:
        model.eval()

    running_loss = 0.0
    all_predictions = []
    all_labels = []

    for images, labels in loader:

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        if is_training:
            optimizer.zero_grad()

        with torch.set_grad_enabled(is_training):

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            predictions = outputs.argmax(
                dim=1
            )

            if is_training:
                loss.backward()
                optimizer.step()

        running_loss += (
            loss.item() * images.size(0)
        )

        all_predictions.extend(
            predictions.detach().cpu().tolist()
        )

        all_labels.extend(
            labels.detach().cpu().tolist()
        )

    epoch_loss = (
        running_loss / len(loader.dataset)
    )

    epoch_accuracy = accuracy_score(
        all_labels,
        all_predictions
    )

    epoch_f1 = f1_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0,
    )

    return (
        epoch_loss,
        epoch_accuracy,
        epoch_f1,
    )


# ============================================================
# VALIDATION
# ============================================================

def evaluate_validation():

    model.eval()

    return run_epoch(
        model,
        val_loader,
        criterion,
        optimizer=None,
    )


# ============================================================
# TRAINING HISTORY
# ============================================================

history = {
    "train_loss": [],
    "train_accuracy": [],
    "train_f1": [],
    "val_loss": [],
    "val_accuracy": [],
    "val_f1": [],
}

best_val_f1 = -1.0
best_state = copy.deepcopy(model.state_dict())

epochs_without_improvement = 0

start_time = time.time()


# ============================================================
# PHASE 1
# ============================================================

for epoch in range(1, HEAD_EPOCHS + 1):

    train_loss, train_acc, train_f1 = run_epoch(
        model,
        train_loader,
        criterion,
        optimizer,
    )

    val_loss, val_acc, val_f1 = evaluate_validation()

    history["train_loss"].append(train_loss)
    history["train_accuracy"].append(train_acc)
    history["train_f1"].append(train_f1)

    history["val_loss"].append(val_loss)
    history["val_accuracy"].append(val_acc)
    history["val_f1"].append(val_f1)

    print(
        f"\nEpoch {epoch}/{NUM_EPOCHS}"
    )

    print(
        f"Train Loss: {train_loss:.4f} | "
        f"Train Acc: {train_acc:.4f} | "
        f"Train Macro-F1: {train_f1:.4f}"
    )

    print(
        f"Val Loss:   {val_loss:.4f} | "
        f"Val Acc:   {val_acc:.4f} | "
        f"Val Macro-F1: {val_f1:.4f}"
    )

    if val_f1 > best_val_f1:

        best_val_f1 = val_f1
        best_state = copy.deepcopy(
            model.state_dict()
        )

        epochs_without_improvement = 0

        print("  ✓ New best validation Macro-F1")

    else:

        epochs_without_improvement += 1


# ============================================================
# PHASE 2 — FINE-TUNING
# ============================================================

print("\n" + "=" * 70)
print("PHASE 2 — FINE-TUNING BACKBONE")
print("=" * 70)

for parameter in model.features.parameters():
    parameter.requires_grad = True

optimizer = optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE_FINE,
    weight_decay=1e-4,
)


# ============================================================
# REMAINING EPOCHS
# ============================================================

for epoch in range(
    HEAD_EPOCHS + 1,
    NUM_EPOCHS + 1
):

    train_loss, train_acc, train_f1 = run_epoch(
        model,
        train_loader,
        criterion,
        optimizer,
    )

    val_loss, val_acc, val_f1 = evaluate_validation()

    history["train_loss"].append(train_loss)
    history["train_accuracy"].append(train_acc)
    history["train_f1"].append(train_f1)

    history["val_loss"].append(val_loss)
    history["val_accuracy"].append(val_acc)
    history["val_f1"].append(val_f1)

    print(
        f"\nEpoch {epoch}/{NUM_EPOCHS}"
    )

    print(
        f"Train Loss: {train_loss:.4f} | "
        f"Train Acc: {train_acc:.4f} | "
        f"Train Macro-F1: {train_f1:.4f}"
    )

    print(
        f"Val Loss:   {val_loss:.4f} | "
        f"Val Acc:   {val_acc:.4f} | "
        f"Val Macro-F1: {val_f1:.4f}"
    )

    if val_f1 > best_val_f1:

        best_val_f1 = val_f1

        best_state = copy.deepcopy(
            model.state_dict()
        )

        epochs_without_improvement = 0

        print("  ✓ New best validation Macro-F1")

    else:

        epochs_without_improvement += 1

    if epochs_without_improvement >= PATIENCE:

        print(
            f"\nEarly stopping after "
            f"{PATIENCE} epochs without improvement."
        )

        break


# ============================================================
# LOAD BEST MODEL
# ============================================================

model.load_state_dict(best_state)

print("\n" + "=" * 70)
print("BEST VALIDATION MODEL RESTORED")
print("=" * 70)

print(
    f"Best validation Macro-F1: "
    f"{best_val_f1:.4f}"
)


# ============================================================
# SAVE MODEL
# ============================================================

model_path = (
    MODEL_DIR /
    "krushisetu_paddy_efficientnet_b0_best.pth"
)

torch.save(
    {
        "model_state_dict": model.state_dict(),
        "classes": EXPECTED_CLASSES,
        "num_classes": NUM_CLASSES,
        "image_size": IMAGE_SIZE,
        "best_val_macro_f1": best_val_f1,
    },
    model_path,
)

print(
    f"\nModel saved to:\n{model_path}"
)


# ============================================================
# FINAL TEST EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL TEST EVALUATION")
print("=" * 70)

model.eval()

all_test_labels = []
all_test_predictions = []

with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(DEVICE)

        outputs = model(images)

        predictions = outputs.argmax(
            dim=1
        )

        all_test_predictions.extend(
            predictions.cpu().tolist()
        )

        all_test_labels.extend(
            labels.tolist()
        )


test_accuracy = accuracy_score(
    all_test_labels,
    all_test_predictions
)

test_macro_f1 = f1_score(
    all_test_labels,
    all_test_predictions,
    average="macro",
    zero_division=0,
)

test_weighted_f1 = f1_score(
    all_test_labels,
    all_test_predictions,
    average="weighted",
    zero_division=0,
)

print(
    f"\nTest Accuracy : {test_accuracy:.4f}"
)

print(
    f"Test Macro F1 : {test_macro_f1:.4f}"
)

print(
    f"Test Weighted F1: {test_weighted_f1:.4f}"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

report = classification_report(
    all_test_labels,
    all_test_predictions,
    target_names=EXPECTED_CLASSES,
    digits=4,
    zero_division=0,
)

print("\nClassification Report:")
print(report)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    all_test_labels,
    all_test_predictions,
)

print("\nConfusion Matrix:")
print(cm)


# ============================================================
# SAVE CONFUSION MATRIX
# ============================================================

plt.figure(figsize=(8, 7))

plt.imshow(cm)

plt.title("Paddy 4-Class Confusion Matrix")

plt.xticks(
    range(NUM_CLASSES),
    EXPECTED_CLASSES,
    rotation=45,
    ha="right",
)

plt.yticks(
    range(NUM_CLASSES),
    EXPECTED_CLASSES,
)

plt.xlabel("Predicted")
plt.ylabel("Actual")

for i in range(NUM_CLASSES):
    for j in range(NUM_CLASSES):
        plt.text(
            j,
            i,
            cm[i, j],
            ha="center",
            va="center",
        )

plt.tight_layout()

cm_path = (
    RESULT_DIR /
    "paddy_confusion_matrix.png"
)

plt.savefig(
    cm_path,
    dpi=200,
)

plt.close()


# ============================================================
# TRAINING CURVES
# ============================================================

epochs = range(
    1,
    len(history["train_loss"]) + 1
)

plt.figure(figsize=(8, 6))

plt.plot(
    epochs,
    history["train_loss"],
    label="Train Loss",
)

plt.plot(
    epochs,
    history["val_loss"],
    label="Validation Loss",
)

plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Paddy Training / Validation Loss")
plt.legend()
plt.tight_layout()

loss_path = (
    RESULT_DIR /
    "paddy_training_loss.png"
)

plt.savefig(
    loss_path,
    dpi=200,
)

plt.close()


# ============================================================
# SAVE METRICS
# ============================================================

metrics = {
    "classes": EXPECTED_CLASSES,
    "train_images": len(train_dataset),
    "val_images": len(val_dataset),
    "test_images": len(test_dataset),
    "test_accuracy": test_accuracy,
    "test_macro_f1": test_macro_f1,
    "test_weighted_f1": test_weighted_f1,
    "best_val_macro_f1": best_val_f1,
    "confusion_matrix": cm.tolist(),
}

metrics_path = (
    RESULT_DIR /
    "paddy_training_metrics.json"
)

with open(
    metrics_path,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        metrics,
        f,
        indent=2,
    )


# ============================================================
# SAVE HISTORY
# ============================================================

history_path = (
    RESULT_DIR /
    "paddy_training_history.json"
)

with open(
    history_path,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        history,
        f,
        indent=2,
    )


elapsed = (
    time.time() - start_time
) / 60


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("PADDY TRAINING COMPLETE")
print("=" * 70)

print(f"\nTest Accuracy   : {test_accuracy:.4f}")
print(f"Test Macro-F1   : {test_macro_f1:.4f}")
print(f"Test Weighted-F1: {test_weighted_f1:.4f}")

print(f"\nModel:")
print(model_path)

print(f"\nConfusion matrix:")
print(cm_path)

print(f"\nMetrics:")
print(metrics_path)

print(f"\nTraining time: {elapsed:.2f} minutes")

print("\n" + "=" * 70)