#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pillow",
# ]
# ///

from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

try:
    from PIL import Image, ImageFilter
except ImportError:
    print(
        "Error: Pillow is required.\n"
        "  Run using: uv run cube2flaxlut.py ...",
        file=sys.stderr,
    )
    sys.exit(1)


# Constants
ROOT_DIR   = os.path.dirname(os.path.abspath(__file__)) # This is the Project Root
LUT_WIDTH  = 256 #Do not change
LUT_HEIGHT = 16  #Do not change


def validate_neutral_lut(img: Image.Image) -> None:
    """Raise ValueError if the image is not a valid 256x16 neutral LUT."""
    if img.size != (LUT_WIDTH, LUT_HEIGHT):
        raise ValueError(
            f"Neutral LUT must be {LUT_WIDTH}x{LUT_HEIGHT} pixels, "
            f"got {img.size[0]}x{img.size[1]}."
        )


def parse_cube(path: Path) -> tuple[int, list[float]]:
    """Parse an .cube file to extract the 3D grid size and float data."""
    size = 0
    data = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines or comments
            if not line or line.startswith("#"):
                continue

            if line.startswith("LUT_3D_SIZE"):
                size = int(line.split()[1])
            elif line.startswith("DOMAIN_MIN") or line.startswith("DOMAIN_MAX"):
                # Implicitly assuming standard [0, 1] bounds, which Pillow defaults to.
                pass
            elif line.startswith("TITLE"):
                pass
            elif line.startswith("LUT_1D_SIZE"):
                raise ValueError("1D LUTs are not supported. Please provide a 3D LUT .cube file.")
            else:
                # Should be a color value: R G B
                parts = line.split()
                if len(parts) == 3:
                    try:
                        data.extend([float(parts[0]), float(parts[1]), float(parts[2])])
                    except ValueError:
                        pass # Ignore non-float data gracefully

    if size == 0:
        raise ValueError("LUT_3D_SIZE not found in the .cube file.")

    expected_len = size * size * size * 3
    if len(data) != expected_len:
        raise ValueError(
            f"Expected {expected_len} values for a {size}^3 LUT, but got {len(data)}. "
            "The file might be corrupted or incorrectly formatted."
        )

    return size, data


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="cube2flaxlut.py",
        description="Convert an .cube 3D LUT to a Flax Engine 256x16 LUT PNG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  uv run cube2flaxlut.py grading.cube --neutral neutral.png
  uv run cube2flaxlut.py cinematic.cube -n neutral.png -o ./luts/
        """,
    )

    parser.add_argument(
        "cube_file",
        help="Path to the input .cube 3D LUT file.",
    )
    parser.add_argument(
        "--neutral", "-n",
        required=False,
        metavar="PNG",
        help="Path to the 256x16 neutral (identity) LUT PNG.",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="DIR",
        default=".",
        help="Output directory. Default: current directory.",
    )

    args = parser.parse_args(argv)

    cube_path = Path(args.cube_file)
    if not os.path.exists(cube_path):
        print(f"Error: .cube file not found: {cube_path}", file=sys.stderr)
        sys.exit(1)

    if args.neutral is None or len(args.neutral) == 0:
        neutral_path = os.path.join(ROOT_DIR, "neutral.png")
    else:
        neutral_path = Path(args.neutral)

    if not os.path.exists(neutral_path):
        print(f"Error: Neutral LUT not found: {neutral_path}", file=sys.stderr)
        sys.exit(1)

    # Load Neutral LUT
    try:
        neutral_img = Image.open(neutral_path)
        validate_neutral_lut(neutral_img)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error opening neutral LUT: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Neutral : {neutral_path} ({neutral_img.size[0]}x{neutral_img.size[1]}, {neutral_img.mode})")

    # Parse .cube File
    print(f"Loading : {cube_path}")
    try:
        lut_size, lut_data = parse_cube(cube_path)
    except Exception as e:
        print(f"Error parsing .cube file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"LUT     : 3D Grid, size {lut_size}^3")

    # Apply Trilinear Interpolation via Pillow
    print(f"Applying transformation to {LUT_WIDTH}x{LUT_HEIGHT} LUT...")
    try:
        # Make sure we're in RGB mode
        neutral_rgb = neutral_img.convert("RGB")

        # Color3DLUT natively processes the trilinear interpolation against the float table
        pillow_lut = ImageFilter.Color3DLUT(lut_size, lut_data)
        out_img = neutral_rgb.filter(pillow_lut)
    except Exception as e:
        print(f"Error applying LUT transformation: {e}", file=sys.stderr)
        sys.exit(1)

    # Save the Output
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_png = out_dir / f"{cube_path.stem}.png"
    out_img.save(out_png, format="PNG", optimize=False)

    print(f"\nOutput  : {out_png}")
    print(f"  Size  : {out_img.size[0]}x{out_img.size[1]} RGB PNG")
    print(f"  Import into Flax with: Format=RGB  Compression=None  Mipmaps=Off")
    print("\nDone.")


if __name__ == "__main__":
    main()
