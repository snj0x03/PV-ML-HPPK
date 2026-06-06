from collections import Counter
from pathlib import Path

def count_instances(label_dir):
    counts = Counter()

    for label_file in Path(label_dir).glob("*.txt"):
        with open(label_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    class_id = int(parts[0])
                    counts[class_id] += 1

    return counts

train_counts = count_instances("./train/labels")
val_counts = count_instances("./valid/labels")
test_counts = count_instances("./test/labels")

train_total = sum(train_counts.values())
val_total = sum(val_counts.values())
test_total = sum(test_counts.values())

all_classes = sorted(set(train_counts) | set(test_counts))

print(f"{'Class':<8}{'Train':>16}{'Val ':>16}{'Test':>16}")
print("-" * 62)

for cls in all_classes:
    train_n = train_counts.get(cls, 0)
    val_n = val_counts.get(cls, 0)
    test_n = test_counts.get(cls, 0)

    train_pct = (train_n / train_total * 100) if train_total else 0
    val_pct = (val_n / val_total * 100) if val_total else 0
    test_pct = (test_n / test_total * 100) if test_total else 0

    

    print(
        f"{cls:<8}"
        f"{train_n:>10}( {train_pct:.2f}%)"
        f"{val_n:>10}( {val_pct:.2f}%)"
        f"{test_n:>10}( {test_pct:.2f}%)"
    )
total = train_total + val_total + test_total
print("-------------------------------------------------------------")
print(
    f"{total:<8}"
    f"{train_total:>10}( {train_total/total * 100:.2f}%)"
    f"{val_total:>10}( {val_total/total * 100:.2f}%)"
    f"{test_total:>10}( {test_total/total * 100:.2f}%)"
)
