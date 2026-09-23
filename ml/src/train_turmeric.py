"""
KRUSHISETU AI — TURMERIC LEAF CLASSIFIER

Model:
    EfficientNet-B0 pretrained on ImageNet

Dataset:
    ml/data/turmeric_4class

Classes:
    Aphids_Disease
    Blotch
    Healthy_Leaf
    Leaf_Spot

Important:
    Only ORIGINAL turmeric images are used.
    The 3,496 augmented source images were excluded
    to avoid hidden train/test leakage.

Training:
    Phase 1 -> classifier head
    Phase 2 -> full fine-tuning

Checkpoint selection:
    Validation Macro-F1

Final evaluation:
    Untouched test set

Seed:
    42
"""

from pathlib import Path
import json
import random
import time

import numpy as np
import torch
import torch.nn as nn

from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

DATA_DIR = Path("ml/data/turmeric_4class")

MODEL_DIR = Path("ml/models")
RESULT_DIR = Path("ml/results/spices")

MODEL_PATH = (
    MODEL_DIR /
    "krushisetu_turmeric_efficientnet_b0_best.pth"
)

METRICS_PATH = (
    RESULT_DIR /
    "turmeric_training_metrics.json"
)

CONFUSION_PATH = (
    RESULT_DIR /
    "turmeric_confusion_matrix.png"
)

IMAGE_SIZE = 224
BATCH_SIZE = 16

HEAD_EPOCHS = 3
MAX_TOTAL_EPOCHS = 25

HEAD_LR = 1e-3
FINE_TUNE_LR = 1e-4

WEIGHT_DECAY = 1e-4
PATIENCE = 6

NUM_WORKERS = 0


# ============================================================
# REPRODUCIBILITY
# ============================================================

def set_seed(seed=42):

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


set_seed(SEED)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


print("=" * 70)
print("KRUSHISETU AI — TURMERIC LEAF CLASSIFIER")
print("=" * 70)

print(f"Device : {device}")
print(f"Dataset: {DATA_DIR}")
print()


# ============================================================
# OUTPUT DIRECTORIES
# ============================================================

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DATA TRANSFORMS
# ============================================================

train_transform = transforms.Compose([

    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.RandomHorizontalFlip(
        p=0.5
    ),

    transforms.RandomVerticalFlip(
        p=0.5
    ),

    transforms.RandomRotation(
        15
    ),

    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2,
        saturation=0.2
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[
            0.485,
            0.456,
            0.406
        ],
        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])


eval_transform = transforms.Compose([

    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[
            0.485,
            0.456,
            0.406
        ],
        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])


# ============================================================
# DATASET PATHS
# ============================================================

train_dir = DATA_DIR / "train"
val_dir = DATA_DIR / "val"
test_dir = DATA_DIR / "test"


for directory in [
    train_dir,
    val_dir,
    test_dir
]:

    if not directory.exists():

        raise FileNotFoundError(
            f"Dataset directory not found: {directory}"
        )


# ============================================================
# LOAD DATASETS
# ============================================================

train_dataset = datasets.ImageFolder(
    train_dir,
    transform=train_transform
)

val_dataset = datasets.ImageFolder(
    val_dir,
    transform=eval_transform
)

test_dataset = datasets.ImageFolder(
    test_dir,
    transform=eval_transform
)


# ============================================================
# VERIFY CLASS MAPPING
# ============================================================

print("Class mapping:")

for class_name, class_id in train_dataset.class_to_idx.items():

    print(
        f"  {class_id} -> {class_name}"
    )

print()


if train_dataset.class_to_idx != val_dataset.class_to_idx:

    raise RuntimeError(
        "Train and validation class mappings do not match."
    )


if train_dataset.class_to_idx != test_dataset.class_to_idx:

    raise RuntimeError(
        "Train and test class mappings do not match."
    )


class_names = train_dataset.classes

num_classes = len(class_names)


if num_classes != 4:

    raise RuntimeError(
        f"Expected 4 classes, found {num_classes}: "
        f"{class_names}"
    )


# ============================================================
# DATA LOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available()
)

