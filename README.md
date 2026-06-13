# Cube2FlaxLUT

## What is this?
This script converts a [Cube LUT](https://en.wikipedia.org/wiki/3D_lookup_table) into a 256×16 LUT texture for [Flax Engine](https://flaxengine.com/).

The used PNG format is based on Flax docs:
> LUT textures used in Flax must be unwrapped 256x16 textures imported without compression, without mipmaps and with only the RGB channels used.  

https://docs.flaxengine.com/manual/graphics/post-effects/color-grading.html#custom-lut-textures


## The 256×16 format
Flax Engine (and several other engines) uses a 256×16 unwrapped 3D LUT:

• 16 tiles of 16×16 pixels, arranged left-to-right in a single row.  
• Tile index (px // 16) = Blue axis (0/15 … 15/15)  
• Column in tile (px % 16) = Red axis (0/15 … 15/15)  
• Row (py) = Green axis (0/15 … 15/15)  

The pixel value at each position represents the *output* color for the
corresponding *input* (R, G, B).  The neutral LUT maps every input to
itself, leaving the image unchanged.  This script replaces each output
with the nearest color from the chosen palette, so applying the result
LUT posterizes any image to that palette.

## Usage

See the following examples. You can ignore the -n parameter, the tool will use [Flax Engine's default neutral LUT](https://docs.flaxengine.com/manual/graphics/post-effects/color-grading.html#custom-lut-textures) if none is provided.

### Examples

```uv run main.py "path/to/my-lut.cube" -o "path/to/LUTs```  
```uv run main.py "path/to/my-lut.cube" -n path/to/neutral_lut.png -o "path/to/LUTs```  

### Import settings in Flax
When importing the output PNG into Flax Engine:
    • Format       : RGB (no alpha)
    • Compression  : None (lossless — LUT data must not be approximated)
    • Mipmaps      : disabled
    • sRGB         : depends on your project's color pipeline
