"""Rename images under immediate subfolders: <folder_name>_001.<ext>, ...

Example:
    YOLO_Defects/
      adim_atlamasi/*.jpg   -> adim_atlamasi_001.jpg, ...
      adim_daralmasi/*.jpg

Two-phase rename avoids overwriting intermediate names on Windows.

Usage:
    cd C:\\path\\to\\jidoka
    python scripts/rename_dataset_by_folder.py --root "D:\\YOLO_Defects" --dry-run
    python scripts/rename_dataset_by_folder.py --root "D:\\YOLO_Defects"
"""

from __future__ import annotations

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp")
_TMP_MARKER = "__jidoka_rename_tmp_"


def _is_image(name: str) -> bool:
    return name.lower().endswith(IMAGE_EXTS)


def sorted_images(directory: str) -> list[str]:
    out: list[str] = []
    for name in sorted(os.listdir(directory), key=lambda s: (s.lower(), s)):
        if not _is_image(name):
            continue
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            out.append(path)
    return out


def immediate_subdirs(root: str) -> list[str]:
    dirs: list[str] = []
    for name in sorted(os.listdir(root), key=lambda s: s.lower()):
        p = os.path.join(root, name)
        if os.path.isdir(p):
            dirs.append(p)
    return dirs


def rename_one_subfolder(subdir: str, min_digits: int, dry_run: bool) -> int:
    slug = os.path.basename(os.path.normpath(subdir))
    imgs = sorted_images(subdir)
    if not imgs:
        print(f"  (atlandi) görüntü yok: {slug}")
        return 0

    width = max(min_digits, len(str(len(imgs))))

    temps: list[tuple[str, str]] = []
    finals: list[tuple[str, str]] = []

    for i, src in enumerate(imgs):
        ext = os.path.splitext(src)[1].lower()
        tmp = os.path.join(subdir, f"{_TMP_MARKER}{i:06d}{ext}")
        n = i + 1
        final_path = os.path.join(subdir, f"{slug}_{n:0{width}d}{ext}")
        temps.append((src, tmp))
        finals.append((tmp, final_path))

    print(f"  [{slug}] {len(imgs)} dosya")
    if dry_run:
        for src, (_, final_path) in zip(imgs, finals):
            print(f"    {os.path.basename(src)} -> {os.path.basename(final_path)}")
        return len(imgs)

    for src, tmp in temps:
        if os.path.abspath(src) == os.path.abspath(tmp):
            continue
        if os.path.exists(tmp):
            print(f"HATA: Geçici isim dolu (yarım kalmış işlem?): {tmp}", file=sys.stderr)
            sys.exit(1)
        os.rename(src, tmp)

    for tmp, final_path in finals:
        if os.path.abspath(tmp) == os.path.abspath(final_path):
            continue
        if os.path.exists(final_path):
            print(f"HATA: Bu isim zaten var: {final_path}", file=sys.stderr)
            sys.exit(1)
        os.rename(tmp, final_path)

    return len(imgs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Alt klasördeki fotoğrafları <klasörAdı>_NNN biçiminde sıralı adlandırır.",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=os.path.join(PROJECT_ROOT, "YOLO_Defects"),
        help=r'Üst klasör (örn. "...\\YOLO_Defects")',
    )
    parser.add_argument(
        "--digits",
        type=int,
        default=3,
        help="Minimum basamak (varsayılan 3 -> 001; çok görselde otomatik genişler)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Sadece listele")
    args = parser.parse_args()

    root = os.path.abspath(os.path.expanduser(args.root))
    min_digits = max(1, args.digits)

    if not os.path.isdir(root):
        print(f"HATA: Klasör yok: {root}", file=sys.stderr)
        sys.exit(1)

    subdirs = immediate_subdirs(root)
    if not subdirs:
        print(f"HATA: Alt klasör yok: {root}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(f"Kök: {root}")
    print(f"Mod: {'DRY-RUN' if args.dry_run else 'UYGULA'}")
    print("=" * 60)

    total = 0
    for sd in subdirs:
        total += rename_one_subfolder(sd, min_digits, args.dry_run)

    if args.dry_run:
        print("\nUygulamak için --dry-run olmadan tekrar çalıştırın.")
    else:
        print(f"\nTamam — toplam {total} dosya güncellendi.")


if __name__ == "__main__":
    main()
