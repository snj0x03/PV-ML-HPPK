"""
Multi-Label Stratified Split for YOLO-format image datasets.

Usage:
    python multi_label_stratified_split.py --dataset ./my_dataset --train 0.7 --val 0.2 --test 0.1
    python multi_label_stratified_split.py --dataset ./my_dataset --names data.yaml

Requirements:
    pip install iterative-stratification numpy pyyaml
"""

import argparse
import shutil
import sys
from pathlib import Path

from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
import numpy as np
import yaml

ROOT_DIR = ""
OUTPUT_DIR = ""
TRAIN_DIR = ""
VALID_DIR = ""
TEST_DIR = ""

CLASS_NAMES = []

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def load_dataset(dataset_root: Path) -> tuple[list[Path], list[Path], int]:
    """Return (image_paths, label_paths, n_classes) from a YOLO dataset root."""
    images_dir = dataset_root / "images"
    labels_dir = dataset_root / "labels"

    if not images_dir.exists():
        sys.exit(f"[ERROR] 'images' folder not found: {images_dir}")
    if not labels_dir.exists():
        sys.exit(f"[ERROR] 'labels' folder not found: {labels_dir}")

    image_paths, label_paths = [], []
    missing_labels = []

    for img_path in sorted(images_dir.iterdir()):
        if img_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        lbl_path = labels_dir / (img_path.stem + ".txt")
        if not lbl_path.exists():
            missing_labels.append(img_path.name)
            continue
        image_paths.append(img_path)
        label_paths.append(lbl_path)

    if missing_labels:
        preview = missing_labels[:5]
        suffix = "..." if len(missing_labels) > 5 else ""
        print(f"[WARNING] {len(missing_labels)} image(s) skipped (no matching label file): {preview}{suffix}")

    if not image_paths:
        sys.exit("[ERROR] No valid image-label pairs found.")

    # Detect number of classes from label files
    all_classes: set[int] = set()
    for lbl_path in label_paths:
        for line in lbl_path.read_text().splitlines():
            line = line.strip()
            if line:
                all_classes.add(int(line.split()[0]))

    n_classes = max(all_classes) + 1 if all_classes else 0
    print(f"[INFO] Found {len(image_paths)} images, {n_classes} classes")
    return image_paths, label_paths, n_classes


def build_label_matrix(label_paths: list[Path], n_classes: int) -> np.ndarray:
    """Build binary (N_images x N_classes) multi-label matrix."""
    matrix = np.zeros((len(label_paths), n_classes), dtype=np.int32)
    for i, lbl_path in enumerate(label_paths):
        for line in lbl_path.read_text().splitlines():
            line = line.strip()
            if line:
                cls_id = int(line.split()[0])
                if cls_id < n_classes:
                    matrix[i, cls_id] = 1
    return matrix


def iterative_split(indices: np.ndarray, labels: np.ndarray, ratio: float, seed: int):
    """Split indices into two parts using MultilabelStratifiedShuffleSplit."""

    splitter = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=ratio, random_state=seed)
    dummy_X = np.zeros((len(indices), 1))
    sub_labels = labels[indices]

    for part_a_idx, part_b_idx in splitter.split(dummy_X, sub_labels):
        return indices[part_a_idx], indices[part_b_idx]


def copy_files(
    indices: np.ndarray,
    image_paths: list[Path],
    label_paths: list[Path],
    dest_root: Path,
    split_name: str,
) -> None:
    img_dest = dest_root / split_name / "images"
    lbl_dest = dest_root / split_name / "labels"
    img_dest.mkdir(parents=True, exist_ok=True)
    lbl_dest.mkdir(parents=True, exist_ok=True)

    for idx in indices:
        shutil.copy2(image_paths[idx], img_dest / image_paths[idx].name)
        shutil.copy2(label_paths[idx], lbl_dest / label_paths[idx].name)


