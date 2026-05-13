"""Batch-crop raw camera images to square ROI (6×6 cm).

Basler acA2440-20gc captures 2448×2048.
This script crops the center 2048×2048 region (60×60 mm FOV)
so that labeling is done on the final ROI that the pipeline will use.

Usage:
    python scripts/crop_roi.py
    python scripts/crop_roi.py --input dataset/raw/ng --output dataset/cropped/ng
    python scripts/crop_roi.py --width 2048 --height 2048
"""

import argparse
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Basler acA2440-20gc varsayilan kirpma degerleri
# Tam goruntu: 2448 x 2048
# Kare kirpma: ortadan 2048 x 2048 (6x6 cm FOV)
DEFAULT_X1 = 200   # (2448 - 2048) / 2
DEFAULT_Y1 = 0
DEFAULT_CROP_W = 2048
DEFAULT_CROP_H = 2048


def crop_image(img, x1, y1, crop_w, crop_h):
    """Crop image to specified region, handling edge cases."""
    h, w = img.shape[:2]
    # Clamp to image boundaries
    x1 = max(0, min(x1, w - 1))
    y1 = max(0, min(y1, h - 1))
    x2 = min(x1 + crop_w, w)
    y2 = min(y1 + crop_h, h)
    return img[y1:y2, x1:x2]


def process_directory(input_dir, output_dir, x1, y1, crop_w, crop_h):
    """Recursively process all images in directory, preserving subfolder structure."""
    exts = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif")
    total = 0
    skipped = 0

    for root, dirs, files in os.walk(input_dir):
        # Preserve subfolder structure
        rel_path = os.path.relpath(root, input_dir)
        out_subdir = os.path.join(output_dir, rel_path)

        for f in sorted(files):
            if not f.lower().endswith(exts):
                continue

            img_path = os.path.join(root, f)
            img = cv2.imread(img_path)
            if img is None:
                print(f"  UYARI: Okunamadi, atlaniyor: {img_path}")
                skipped += 1
                continue

            h, w = img.shape[:2]

            # Eger goruntu zaten kare veya kirpma boyutundan kucukse atlama
            if w <= crop_w and h <= crop_h:
                print(f"  BILGI: Zaten kucuk ({w}x{h}), olduğu gibi kopyalaniyor: {f}")
                os.makedirs(out_subdir, exist_ok=True)
                cv2.imwrite(os.path.join(out_subdir, f), img)
                total += 1
                continue

            cropped = crop_image(img, x1, y1, crop_w, crop_h)
            os.makedirs(out_subdir, exist_ok=True)
            out_path = os.path.join(out_subdir, f)
            cv2.imwrite(out_path, cropped)
            total += 1

    return total, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Basler acA2440-20gc goruntuleri 6x6 cm ROI'ye kirpma"
    )
    parser.add_argument(
        "--input", type=str,
        default=os.path.join(PROJECT_ROOT, "dataset", "raw"),
        help="Girdi klasoru (varsayilan: dataset/raw)"
    )
    parser.add_argument(
        "--output", type=str,
        default=os.path.join(PROJECT_ROOT, "dataset", "cropped"),
        help="Cikti klasoru (varsayilan: dataset/cropped)"
    )
    parser.add_argument("--x1", type=int, default=DEFAULT_X1,
                        help=f"Kirpma baslangic X (varsayilan: {DEFAULT_X1})")
    parser.add_argument("--y1", type=int, default=DEFAULT_Y1,
                        help=f"Kirpma baslangic Y (varsayilan: {DEFAULT_Y1})")
    parser.add_argument("--width", type=int, default=DEFAULT_CROP_W,
                        help=f"Kirpma genisligi (varsayilan: {DEFAULT_CROP_W})")
    parser.add_argument("--height", type=int, default=DEFAULT_CROP_H,
                        help=f"Kirpma yuksekligi (varsayilan: {DEFAULT_CROP_H})")
    parser.add_argument("--preview", action="store_true",
                        help="Ilk goruntuyu kirpma oncesi/sonrasi goster")
    args = parser.parse_args()

    print("=" * 60)
    print("Jidoka 2.0 - ROI Kirpma")
    print("=" * 60)
    print(f"  Girdi:    {args.input}")
    print(f"  Cikti:    {args.output}")
    print(f"  Kirpma:   ({args.x1}, {args.y1}) -> ({args.x1 + args.width}, {args.y1 + args.height})")
    print(f"  Boyut:    {args.width} x {args.height} piksel")
    print("=" * 60)

    if not os.path.isdir(args.input):
        print(f"HATA: Girdi klasoru bulunamadi: {args.input}")
        sys.exit(1)

    if args.preview:
        # Find first image for preview
        for root, dirs, files in os.walk(args.input):
            for f in files:
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                    img = cv2.imread(os.path.join(root, f))
                    if img is not None:
                        h, w = img.shape[:2]
                        print(f"\nOnizleme: {f} ({w}x{h})")
                        # Draw ROI rectangle on original
                        preview = img.copy()
                        cv2.rectangle(preview,
                                      (args.x1, args.y1),
                                      (args.x1 + args.width, args.y1 + args.height),
                                      (0, 255, 0), 3)
                        cv2.putText(preview, "ROI (6x6 cm)",
                                    (args.x1 + 10, args.y1 + 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

                        # Show side by side
                        cropped = crop_image(img, args.x1, args.y1,
                                             args.width, args.height)
                        cv2.imshow("Orijinal + ROI", cv2.resize(preview, (800, 670)))
                        cv2.imshow("Kirpilmis", cv2.resize(cropped, (670, 670)))
                        print("Devam etmek icin bir tusa basin, iptal icin 'q'...")
                        key = cv2.waitKey(0) & 0xFF
                        cv2.destroyAllWindows()
                        if key == ord('q'):
                            print("Iptal edildi.")
                            sys.exit(0)
                        break
            else:
                continue
            break

    total, skipped = process_directory(
        args.input, args.output,
        args.x1, args.y1, args.width, args.height
    )

    print(f"\nTamamlandi!")
    print(f"  Kirpilan:  {total} goruntu")
    print(f"  Atlanan:   {skipped} goruntu")
    print(f"  Cikti:     {args.output}")
    print(f"\nSimdi LabelImg ile etiketlemeye baslayabilirsiniz:")
    print(f"  labelImg {args.output}")


if __name__ == "__main__":
    main()
