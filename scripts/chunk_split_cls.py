import shutil
import random
from math import ceil
from pathlib import Path

TRAIN_RATIO = 0.7
VAL_RATIO = 0.2
TEST_RATIO = 0.1

ROOT_DIR = Path("C:\\Users\\sawna\\Desktop\\CLS_TRAIN")
OUTPUT_DIR = Path("C:\\Users\\sawna\\Desktop\\tput")

VAL_RATIO += 0.01
TEST_RATIO -= 0.01



# random ["train", "test", "val", "val", "train", "test", "test", ....]
def create_chunk_list(total, chunk_size):
    n_chunk = ceil(total / chunk_size)

    train_len = int(n_chunk * TRAIN_RATIO)
    val_len = int(n_chunk * VAL_RATIO)
    if (train_len + val_len) < int(n_chunk * (TRAIN_RATIO + VAL_RATIO)):
        train_len += 1
    test_len = n_chunk - (train_len + val_len)

    lst = []
    lst += ["train"] * train_len
    lst += ["val"] * val_len
    lst += ["test"] * test_len

    random.shuffle(lst)

    return lst

# All Classes
for cls_dir in ROOT_DIR.iterdir():
    print(cls_dir)

    # img_count = sum(1 for x in cls_img_dir.glob('*.jpg') if x.is_file())
    img_lst = sorted(
                (f for f in cls_dir.iterdir() if f.is_file()),
                key=lambda p: p.stat().st_birthtime
            )
    
    for file in img_lst:
        print(file.name)

    img_count = len(img_lst)
    print(img_count)


    lst = create_chunk_list(img_count, 5)
    print(lst)

    for i in range(len(lst)):
        j = i * 5
        for idx in range(j, min(img_count, j+5)):
            # Train
            if lst[i] == "train":
                # Set Output Directory
                train_img_output_dir = OUTPUT_DIR / "train" / cls_dir.stem
                train_img_output_dir.mkdir(parents=True, exist_ok=True)

                # Copy Files
                shutil.copy2(img_lst[idx], train_img_output_dir)
            # Valid
            if lst[i] == "val":
                # Set Output Directory
                val_img_output_dir = OUTPUT_DIR / "valid" / cls_dir.stem
                val_img_output_dir.mkdir(parents=True, exist_ok=True)

                # Copy Files
                shutil.copy2(img_lst[idx], val_img_output_dir)
            # Test
            if lst[i] == "test":
                # Set Output Directory
                test_img_output_dir = OUTPUT_DIR / "test" / cls_dir.stem
                test_img_output_dir.mkdir(parents=True, exist_ok=True)

                # Copy Files
                shutil.copy2(img_lst[idx], test_img_output_dir)


