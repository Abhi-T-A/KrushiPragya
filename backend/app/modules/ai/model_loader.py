from pathlib import Path

import torch
from torchvision.models import efficientnet_b0
from sqlalchemy.orm import Session

from app.modules.ai.models import MLModel


PROJECT_ROOT = Path(__file__).resolve().parents[4]


class ModelLoader:
    def __init__(self):
        self.models = {}

    def load_models(self, db: Session):
        records = (
            db.query(MLModel)
            .filter(
                MLModel.is_active.is_(True),
                MLModel.status == "validated",
            )
            .order_by(MLModel.id)
            .all()
        )

        for record in records:
            model_path = PROJECT_ROOT / record.model_path

            if not model_path.exists():
                print(
                    f"WARNING: Model file not found for "
                    f"{record.crop}: {model_path}"
                )
                continue

            # Create the same EfficientNet-B0 architecture
            # used during training.
            model = efficientnet_b0(weights=None)

            num_classes = len(record.class_mapping)

            model.classifier[1] = torch.nn.Linear(
                model.classifier[1].in_features,
                num_classes,
            )

            # Load checkpoint
            checkpoint = torch.load(
                model_path,
                map_location="cpu",
                weights_only=True,
            )

            # Verify checkpoint class mapping against database mapping.
            checkpoint_classes = checkpoint.get("classes")

            if checkpoint_classes:
                db_classes = [
                    record.class_mapping[str(i)]
                    for i in range(len(record.class_mapping))
                ]

                if checkpoint_classes != db_classes:
                    raise ValueError(
                        f"Class mapping mismatch for {record.crop}: "
                        f"checkpoint={checkpoint_classes}, "
                        f"database={db_classes}"
                    )

            # Load trained weights.
            model.load_state_dict(
                checkpoint["model_state_dict"]
            )

            # Inference mode.
            model.eval()

            self.models[record.crop] = {
                "model": model,
                "version": record.version,
                "class_mapping": record.class_mapping,
                "model_path": str(model_path),
            }

            print(
                f"LOADED: {record.crop} "
                f"({record.version})"
            )

        print(
            f"Total models loaded: {len(self.models)}"
        )


model_loader = ModelLoader()