def print_distribution(
    splits: dict[str, np.ndarray],
    label_matrix: np.ndarray,
    class_names: list[str],
) -> None:
    n_classes = label_matrix.shape[1]
    col_width = max(len(n) for n in class_names) + 2 if class_names else 10
    total = {name: len(idx) for name, idx in splits.items()}

    print("\n" + "=" * (col_width + 36))
    print("Class distribution per split (count / percentage)")
    print("=" * (col_width + 36))
    print(f"{'Class':<{col_width}}{'Train':>12}{'Val':>12}{'Test':>12}")
    print("-" * (col_width + 36))

    for c in range(n_classes):
        name = class_names[c] if c < len(class_names) else f"class_{c}"
        row = f"{name:<{col_width}}"
        for split_name, idx in splits.items():
            count = int(label_matrix[idx, c].sum())
            pct = count / total[split_name] * 100 if total[split_name] else 0
            row += f"{count:>6}({pct:4.1f}%)"
        print(row)

    print("-" * (col_width + 36))
    row = f"{'TOTAL':<{col_width}}"
    for split_name, idx in splits.items():
        row += f"{total[split_name]:>12}"
    print(row)
    print("=" * (col_width + 36))


def save_data_yaml(output_root: Path, class_names: list[str], n_classes: int) -> None:
    names = class_names if class_names else [f"class_{i}" for i in range(n_classes)]
    config = {
        "path": str(output_root.resolve()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": len(names),
        "names": names,
    }
    yaml_path = output_root / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    print(f"[INFO] Saved data.yaml: {yaml_path}")


def load_class_names(names_arg: str | None, dataset_root: Path) -> list[str]:
    """Load class names from --names argument (yaml path or comma-separated list)."""
    if names_arg is None:
        # Try to auto-detect data.yaml in the dataset root
        auto_yaml = dataset_root / "data.yaml"
        if auto_yaml.exists():
            with open(auto_yaml, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            names = cfg.get("names", [])
            print(f"[INFO] Loaded {len(names)} class name(s) from data.yaml")
            return names
        return []

    p = Path(names_arg)
    if p.exists() and p.suffix in {".yaml", ".yml"}:
        with open(p, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("names", [])

    # Treat as comma-separated class names
    return [n.strip() for n in names_arg.split(",") if n.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Label Stratified Split for YOLO datasets")
    parser.add_argument("--dataset", required=True, help="Path to YOLO dataset root (must contain images/ and labels/)")
    parser.add_argument("--output", default="./split_output", help="Output directory (default: ./split_output)")
    parser.add_argument("--train", type=float, default=0.7, help="Train split ratio (default: 0.7)")
    parser.add_argument("--val", type=float, default=0.2, help="Val split ratio (default: 0.2)")
    parser.add_argument("--test", type=float, default=0.1, help="Test split ratio (default: 0.1)")
    parser.add_argument("--names", default=None, help="Class names: path to data.yaml or comma-separated string")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    args = parser.parse_args()

    # Validate ratios sum to 1.0
    total = args.train + args.val + args.test
    if abs(total - 1.0) > 1e-6:
        sys.exit(f"[ERROR] train + val + test must sum to 1.0, got {total:.4f}")

    dataset_root = Path(args.dataset)
    output_root = Path(args.output)

    if output_root.exists():
        print(f"[WARNING] Output directory already exists and may be overwritten: {output_root}")

    # Step 1: Load dataset
    image_paths, label_paths, n_classes = load_dataset(dataset_root)
    class_names = load_class_names(args.names, dataset_root)

    # Step 2: Build multi-label binary matrix
    label_matrix = build_label_matrix(label_paths, n_classes)

    all_indices = np.arange(len(image_paths))

    # Step 3: Two-stage stratified split
    #   Stage 1 — separate train from the remaining (val + test) pool
    temp_ratio = args.val + args.test
    train_idx, temp_idx = iterative_split(all_indices, label_matrix, ratio=temp_ratio, seed=args.seed)

    #   Stage 2 — split the remaining pool into val and test
    val_ratio_within_temp = args.val / (args.val + args.test)
    val_idx, test_idx = iterative_split(temp_idx, label_matrix, ratio=1 - val_ratio_within_temp, seed=args.seed)

    splits = {"train": train_idx, "val": val_idx, "test": test_idx}

    # Step 4: Copy files to output folders
    for split_name, idx in splits.items():
        copy_files(idx, image_paths, label_paths, output_root, split_name)
        print(f"[INFO] {split_name}: {len(idx)} images copied")

    # Step 5: Print class distribution report
    names_for_report = class_names if class_names else [f"class_{i}" for i in range(n_classes)]
    print_distribution(splits, label_matrix, names_for_report)

    # Step 6: Save data.yaml for YOLO training
    save_data_yaml(output_root, class_names, n_classes)

    print(f"\n[DONE] Output saved to: {output_root.resolve()}")


if __name__ == "__main__":
    main()
