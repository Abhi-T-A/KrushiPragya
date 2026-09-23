from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image
from sqlalchemy import select

from app.database.connection import SessionLocal
from app.modules.ai.models.dataset import Dataset, DatasetImage


DATASETS = [
    {
        "name": "Arecanut 6-Class Final Dataset",
        "crop": "arecanut",
        "root": Path(r"C:\Users\Teja\scout\ml\data\arecanut_6class"),
        "source": "Cleaned project dataset",
        "license": None,
        "version": "v1",
        "description": (
            "Final 6-class Arecanut dataset used for EfficientNet-B0 evaluation. "
            "Duplicate and cross-split leakage cleanup applied."
        ),
    },
    {
        "name": "Paddy 4-Class Final Dataset",
        "crop": "paddy",
        "root": Path(r"C:\Users\Teja\scout\ml\data\paddy_4class"),
        "source": "Paddy Doctor + supplementary datasets",
        "license": None,
        "version": "v1",
        "description": (
            "Final 4-class Paddy dataset used for EfficientNet-B0 evaluation "
            "after duplicate and cross-split leakage cleanup."
        ),
    },
    {
        "name": "Coconut 5-Class Final Dataset",
        "crop": "coconut",
        "root": Path(r"C:\Users\Teja\scout\ml\data\coconut_5class"),
        "source": "Mendeley Coconut Tree Disease Dataset",
        "license": "CC BY 4.0",
        "version": "v1",
        "description": (
            "Final 5-class Coconut dataset used for EfficientNet-B0 evaluation."
        ),
    },
    {
        "name": "Black Pepper 3-Class Final Dataset",
        "crop": "black_pepper",
        "root": Path(r"C:\Users\Teja\scout\ml\data\black_pepper_3class"),
        "source": "Black Pepper Leaf Disease Mini-Dataset",
        "license": "CC0",
        "version": "v1",
        "description": (
            "Final 3-class Black Pepper dataset after duplicate cleanup "
            "and cross-split leakage verification."
        ),
    },
    {
        "name": "Cardamom 3-Class Final Dataset",
        "crop": "cardamom",
        "root": Path(r"C:\Users\Teja\scout\ml\data\cardamom_3class"),
        "source": "Cardamom Plant Dataset",
        "license": None,
        "version": "v1",
        "description": (
            "Final 3-class Cardamom dataset used for EfficientNet-B0 evaluation."
        ),
    },
    {
        "name": "Ginger 4-Class Final Dataset",
        "crop": "ginger",
        "root": Path(r"C:\Users\Teja\scout\ml\data\ginger_4class"),
        "source": "Ginger Leaf Dataset",
        "license": None,
        "version": "v1",
        "description": (
            "Final 4-class Ginger dataset used for EfficientNet-B0 evaluation."
        ),
    },
    {
        "name": "Turmeric 4-Class Final Dataset",
        "crop": "turmeric",
        "root": Path(r"C:\Users\Teja\scout\ml\data\turmeric_4class"),
        "source": "Image Dataset for Turmeric Plant Leaf Disease Detection",
        "license": "CC BY 4.0",
        "version": "v1",
        "description": (
            "Final 4-class Turmeric dataset. Formal split uses original images; "
            "augmented images were excluded from the formal evaluation split."
        ),
    },
]


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def image_metadata(path: Path):
    try:
        with Image.open(path) as image:
            width, height = image.size
        return width, height
    except Exception as exc:
        print(f"  WARNING: could not read image dimensions: {path}")
        print(f"           {exc}")
        return None, None


def import_dataset(db, config):
    root = config["root"]

    if not root.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {root}")

    existing = db.execute(
        select(Dataset).where(
            Dataset.crop == config["crop"],
            Dataset.version == config["version"],
        )
    ).scalar_one_or_none()

    if existing:
        print(
            f"\nSKIP: {config['crop']} already exists "
            f"(dataset_id={existing.id}, version={existing.version})"
        )
        return existing.id, 0

    dataset = Dataset(
        name=config["name"],
        crop=config["crop"],
        source=config["source"],
        license=config["license"],
        version=config["version"],
        description=config["description"],
        total_images=0,
    )

    db.add(dataset)
    db.flush()

    imported = 0

    for split_dir in sorted(root.iterdir()):
        if not split_dir.is_dir():
            continue

        split = split_dir.name.lower()

        if split not in {"train", "val", "test"}:
            continue

        for class_dir in sorted(split_dir.iterdir()):
            if not class_dir.is_dir():
                continue

            class_name = class_dir.name

            for image_path in sorted(class_dir.rglob("*")):
                if not image_path.is_file():
                    continue

                if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue

                file_hash = sha256_file(image_path)

                duplicate = db.execute(
                    select(DatasetImage.id).where(
                        DatasetImage.dataset_id == dataset.id,
                        DatasetImage.sha256 == file_hash,
                    )
                ).scalar_one_or_none()

                if duplicate is not None:
                    print(f"  SKIP duplicate: {image_path.name}")
                    continue

                width, height = image_metadata(image_path)

                image_record = DatasetImage(
                    dataset_id=dataset.id,
                    crop=config["crop"],
                    class_name=class_name,
                    split=split,
                    file_name=image_path.name,
                    storage_path=str(image_path),
                    sha256=file_hash,
                    width=width,
                    height=height,
                    file_size=image_path.stat().st_size,
                    source_url=None,
                )

                db.add(image_record)
                imported += 1

                if imported % 500 == 0:
                    db.flush()
                    print(f"  Imported {imported} images...")

    dataset.total_images = imported

    db.commit()

    print(
        f"  DONE: {config['crop']} "
        f"dataset_id={dataset.id}, images={imported}"
    )

    return dataset.id, imported


def main():
    db = SessionLocal()

    total_imported = 0

    try:
        print("==============================================")
        print(" KrushiPragya Dataset Import")
        print("==============================================")

        for config in DATASETS:
            print(f"\nIMPORTING: {config['crop']}")
            print(f"ROOT: {config['root']}")

            _, imported = import_dataset(db, config)
            total_imported += imported

        print("\n==============================================")
        print(f"TOTAL NEW IMAGES IMPORTED: {total_imported}")
        print("==============================================")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()