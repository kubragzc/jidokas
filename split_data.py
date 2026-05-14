"""Split labeled images into train/val sets (80/20).

Copies images and their YOLO label files from dataset/raw/ (after labeling)
into dataset/images/{train,val}/ and dataset/labels/{train,val}/.

Usage:
    python scripts/split_dataset.py
    python scripts/split_dataset.py --ratio 0.2
    python scripts/split_dataset.py --input dataset/raw/ng --seed 42
"""

import argparse
import glob
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def collect_image_label_pairs(input_dir: str):
    """Recursively find all images and their matching label files."""
    exts = (".jpg", ".jpeg", ".png", ".bmp")
    pairs = []

    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if f.lower().endswith(exts):
                img_path = os.path.join(root, f)
                stem = os.path.splitext(f)[0]
                # Label file next to image
                lbl_path = os.path.join(root, stem + ".txt")
                if os.path.exists(lbl_path):
                    pairs.append((img_path, lbl_path))
                else:
                    # Check if there's a labels/ sibling directory
                    parent = os.path.dirname(root)
                    lbl_alt = os.path.join(parent, "labels", stem + ".txt")
                    if os.path.exists(lbl_alt):
                        pairs.append((img_path, lbl_alt))
                    else:
                        print(f"  UYARI: Etiket bulunamadi, atlaniyor: {img_path}")
    return pairs


def main():
    parser = argparse.ArgumentParser(
        description="Split labeled dataset into train/val"
    )
    parser.add_argument(
        "--input", type=str,
        default=os.path.join(PROJECT_ROOT, "dataset", "raw", "ng"),
        help="Input directory containing labeled images (default: dataset/raw/ng)"
    )
    parser.add_argument(
        "--output", type=str,
        default=os.path.join(PROJECT_ROOT, "dataset"),
        help="Output base directory (default: dataset/)"
    )
    parser.add_argument(
        "--ratio", type=float, default=0.2,
        help="Validation split ratio (default: 0.2 = 20%%)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--copy", action="store_true", default=True,
        help="Copy files (default). Use --move to move instead."
    )
    parser.add_argument(
        "--move", action="store_true", default=False,
        help="Move files instead of copying"
    )
    args = parser.parse_args()

    random.seed(args.seed)

    train_img_dir = os.path.join(args.output, "images", "train")
    val_img_dir = os.path.join(args.output, "images", "val")
    train_lbl_dir = os.path.join(args.output, "labels", "train")
    val_lbl_dir = os.path.join(args.output, "labels", "val")

    for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        os.makedirs(d, exist_ok=True)

    print(f"Girdi klasoru: {args.input}")
    pairs = collect_image_label_pairs(args.input)

    if not pairs:
        print("HATA: Etiketli goruntu bulunamadi!")
        print("Once LabelImg ile etiketleme yapin.")
        sys.exit(1)

    print(f"Toplam {len(pairs)} etiketli goruntu bulundu")

    random.shuffle(pairs)
    val_count = max(1, int(len(pairs) * args.ratio))
    val_pairs = pairs[:val_count]
    train_pairs = pairs[val_count:]

    print(f"Train: {len(train_pairs)} | Val: {val_count}")

    transfer = shutil.move if args.move else shutil.copy2

    for img_path, lbl_path in train_pairs:
        img_name = os.path.basename(img_path)
        lbl_name = os.path.splitext(img_name)[0] + ".txt"
        transfer(img_path, os.path.join(train_img_dir, img_name))
        transfer(lbl_path, os.path.join(train_lbl_dir, lbl_name))

    for img_path, lbl_path in val_pairs:
        img_name = os.path.basename(img_path)
        lbl_name = os.path.splitext(img_name)[0] + ".txt"
        transfer(img_path, os.path.join(val_img_dir, img_name))
        transfer(lbl_path, os.path.join(val_lbl_dir, lbl_name))

    print(f"\nTamamlandi!")
    print(f"  Train goruntuler: {train_img_dir}")
    print(f"  Train etiketler:  {train_lbl_dir}")
    print(f"  Val goruntuler:   {val_img_dir}")
    print(f"  Val etiketler:    {val_lbl_dir}")

    # Print class distribution
    class_counts = {}
    for _, lbl_path in pairs:
        with open(lbl_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    cls_id = int(parts[0])
                    class_counts[cls_id] = class_counts.get(cls_id, 0) + 1

    if class_counts:
        names = {
            0: "sokulme",
            1: "gevsek_dikis",
            2: "cit_kaymasi",
            3: "kirisiklik",
            4: "boncuk",
            5: "adim_daralmasi",
            6: "adim_atlama",
        }
        print("\nSinif dagilimi:")
        for cls_id in sorted(class_counts.keys()):
            name = names.get(cls_id, f"class_{cls_id}")
            print(f"  [{cls_id}] {name}: {class_counts[cls_id]} adet")


if __name__ == "__main__":
    main()
