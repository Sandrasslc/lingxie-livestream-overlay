#!/usr/bin/env python3
"""Finalize a Lingxie livestream overlay with an exact QR and alpha checks."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Tuple

from PIL import Image


Box = Tuple[int, int, int, int]


def parse_box(value: str) -> Box:
    try:
        parts = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("box must be left,top,width,height") from exc
    if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        raise argparse.ArgumentTypeError("box must be left,top,width,height with positive size")
    return parts  # type: ignore[return-value]


def parse_size(value: str) -> Tuple[int, int]:
    try:
        width, height = (int(part) for part in value.lower().split("x", 1))
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("size must be WIDTHxHEIGHT") from exc
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("size must be positive")
    return width, height


def auto_qr_box(path: Path, margin_ratio: float) -> Box:
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is required for automatic QR detection; pass --qr-source-box instead"
        ) from exc

    image = cv2.imread(str(path))
    if image is None:
        raise RuntimeError(f"cannot read QR source: {path}")

    detector = cv2.QRCodeDetector()
    detected, points = detector.detect(image)
    if not detected or points is None:
        raise RuntimeError("QR detection failed; inspect the image and pass --qr-source-box")

    points = points.reshape(-1, 2)
    x1 = float(points[:, 0].min())
    y1 = float(points[:, 1].min())
    x2 = float(points[:, 0].max())
    y2 = float(points[:, 1].max())
    side = max(x2 - x1, y2 - y1)
    pad = side * margin_ratio
    height, width = image.shape[:2]
    left = max(0, math.floor(x1 - pad))
    top = max(0, math.floor(y1 - pad))
    right = min(width, math.ceil(x2 + pad))
    bottom = min(height, math.ceil(y2 + pad))
    crop_side = min(right - left, bottom - top)
    return left, top, crop_side, crop_side


def crop_by_box(image: Image.Image, box: Box) -> Image.Image:
    left, top, width, height = box
    if left < 0 or top < 0 or left + width > image.width or top + height > image.height:
        raise ValueError(f"crop box {box} exceeds image bounds {image.size}")
    return image.crop((left, top, left + width, top + height))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True, help="generated transparent PNG")
    parser.add_argument("--qr-source", type=Path, required=True, help="image containing original QR")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=parse_size, default=parse_size("1920x1080"))
    parser.add_argument("--qr-source-box", type=parse_box)
    parser.add_argument("--qr-margin", type=float, default=0.03)
    parser.add_argument("--qr-dest", type=parse_box, default=parse_box("1650,785,205,205"))
    parser.add_argument(
        "--transparent-box", type=parse_box, default=parse_box("100,180,1400,700")
    )
    parser.add_argument("--min-transparent-ratio", type=float, default=0.98)
    args = parser.parse_args()

    if not 0 <= args.min_transparent_ratio <= 1:
        parser.error("--min-transparent-ratio must be between 0 and 1")

    resampling = getattr(Image, "Resampling", Image)
    base = Image.open(args.base).convert("RGBA").resize(args.size, resampling.LANCZOS)
    qr_source = Image.open(args.qr_source).convert("RGB")
    source_box = args.qr_source_box or auto_qr_box(args.qr_source, args.qr_margin)
    qr = crop_by_box(qr_source, source_box)

    dest_left, dest_top, dest_width, dest_height = args.qr_dest
    if dest_left < 0 or dest_top < 0 or dest_left + dest_width > base.width or dest_top + dest_height > base.height:
        raise ValueError(f"QR destination {args.qr_dest} exceeds output bounds {base.size}")
    qr = qr.resize((dest_width, dest_height), resampling.NEAREST).convert("RGBA")
    base.alpha_composite(qr, (dest_left, dest_top))

    transparent = crop_by_box(base.getchannel("A"), args.transparent_box)
    histogram = transparent.histogram()
    total = transparent.width * transparent.height
    transparent_ratio = histogram[0] / total
    if transparent_ratio < args.min_transparent_ratio:
        raise RuntimeError(
            f"transparent area check failed: {transparent_ratio:.3%} < {args.min_transparent_ratio:.3%}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    base.save(args.output, format="PNG")
    print(f"output={args.output}")
    print(f"size={base.width}x{base.height} channels=RGBA alpha=true")
    print(f"qr_source_box={source_box} qr_dest={args.qr_dest}")
    print(f"transparent_ratio={transparent_ratio:.3%}")


if __name__ == "__main__":
    main()
