from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models
from sklearn.metrics import classification_report, confusion_matrix

from dataset import create_dataloaders


# ============================================================
# KrushiSetu AI - EfficientNet-B0 Training
# ============================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

NUM_CLASSES = 6
EPOCHS = 8
LEARNING_RATE = 0.0003

MODEL_DIR = Path("ml/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

BEST_MODEL_PATH = MODEL_DIR / "krushisetu_efficientnet_b0_best.pth"


# ============================================================
# Main
# ============================================================

def main():

    print()
    print("=" * 60)
    print("KrushiSetu AI - Model Training")
    print("=" * 60)

    print()
    print(f"Device: {DEVICE}")

    # --------------------------------------------------------
    # Dataset
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    print()
    print("Loading pretrained EfficientNet-B0...")

    weights = models.EfficientNet_B0_Weights.DEFAULT

    model = models.efficientnet_b0(weights=weights)

    # Replace final classifier
    in_features = model.classifier[1].in_features

    model.classifier[1] = nn.Linear(
        in_features,
        NUM_CLASSES
    )

    model = model.to(DEVICE)

    # --------------------------------------------------------
    # Freeze backbone initially
    # --------------------------------------------------------

    for param in model.features.parameters():
        param.requires_grad = False

    print("Backbone frozen.")
    print("Training classification head first.")

    # --------------------------------------------------------
    # Class weights
    # --------------------------------------------------------

    # Approximate weights from the original training
    # distribution. Minority classes receive higher weight.

    class_counts = torch.tensor(
        [3781, 2426, 146, 139, 522, 1420],
        dtype=torch.float
    )

    class_weights = class_counts.sum() / (
        NUM_CLASSES * class_counts
    )

    class_weights = class_weights.to(DEVICE)

    print()
    print("Class weights:")

    for name, weight in zip(classes, class_weights):
        print(f"{name:25} : {weight.item():.4f}")

    # --------------------------------------------------------
    # Loss
    # --------------------------------------------------------

    criterion = nn.CrossEntropyLoss(
        weight=class_weights
    )

    # Only classifier parameters initially
    optimizer = torch.optim.AdamW(
        model.classifier.parameters(),
        lr=LEARNING_RATE,
        weight_decay=1e-4
    )

    # --------------------------------------------------------
    # Training
    # --------------------------------------------------------

    best_validation_accuracy = 0.0

    for epoch in range(EPOCHS):

        model.train()

        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for batch_index, (images, labels) in enumerate(train_loader):

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            loss.backward()
            optimizer.step()

            train_loss += loss.item()

            predictions = outputs.argmax(
                dim=1
            )

            train_correct += (
                predictions == labels
            ).sum().item()

            train_total += labels.size(0)

            if (batch_index + 1) % 25 == 0:
                print(
                    f"Epoch [{epoch + 1}/{EPOCHS}] "
                    f"Batch [{batch_index + 1}/{len(train_loader)}]"
                )

        train_accuracy = (
            train_correct / train_total
        ) * 100

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        model.eval()

        validation_correct = 0
        validation_total = 0
        validation_loss = 0.0

        with torch.no_grad():

            for images, labels in validation_loader:

                images = images.to(DEVICE)
                labels = labels.to(DEVICE)

                outputs = model(images)

                loss = criterion(
                    outputs,
                    labels
                )

                validation_loss += loss.item()

                predictions = outputs.argmax(
                    dim=1
                )

                validation_correct += (
                    predictions == labels
                ).sum().item()

                validation_total += labels.size(0)

        validation_accuracy = (
            validation_correct / validation_total
        ) * 100

        print()
        print("-" * 60)

        print(
            f"Epoch {epoch + 1}/{EPOCHS}"
        )

        print(
            f"Train Loss       : "
            f"{train_loss / len(train_loader):.4f}"
        )

        print(
            f"Train Accuracy   : "
            f"{train_accuracy:.2f}%"
        )

        print(
            f"Validation Loss  : "
            f"{validation_loss / len(validation_loader):.4f}"
        )

        print(
            f"Validation Acc   : "
            f"{validation_accuracy:.2f}%"
        )

        # ----------------------------------------------------
        # Save best model
        # ----------------------------------------------------

        if validation_accuracy > best_validation_accuracy:

            best_validation_accuracy = validation_accuracy

            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "classes": classes,
                    "validation_accuracy":
                        validation_accuracy,
                },
                BEST_MODEL_PATH
            )

            print()
            print("✓ Best model saved.")

        print("-" * 60)

    # ========================================================
    # Final Test Evaluation
    # ========================================================

    print()
    print("=" * 60)
    print("FINAL TEST EVALUATION")
    print("=" * 60)

    # Load best model
    checkpoint = torch.load(
        BEST_MODEL_PATH,
        map_location=DEVICE
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.eval()

    all_predictions = []
    all_labels = []

    with torch.no_grad():

        for images, labels in test_loader:

            images = images.to(DEVICE)

            outputs = model(images)

            predictions = outputs.argmax(
                dim=1
            )

            all_predictions.extend(
                predictions.cpu().tolist()
            )

            all_labels.extend(
                labels.tolist()
            )

    # --------------------------------------------------------
    # Accuracy
    # --------------------------------------------------------

    correct = sum(
        prediction == label
        for prediction, label
        in zip(all_predictions, all_labels)
    )

    test_accuracy = (
        correct / len(all_labels)
    ) * 100

    print()
    print(
        f"Test Accuracy : {test_accuracy:.2f}%"
    )

    # --------------------------------------------------------
    # Classification report
    # --------------------------------------------------------

    print()
    print("Classification Report")
    print("=" * 60)

    print(
        classification_report(
            all_labels,
            all_predictions,
            target_names=classes,
            digits=4,
            zero_division=0
        )
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    print("Confusion Matrix")
    print("=" * 60)

    matrix = confusion_matrix(
        all_labels,
        all_predictions
    )

    print(matrix)

    print()
    print("=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    print()
    print(
        f"Best model: {BEST_MODEL_PATH}"
    )

    print(
        f"Best validation accuracy: "
        f"{best_validation_accuracy:.2f}%"
    )

    print(
        f"Test accuracy: "
        f"{test_accuracy:.2f}%"
    )


if __name__ == "__main__":
    main()