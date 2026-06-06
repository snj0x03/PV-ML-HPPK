import os
import matplotlib.pyplot as plt
from collections import Counter

C = []
for i in range(40):
    C.append("C" + str(i))

def plot_yolo_distribution(labels_dir):
    """
    Parses YOLO label text files and plots class distributions.
    
    :param labels_dir: Path to the directory containing .txt annotation files
    :param class_names: List of class names matching the index positions
    """
    class_counts = Counter()
    
    # Iterate through all label files
    for filename in os.listdir(labels_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(labels_dir, filename)
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        class_id = int(parts[0])
                        class_counts[class_id] += 1

    # Map class IDs to names (fallback to ID if name is missing)
    sorted_classes = sorted(class_counts.items())
    labels = [C[cid] if cid < 40 else f"ID {cid}" for cid, _ in sorted_classes]
    counts = [count for _, count in sorted_classes]

    # Create the visualization
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, counts, color='skyblue', edgecolor='black')
    
    # Style the chart
    plt.xlabel('Class Names', fontsize=12)
    plt.ylabel('Instance Count (Bounding Boxes)', fontsize=12)
    plt.title('Class Instance Distribution (YOLO Dataset)', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add exact values on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + (max(counts)*0.01), f'{yval}', ha='center', va='bottom')

    plt.tight_layout()
    plt.show()

plot_yolo_distribution("labels")
