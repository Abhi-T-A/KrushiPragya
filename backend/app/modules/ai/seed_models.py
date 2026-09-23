from app.database.connection import SessionLocal
from app.modules.ai.models import MLModel, ModelMetric


MODELS = [
    {
        "crop": "arecanut",
        "model_name": "Arecanut Disease Classifier",
        "architecture": "EfficientNet-B0",
        "version": "arecanut-v1",
        "model_path": "ml/models/krushisetu_efficientnet_b0_best.pth",
        "status": "validated",
       "class_mapping": {
    "0": "Healthy",
    "1": "Mahali_Koleroga",
    "2": "Stem_bleeding",
    "3": "bud borer",
    "4": "stem cracking",
    "5": "yellow leaf disease",
},        "description": "Six-class Arecanut disease classifier trained on the cleaned Arecanut dataset.",
        "test_accuracy": 0.9331,
        "macro_f1": 0.8758,
        "weighted_f1": 0.9353,
        "test_samples": 2003,
        "evaluation_notes": "Held-out cleaned test set. Cross-split duplicate leakage removed before evaluation.",
    },
    {
        "crop": "paddy",
        "model_name": "Paddy Disease Classifier",
        "architecture": "EfficientNet-B0",
        "version": "paddy-v1",
        "model_path": "ml/models/krushisetu_paddy_efficientnet_b0_best.pth",
        "status": "validated",
        "class_mapping": {
            "0": "bacterial_leaf_blight",
            "1": "blast",
            "2": "BPH",
            "3": "Sheath Blight",
        },
        "description": "Four-class Paddy disease and pest classifier.",
        "test_accuracy": 0.9954,
        "macro_f1": 0.9901,
        "weighted_f1": 0.9954,
        "test_samples": 651,
        "evaluation_notes": "Held-out final test set after duplicate cleanup and cross-split leakage removal.",
    },
    {
        "crop": "black_pepper",
        "model_name": "Black Pepper Disease Classifier",
        "architecture": "EfficientNet-B0",
        "version": "black-pepper-v1",
        "model_path": "ml/models/krushisetu_black_pepper_efficientnet_b0_best.pth",
        "status": "validated",
        "class_mapping": {
            "0": "Footrot",
            "1": "Pollu_Disease",
            "2": "Slow-Decline",
        },
        "description": "Three-class Black Pepper disease classifier.",
        "test_accuracy": 1.0,
        "macro_f1": 1.0,
        "weighted_f1": 1.0,
        "test_samples": 221,
        "evaluation_notes": "100% result on a 221-image held-out source-dataset test set; not a guarantee of field performance.",
    },
    {
        "crop": "cardamom",
        "model_name": "Cardamom Disease Classifier",
        "architecture": "EfficientNet-B0",
        "version": "cardamom-v1",
        "model_path": "ml/models/krushisetu_cardamom_efficientnet_b0_best.pth",
        "status": "validated",
        "class_mapping": {
            "0": "Blight",
            "1": "Healthy_1000",
            "2": "Phylosticta_LS_1000",
        },
        "description": "Three-class Cardamom disease classifier.",
        "test_accuracy": 1.0,
        "macro_f1": 1.0,
        "weighted_f1": 1.0,
        "test_samples": 260,
        "evaluation_notes": "100% result on a 260-image held-out source-dataset test set; not a guarantee of field performance.",
    },
    {
        "crop": "coconut",
        "model_name": "Coconut Disease Classifier",
        "architecture": "EfficientNet-B0",
        "version": "coconut-v1",
        "model_path": "ml/models/krushisetu_coconut_efficientnet_b0_best.pth",
        "status": "validated",
        "class_mapping": {
            "0": "Bud Root Dropping",
            "1": "Bud Rot",
            "2": "Gray Leaf Spot",
            "3": "Leaf Rot",
            "4": "Stem Bleeding",
        },
        "description": "Five-class Coconut disease classifier.",
        "test_accuracy": 1.0,
        "macro_f1": 1.0,
        "weighted_f1": 1.0,
        "test_samples": 864,
        "evaluation_notes": "100% result on the held-out test set from the coconut_5class dataset; field performance still requires external validation.",
    },
    {
        "crop": "turmeric",
        "model_name": "Turmeric Disease Classifier",
        "architecture": "EfficientNet-B0",
        "version": "turmeric-v1",
        "model_path": "ml/models/krushisetu_turmeric_efficientnet_b0_best.pth",
        "status": "validated",
        "class_mapping": {
            "0": "Aphids_Disease",
            "1": "Blotch",
            "2": "Healthy_Leaf",
            "3": "Leaf_Spot",
        },
        "description": "Four-class Turmeric leaf disease classifier using original images only for formal evaluation.",
        "test_accuracy": 0.9925373134328358,
        "macro_f1": 0.9928439991821714,
        "weighted_f1": 0.9925418908320797,
        "test_samples": 134,
        "evaluation_notes": "Formal split used 865 original images; 3,496 augmented images were excluded from the formal split.",
    },
    {
        "crop": "ginger",
        "model_name": "Ginger Disease Classifier",
        "architecture": "EfficientNet-B0",
        "version": "ginger-v1",
        "model_path": "ml/models/krushisetu_ginger_efficientnet_b0_best.pth",
        "status": "validated",
        "class_mapping": {
            "0": "Damage-Pest",
            "1": "Dehydrated",
            "2": "Healthy",
            "3": "Leaf-blight",
        },
        "description": "Four-class Ginger disease and condition classifier.",
        "test_accuracy": 0.9872029250457038,
        "macro_f1": 0.9891916147183895,
        "weighted_f1": 0.9871923207127409,
        "test_samples": 1641,
        "evaluation_notes": "Held-out final test set from ginger_4class.",
    },
]


def seed_models():
    db = SessionLocal()

    try:
        inserted = 0
        skipped = 0

        for data in MODELS:
            existing = (
                db.query(MLModel)
                .filter(
                    MLModel.crop == data["crop"],
                    MLModel.version == data["version"],
                )
                .first()
            )

            if existing:
                print(
                    f"SKIPPED: {data['crop']} "
                    f"({data['version']}) already exists"
                )
                skipped += 1
                continue

            model = MLModel(
                crop=data["crop"],
                model_name=data["model_name"],
                architecture=data["architecture"],
                version=data["version"],
                model_path=data["model_path"],
                status=data["status"],
                class_mapping=data["class_mapping"],
                description=data["description"],
                is_active=True,
            )

            db.add(model)
            db.flush()

            metric = ModelMetric(
                model_id=model.id,
                test_accuracy=data["test_accuracy"],
                macro_f1=data["macro_f1"],
                weighted_f1=data["weighted_f1"],
                test_samples=data["test_samples"],
                evaluation_notes=data["evaluation_notes"],
            )

            db.add(metric)

            inserted += 1
            print(f"INSERTED: {data['crop']} → model_id={model.id}")

        db.commit()

        print()
        print(f"Inserted: {inserted}")
        print(f"Skipped:  {skipped}")
        print("Model registry seeding complete.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_models()