val_loader = DataLoader(
    val_dataset,
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


print(
    f"Train images: {len(train_dataset)}"
)

print(
    f"Val images  : {len(val_dataset)}"
)

print(
    f"Test images : {len(test_dataset)}"
)

print()


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

train_targets = np.array(
    train_dataset.targets
)

class_counts = np.bincount(
    train_targets,
    minlength=num_classes
)


print("Training class distribution:")

for idx, name in enumerate(class_names):

    print(
        f"  {name}: {class_counts[idx]}"
    )

print()


# ============================================================
# CLASS WEIGHTS
# ============================================================

class_weights = len(train_targets) / (
    num_classes * class_counts
)

class_weights = torch.tensor(
    class_weights,
    dtype=torch.float32,
    device=device
)


print("Class weights:")

for idx, name in enumerate(class_names):

    print(
        f"  {name}: "
        f"{class_weights[idx].item():.4f}"
    )

print()


# ============================================================
# MODEL
# ============================================================

print(
    "Loading pretrained EfficientNet-B0..."
)

weights = models.EfficientNet_B0_Weights.DEFAULT

model = models.efficientnet_b0(
    weights=weights
)


in_features = model.classifier[1].in_features

model.classifier[1] = nn.Linear(
    in_features,
    num_classes
)

model = model.to(device)


# ============================================================
# LOSS
# ============================================================

criterion = nn.CrossEntropyLoss(
    weight=class_weights
)


# ============================================================
# TRAIN FUNCTION
# ============================================================

def train_one_epoch(
    model,
    loader,
    optimizer
):

    model.train()

    running_loss = 0.0

    all_preds = []
    all_targets = []

    for images, targets in loader:

        images = images.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(
            outputs,
            targets
        )

        loss.backward()

        optimizer.step()

        running_loss += (
            loss.item() *
            images.size(0)
        )

        preds = torch.argmax(
            outputs,
            dim=1
        )

        all_preds.extend(
            preds.detach()
            .cpu()
            .numpy()
        )

        all_targets.extend(
            targets.detach()
            .cpu()
            .numpy()
        )


    epoch_loss = (
        running_loss /
        len(loader.dataset)
    )

    accuracy = accuracy_score(
        all_targets,
        all_preds
    )

    macro_f1 = f1_score(
        all_targets,
        all_preds,
        average="macro",
        zero_division=0
    )

    return (
        epoch_loss,
        accuracy,
        macro_f1
    )


# ============================================================
# EVALUATION FUNCTION
# ============================================================

@torch.no_grad()
def evaluate(
    model,
    loader
):

    model.eval()

    running_loss = 0.0

    all_preds = []
    all_targets = []

    for images, targets in loader:

        images = images.to(device)
        targets = targets.to(device)

        outputs = model(images)

        loss = criterion(
            outputs,
            targets
        )

        running_loss += (
            loss.item() *
            images.size(0)
        )

        preds = torch.argmax(
            outputs,
            dim=1
        )

        all_preds.extend(
            preds.cpu().numpy()
        )

        all_targets.extend(
            targets.cpu().numpy()
        )


    loss = (
        running_loss /
        len(loader.dataset)
    )

    accuracy = accuracy_score(
        all_targets,
        all_preds
    )

    macro_f1 = f1_score(
        all_targets,
        all_preds,
        average="macro",
        zero_division=0
    )

    weighted_f1 = f1_score(
        all_targets,
        all_preds,
        average="weighted",
        zero_division=0
    )

    return (
        loss,
        accuracy,
        macro_f1,
        weighted_f1,
        all_targets,
        all_preds
    )


# ============================================================
# START TRAINING
# ============================================================

print()
print("=" * 70)
print("STARTING TURMERIC TRAINING")
print("=" * 70)

start_time = time.time()

best_val_f1 = -1.0
best_epoch = 0

epochs_without_improvement = 0

history = []


# ============================================================
# PHASE 1 — CLASSIFIER HEAD
# ============================================================

print()
print("=" * 70)
print("PHASE 1 — CLASSIFIER HEAD TRAINING")
print("=" * 70)


for param in model.features.parameters():

    param.requires_grad = False


optimizer = torch.optim.AdamW(
    model.classifier.parameters(),
    lr=HEAD_LR,
    weight_decay=WEIGHT_DECAY
)


for epoch in range(
    1,
    HEAD_EPOCHS + 1
):

    (
        train_loss,
        train_acc,
        train_f1
    ) = train_one_epoch(
        model,
        train_loader,
        optimizer
    )


    (
        val_loss,
        val_acc,
        val_f1,
        val_weighted_f1,
        _,
        _
    ) = evaluate(
        model,
        val_loader
    )


    print(
        f"Epoch {epoch:02d}/{HEAD_EPOCHS} | "
        f"Train Loss: {train_loss:.4f} | "
        f"Train Acc: {train_acc:.4f} | "
        f"Train F1: {train_f1:.4f} | "
        f"Val Loss: {val_loss:.4f} | "
        f"Val Acc: {val_acc:.4f} | "
        f"Val Macro-F1: {val_f1:.4f}"
    )


    history.append({

        "epoch": epoch,
        "phase": "head",

        "train_loss": train_loss,
        "train_accuracy": train_acc,
        "train_macro_f1": train_f1,

        "val_loss": val_loss,
        "val_accuracy": val_acc,
        "val_macro_f1": val_f1
    })


# ============================================================
# PHASE 2 — FULL FINE-TUNING
# ============================================================

print()
print("=" * 70)
print("PHASE 2 — FULL MODEL FINE-TUNING")
print("=" * 70)


for param in model.parameters():

    param.requires_grad = True


optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=FINE_TUNE_LR,
    weight_decay=WEIGHT_DECAY
)


scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=2
)


# ============================================================
# FINE-TUNING LOOP
# ============================================================

for epoch in range(
    HEAD_EPOCHS + 1,
    MAX_TOTAL_EPOCHS + 1
):

    (
        train_loss,
        train_acc,
        train_f1
    ) = train_one_epoch(
        model,
        train_loader,
        optimizer
    )


    (
        val_loss,
        val_acc,
        val_f1,
        val_weighted_f1,
        _,
        _
    ) = evaluate(
        model,
        val_loader
    )


    scheduler.step(
        val_f1
    )


    current_lr = optimizer.param_groups[0]["lr"]


    print(
        f"Epoch {epoch:02d}/{MAX_TOTAL_EPOCHS} | "
        f"LR: {current_lr:.2e} | "
        f"Train Loss: {train_loss:.4f} | "
        f"Train Acc: {train_acc:.4f} | "
        f"Train F1: {train_f1:.4f} | "
        f"Val Loss: {val_loss:.4f} | "
        f"Val Acc: {val_acc:.4f} | "
        f"Val Macro-F1: {val_f1:.4f}"
    )


    history.append({

        "epoch": epoch,
        "phase": "fine_tune",
        "learning_rate": current_lr,

        "train_loss": train_loss,
        "train_accuracy": train_acc,
        "train_macro_f1": train_f1,

        "val_loss": val_loss,
        "val_accuracy": val_acc,
        "val_macro_f1": val_f1
    })


    # --------------------------------------------------------
    # BEST CHECKPOINT
    # --------------------------------------------------------

    if val_f1 > best_val_f1:

        best_val_f1 = val_f1
        best_epoch = epoch

        epochs_without_improvement = 0


        torch.save(
            {
                "model_state_dict":
                    model.state_dict(),

                "class_names":
                    class_names,

                "class_to_idx":
                    train_dataset.class_to_idx,

                "image_size":
                    IMAGE_SIZE,

                "architecture":
                    "EfficientNet-B0",

                "best_val_macro_f1":
                    best_val_f1,

                "epoch":
                    epoch,

                "seed":
                    SEED
            },
            MODEL_PATH
        )


        print(
            f"  ✓ New best model saved "
            f"(Val Macro-F1: {best_val_f1:.4f})"
        )


    else:

        epochs_without_improvement += 1


    # --------------------------------------------------------
    # EARLY STOPPING
    # --------------------------------------------------------

    if (
        epochs_without_improvement
        >= PATIENCE
    ):

        print()

        print(
            "Early stopping triggered "
            f"after {PATIENCE} epochs "
            "without improvement."
        )

        break


# ============================================================
# TRAINING COMPLETE
# ============================================================

training_time = (
    time.time() -
    start_time
)


