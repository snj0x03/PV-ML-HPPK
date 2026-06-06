import shutil
import random
from math import ceil
from pathlib import Path

TRAIN_RATIO = 0.7
VAL_RATIO = 0.2
TEST_RATIO = 0.1

ROOT_DIR = Path("C:\\Users\\sawna\\Desktop\\Annotated_Dataset.yolov8\\train")
TEMP_DIR = Path("C:\\Users\\sawna\\Desktop\\temp")
OUTPUT_DIR = Path("C:\\Users\\sawna\\Desktop\\chunk_output")

VAL_RATIO += 0.01
TEST_RATIO -= 0.01

classes = []
with open("classes.txt", "r") as f:
    for line in f.readlines():
        classes.append(line.rstrip('\n'))
         

print(classes)


images_dir = ROOT_DIR / "images"
labels_dir = ROOT_DIR / "labels"


# Copy images in root directory into corresponding classes by file prefix
for img_path in sorted(images_dir.iterdir()):
    lbl_path = labels_dir / (img_path.stem + ".txt")
    for cls in classes:
        # print(img_path.stem)
        if img_path.stem.startswith(cls):
            img_dest = TEMP_DIR / cls / "images" 
            lbl_dest = TEMP_DIR / cls / "labels"
            img_dest.mkdir(parents=True, exist_ok=True)
            lbl_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img_path, img_dest)
            shutil.copy2(lbl_path, lbl_dest)

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
for cls_dir in TEMP_DIR.iterdir():
    print(cls_dir)
    cls_img_dir = cls_dir / "images"
    cls_lbl_dir = cls_dir / "labels"

    # img_count = sum(1 for x in cls_img_dir.glob('*.jpg') if x.is_file())
    img_lst = sorted(cls_img_dir.iterdir())
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
                train_img_output_dir = OUTPUT_DIR / "train" / "images"
                train_lbl_output_dir = OUTPUT_DIR / "train" / "labels"
                train_img_output_dir.mkdir(parents=True, exist_ok=True)
                train_lbl_output_dir.mkdir(parents=True, exist_ok=True)

                # Copy Files
                shutil.copy2(img_lst[idx], train_img_output_dir)
                shutil.copy2(cls_lbl_dir / (img_lst[idx].stem + ".txt"), train_lbl_output_dir) 
            # Valid
            if lst[i] == "val":
                # Set Output Directory
                val_img_output_dir = OUTPUT_DIR / "valid" / "images"
                val_lbl_output_dir = OUTPUT_DIR / "valid" / "labels"
                val_img_output_dir.mkdir(parents=True, exist_ok=True)
                val_lbl_output_dir.mkdir(parents=True, exist_ok=True)

                # Copy Files
                shutil.copy2(img_lst[idx], val_img_output_dir)
                shutil.copy2(cls_lbl_dir / (img_lst[idx].stem + ".txt"), val_lbl_output_dir) 
            # Test
            if lst[i] == "test":
                # Set Output Directory
                test_img_output_dir = OUTPUT_DIR / "test" / "images"
                test_lbl_output_dir = OUTPUT_DIR / "test" / "labels"
                test_img_output_dir.mkdir(parents=True, exist_ok=True)
                test_lbl_output_dir.mkdir(parents=True, exist_ok=True)

                # Copy Files
                shutil.copy2(img_lst[idx], test_img_output_dir)
                shutil.copy2(cls_lbl_dir / (img_lst[idx].stem + ".txt"), test_lbl_output_dir) 


