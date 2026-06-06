import os
import random
import shutil
import yaml

# ================================================================
# CONFIG — change ratios here (must sum to 1.0)
# ================================================================
TRAIN_RATIO = 0.75
VAL_RATIO   = 0.20
TEST_RATIO  = 0.05

RANDOM_SEED = 42   # set to any number for reproducible splits

# Base directory — folder where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Combined output folder
OUTPUT_DIR = os.path.join(BASE_DIR, "Local", "Run-Annotated", "Combined_Dataset_split")

# Datasets to collect from (relative to BASE_DIR)
DATASETS = [
    os.path.join(BASE_DIR)
]
# ================================================================


def validate_ratios(train, val, test):
    total = round(train + val + test, 10)
    if total != 1.0:
        raise ValueError(f"Ratios must sum to 1.0, got {total}")


def collect_pairs(src_dir: str) -> list[tuple[str, str]]:
    src_images = os.path.join(src_dir, "train", "images")
    src_labels = os.path.join(src_dir, "train", "labels")

    pairs   = []
    skipped = 0

    for img_file in sorted(os.listdir(src_images)):
        if not img_file.endswith(".jpg"):
            continue
        lbl_file = img_file.replace(".jpg", ".txt")
        lbl_path = os.path.join(src_labels, lbl_file)
        if os.path.exists(lbl_path):
            pairs.append((
                os.path.join(src_images, img_file),
                os.path.join(src_labels, lbl_file),
            ))
        else:
            skipped += 1

    print(f"  [{os.path.basename(src_dir)}] {len(pairs)} pairs collected"
          + (f", {skipped} skipped (no label)" if skipped else ""))
    return pairs


def run_split(datasets: list, output_dir: str, train_ratio: float,
              val_ratio: float, test_ratio: float, seed: int):

    print(f"\n{'='*60}")
    print(f"  Output  : {output_dir}")
    print(f"  Ratio   : train={train_ratio} / val={val_ratio} / test={test_ratio}")
    print(f"{'='*60}")

    # Collect all pairs from every dataset
    all_pairs = []
    for src_dir in datasets:
        if not os.path.exists(src_dir):
            print(f"  ⚠️  Not found, skipping: {src_dir}")
            continue
        all_pairs.extend(collect_pairs(src_dir))

    # Shuffle all together
    random.seed(seed)
    random.shuffle(all_pairs)

    total   = len(all_pairs)
    n_train = int(total * train_ratio)
    n_val   = int(total * val_ratio)
    n_test  = total - n_train - n_val

    splits = {
        "train": all_pairs[:n_train],
        "valid": all_pairs[n_train:n_train + n_val],
        "test" : all_pairs[n_train + n_val:],
    }

    print(f"\n  Total   : {total}")
    print(f"  Train   : {n_train}")
    print(f"  Val     : {n_val}")
    print(f"  Test    : {n_test}")

    # Copy files into combined output folder
    for split_name, pairs in splits.items():
        img_out = os.path.join(output_dir, split_name, "images")
        lbl_out = os.path.join(output_dir, split_name, "labels")
        os.makedirs(img_out, exist_ok=True)
        os.makedirs(lbl_out, exist_ok=True)

        for img_path, lbl_path in pairs:
            shutil.copy(img_path, os.path.join(img_out, os.path.basename(img_path)))
            shutil.copy(lbl_path, os.path.join(lbl_out, os.path.basename(lbl_path)))

    # Write data.yaml from the first dataset as the base
    src_yaml = os.path.join(datasets[0], "data.yaml")
    if os.path.exists(src_yaml):
        with open(src_yaml, "r") as f:
            yaml_data = yaml.safe_load(f)

        yaml_data["train"] = "../train/images"
        yaml_data["val"]   = "../valid/images"
        yaml_data["test"]  = "../test/images"

        out_yaml = os.path.join(output_dir, "data.yaml")
        with open(out_yaml, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

        print(f"\n  data.yaml written to: {out_yaml}")

    print(f"\n  Done. Combined split saved to: {output_dir}\n")


# ================================================================
# RUN
# ================================================================
if __name__ == "__main__":
    validate_ratios(TRAIN_RATIO, VAL_RATIO, TEST_RATIO)
    run_split(DATASETS, OUTPUT_DIR, TRAIN_RATIO, VAL_RATIO, TEST_RATIO, RANDOM_SEED)