print()
print("=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)

print(
    f"Training time: "
    f"{training_time / 60:.2f} minutes"
)

print(
    f"Best epoch: {best_epoch}"
)

print(
    f"Best validation Macro-F1: "
    f"{best_val_f1:.4f}"
)

print(
    f"Model saved: {MODEL_PATH}"
)


# ============================================================
# LOAD BEST MODEL
# ============================================================

print()
print(
    "Loading best checkpoint "
    "for final test evaluation..."
)


checkpoint = torch.load(
    MODEL_PATH,
    map_location=device
)


model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()


# ============================================================
# FINAL TEST EVALUATION
# ============================================================

(
    test_loss,
    test_accuracy,
    test_macro_f1,
    test_weighted_f1,
    test_targets,
    test_preds
) = evaluate(
    model,
    test_loader
)


print()
print("=" * 70)
print("FINAL TEST RESULTS")
print("=" * 70)

print(
    f"Test Loss       : "
    f"{test_loss:.4f}"
)

print(
    f"Test Accuracy   : "
    f"{test_accuracy * 100:.2f}%"
)

print(
    f"Test Macro-F1   : "
    f"{test_macro_f1:.4f}"
)

print(
    f"Test Weighted-F1: "
    f"{test_weighted_f1:.4f}"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

report = classification_report(
    test_targets,
    test_preds,
    target_names=class_names,
    digits=4,
    zero_division=0
)


print()
print("=" * 70)
print("PER-CLASS RESULTS")
print("=" * 70)

print(report)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    test_targets,
    test_preds
)


print("=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print(cm)


# ============================================================
# SAVE CONFUSION MATRIX
# ============================================================

try:

    import matplotlib.pyplot as plt

    plt.figure(
        figsize=(8, 7)
    )

    plt.imshow(cm)

    plt.title(
        "KrushiSetu AI — Turmeric Confusion Matrix"
    )

    plt.colorbar()

    tick_marks = np.arange(
        len(class_names)
    )

    plt.xticks(
        tick_marks,
        class_names,
        rotation=45,
        ha="right"
    )

    plt.yticks(
        tick_marks,
        class_names
    )

    plt.xlabel(
        "Predicted Label"
    )

    plt.ylabel(
        "True Label"
    )


    for i in range(
        len(class_names)
    ):

        for j in range(
            len(class_names)
        ):

            plt.text(
                j,
                i,
                cm[i, j],
                ha="center",
                va="center"
            )


    plt.tight_layout()

    plt.savefig(
        CONFUSION_PATH,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print()
    print(
        f"Confusion matrix saved: "
        f"{CONFUSION_PATH}"
    )

except Exception as e:

    print(
        f"Could not save confusion matrix: {e}"
    )


# ============================================================
# SAVE METRICS JSON
# ============================================================

classification_report_dict = classification_report(
    test_targets,
    test_preds,
    target_names=class_names,
    output_dict=True,
    zero_division=0
)


results = {

    "model":
        "EfficientNet-B0",

    "pretrained":
        True,

    "dataset":
        "turmeric_4class_original_only",

    "seed":
        SEED,

    "image_size":
        IMAGE_SIZE,

    "batch_size":
        BATCH_SIZE,

    "train_images":
        len(train_dataset),

    "validation_images":
        len(val_dataset),

    "test_images":
        len(test_dataset),

    "excluded_augmented_images":
        3496,

    "classes":
        class_names,

    "class_to_idx":
        train_dataset.class_to_idx,

    "best_epoch":
        best_epoch,

    "best_validation_macro_f1":
        best_val_f1,

    "test_loss":
        test_loss,

    "test_accuracy":
        test_accuracy,

    "test_macro_f1":
        test_macro_f1,

    "test_weighted_f1":
        test_weighted_f1,

    "classification_report":
        classification_report_dict,

    "confusion_matrix":
        cm.tolist(),

    "training_time_minutes":
        training_time / 60,

    "methodology": {

        "optimizer":
            "AdamW",

        "weight_decay":
            WEIGHT_DECAY,

        "head_learning_rate":
            HEAD_LR,

        "fine_tune_learning_rate":
            FINE_TUNE_LR,

        "loss":
            "Weighted CrossEntropyLoss",

        "phase_1_epochs":
            HEAD_EPOCHS,

        "maximum_total_epochs":
            MAX_TOTAL_EPOCHS,

        "early_stopping_patience":
            PATIENCE,

        "scheduler":
            "ReduceLROnPlateau"
    },

    "history":
        history
}


with open(
    METRICS_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=2
    )


# ============================================================
# FINAL MESSAGE
# ============================================================

print()
print("=" * 70)
print("TURMERIC TRAINING PIPELINE FINISHED")
print("=" * 70)

print(
    f"Model   : {MODEL_PATH}"
)

print(
    f"Metrics : {METRICS_PATH}"
)

print(
    f"Matrix  : {CONFUSION_PATH}"
)

print("=" * 70)