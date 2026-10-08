#!/usr/bin/env python3
"""
prep_photo.py
Preprocesses a user photo for ASCII art generation:
- Removes background using rembg (if installed)
- Enhances contrast using OpenCV CLAHE or PIL fallback
- Composites onto white background
- Converts to grayscale and saves to data/preprocessed_photo.png
"""

import argparse
import os
import sys
from PIL import Image, ImageEnhance, ImageOps

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_PHOTO = os.path.join(DATA_DIR, "preprocessed_photo.png")


def preprocess_image(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"[ERROR] Input photo file not found at: {input_path}")
        sys.exit(1)

    print(f"[INFO] Processing photo: {input_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Load image
    img = Image.open(input_path).convert("RGBA")

    # 1. Background removal using rembg (if available)
    try:
        from rembg import remove
        print("[INFO] Applying background removal using rembg...")
        img_bytes = remove(img)
        if isinstance(img_bytes, bytes):
            import io
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        else:
            img = img_bytes
    except ImportError:
        print("[NOTICE] 'rembg' package not installed. Skipping automatic background removal.")
        print("         To enable background removal, install: pip install rembg")

    # Auto-crop face/headshot for wide or full-body portrait photos if aspect ratio is ~1:1
    w, h = img.size
    if 0.8 <= (w / float(h)) <= 1.2:
        print("[INFO] Applying automatic face/headshot crop focus...")
        left = int(w * 0.35)
        top = int(h * 0.22)
        right = int(w * 0.68)
        bottom = int(h * 0.65)
        img = img.crop((left, top, right, bottom))

    # Composite subject onto white background
    white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, img).convert("L")

    # 2. Enhance contrast using OpenCV CLAHE (if available) or PIL fallback
    try:
        import cv2
        import numpy as np
        print("[INFO] Applying OpenCV CLAHE contrast enhancement...")
        np_img = np.array(composited)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced_np = clahe.apply(np_img)
        final_img = Image.fromarray(enhanced_np)
    except ImportError:
        print("[INFO] OpenCV not installed. Using PIL contrast enhancement fallback...")
        enhancer = ImageEnhance.Contrast(composited)
        final_img = enhancer.enhance(1.8)

    final_img.save(output_path, "PNG")
    print(f"[SUCCESS] Preprocessed photo saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Preprocess a photo for ASCII portrait SVG generation.")
    parser.add_argument("photo_path", nargs="?", help="Path to input photo (jpg, png, etc.)")
    args = parser.parse_args()

    photo_path = args.photo_path

    if not photo_path:
        # Search for potential photo files in common locations
        candidates = [
            os.path.join(DATA_DIR, "photo.jpg"),
            os.path.join(DATA_DIR, "photo.png"),
            os.path.join(DATA_DIR, "profile.jpg"),
            os.path.join(DATA_DIR, "profile.png"),
            "d.1.jpeg",
            "IMG_9746.JPG.jpeg",
            "photo.jpg",
            "photo.png",
            "profile.jpg",
            "profile.png"
        ]
        for cand in candidates:
            if os.path.exists(cand):
                photo_path = cand
                break

    if not photo_path:
        print("[NOTICE] No photo path provided and no default photo found (photo.jpg / profile.jpg).")
        print("         Usage: python scripts/prep_photo.py path/to/your_photo.jpg")
        print("         When no photo is provided, make_ascii_svg.py will render a placeholder portrait.")
        sys.exit(0)

    preprocess_image(photo_path, OUTPUT_PHOTO)


if __name__ == "__main__":
    main()
