from pathlib import Path
from collections import defaultdict
import hashlib


# ============================================================
# PATHS
# ============================================================

DATASET = Path(
    r"C:\Users\Teja\scout\ml\data\paddy_4class"
)

SPLIT_PRIORITY = {
    "train": 0,
    "val": 1,
    "test": 2,
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


# ============================================================
# HELPERS
# ============================================================

def get_images(folder):

    if not folder.exists():
        return []

    return [
        p
        for p in folder.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    ]


def sha256_file(path):

    h = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("PADDY 4-CLASS EXACT DUPLICATE CLEANUP")
    print("=" * 70)

    hashes = defaultdict(list)

    # --------------------------------------------------------
    # Collect all images
    # --------------------------------------------------------

    for split in [
        "train",
        "val",
        "test",
    ]:

        split_dir = DATASET / split

        for image in get_images(split_dir):

            file_hash = sha256_file(image)

            hashes[file_hash].append(
                (
                    split,
                    image
                )
            )

    duplicate_groups = {
        h: files
        for h, files in hashes.items()
        if len(files) > 1
    }

    print()
    print(
        f"Duplicate groups found: "
        f"{len(duplicate_groups)}"
    )

    files_to_delete = []

    # --------------------------------------------------------
    # Decide which copy to keep
    # --------------------------------------------------------

    for file_hash, files in duplicate_groups.items():

        # Sort by:
        # train first
        # val second
        # test last
        #
        # Then alphabetically for deterministic behavior.

        files_sorted = sorted(
            files,
            key=lambda x: (
                SPLIT_PRIORITY[x[0]],
                str(x[1]).lower()
            )
        )

        keep_split, keep_file = files_sorted[0]

        for split, image in files_sorted[1:]:

            files_to_delete.append(
                (
                    file_hash,
                    keep_split,
                    keep_file,
                    split,
                    image
                )
            )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print()
    print(
        f"Duplicate files to remove: "
        f"{len(files_to_delete)}"
    )

    print()
    print("=" * 70)
    print("FILES THAT WILL BE REMOVED")
    print("=" * 70)

    for (
        file_hash,
        keep_split,
        keep_file,
        remove_split,
        remove_file
    ) in files_to_delete:

        print()
        print(
            f"KEEP   [{keep_split}]"
        )

        print(
            f"       {keep_file}"
        )

        print(
            f"REMOVE [{remove_split}]"
        )

        print(
            f"       {remove_file}"
        )

    # --------------------------------------------------------
    # Delete duplicates
    # --------------------------------------------------------

    for (
        file_hash,
        keep_split,
        keep_file,
        remove_split,
        remove_file
    ) in files_to_delete:

        remove_file.unlink()

    # --------------------------------------------------------
    # Final count
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CLEANUP COMPLETE")
    print("=" * 70)

    print(
        f"Removed files: "
        f"{len(files_to_delete)}"
    )

    print()
    print(
        "Original source datasets were NOT modified."
    )