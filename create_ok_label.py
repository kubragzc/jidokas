"""Create empty YOLO label files for OK (defect-free) images.

YOLO uses empty .txt files as 'negative examples' — frames with no defects.
This helps the model learn what a normal stitch looks like and reduces
false positives. Recommended: 10-20% of training set should be OK images.

Usage:
    python scripts/create_ok_labels.py
    python scripts/create_ok_labels.py --input dataset/cropped/ok --output dataset/images/train
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(
        description="OK goruntuleri icin bos YOLO etiket dosyalari olustur"
    )
    parser.add_argument(
        "--input", type=str,
        default=os.path.join(PROJECT_ROOT, "dataset", "cropped", "ok"),
        help="OK goruntu klasoru (varsayilan: dataset/cropped/ok)"
    )
    parser.add_argument(
        "--output-images", type=str,
        default=os.path.join(PROJECT_ROOT, "dataset", "images", "train"),
        help="Goruntulerin kopyalanacagi klasor"
    )
    parser.add_argument(
        "--output-labels", type=str,
        default=os.path.join(PROJECT_ROOT, "dataset", "labels", "train"),
        help="Bos etiketlerin olusturulacagi klasor"
    )
    parser.add_argument(
        "--val-ratio", type=float, default=0.2,
        help="Val setine gidecek OK gorsellerin orani (varsayilan: 0.2)"
    )
    args = parser.parse_args()

    exts = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif")
    files = [f for f in os.listdir(args.input) if f.lower().endswith(exts)]
    files.sort()

    if not files:
        print(f"HATA: {args.input} klasorunde goruntu bulunamadi!")
        sys.exit(1)

    # Split into train/val
    import random
    random.seed(42)
    random.shuffle(files)
    val_count = max(1, int(len(files) * args.val_ratio))
    val_files = files[:val_count]
    train_files = files[val_count:]

    # Create directories
    train_img_dir = args.output_images
    train_lbl_dir = args.output_labels
    val_img_dir = train_img_dir.replace("train", "val")
    val_lbl_dir = train_lbl_dir.replace("train", "val")

    for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
        os.makedirs(d, exist_ok=True)

    print(f"OK goruntuler: {len(files)} adet")
    print(f"  Train: {len(train_files)}")
    print(f"  Val:   {len(val_files)}")

    # Copy images and create empty labels
    for f in train_files:
        shutil.copy2(os.path.join(args.input, f), os.path.join(train_img_dir, f))
        stem = os.path.splitext(f)[0]
        label_path = os.path.join(train_lbl_dir, stem + ".txt")
        open(label_path, "w").close()  # Empty file

    for f in val_files:
        shutil.copy2(os.path.join(args.input, f), os.path.join(val_img_dir, f))
        stem = os.path.splitext(f)[0]
        label_path = os.path.join(val_lbl_dir, stem + ".txt")
        open(label_path, "w").close()  # Empty file

    total = len(train_files) + len(val_files)
    print(f"\nTamamlandi! {total} OK goruntu + bos etiket olusturuldu.")
    print(f"  Train: {train_img_dir}")
    print(f"  Val:   {val_img_dir}")
    print(f"\nBu goruntuler YOLO'ya 'burada hata yok' ogretir (negatif ornek).")


if __name__ == "__main__":
    main()
