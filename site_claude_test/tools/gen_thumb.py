#!/usr/bin/env python3
# =============================================================================
#  gen_thumb.py  —  turn any photo into a neat square thumbnail (no Photoshop).
#
#  It picks a square out of your photo and shrinks it to a small JPEG.
#  By default it keeps the CENTER, but you can choose which part to keep:
#
#     a name:  center (default) · top · bottom · left · right ·
#              top-left · top-right · bottom-left · bottom-right
#     a spot:  "<x>% <y>%"   (0% = left/top, 100% = right/bottom), e.g. "30% 10%"
#
#  build_projects.py calls this for you when a project has a "hero_img" (and an
#  optional "crop"); you can also run it by hand:
#
#     python3 tools/gen_thumb.py SOURCE OUT [SIZE] [CROP]
#     python3 tools/gen_thumb.py ~/photo.jpg out.jpg 400 top-left
#
#  Off-center crops use Pillow (pip3 install Pillow). Without Pillow it still
#  works, but can only keep the center (via the built-in macOS `sips`).
# =============================================================================
import os, re, shutil, subprocess, sys, tempfile

# Named crop spots -> (x fraction, y fraction). 0 = left/top edge, 1 = right/bottom edge.
_NAMED = {
    "center": (0.5, 0.5),
    "top": (0.5, 0.0), "bottom": (0.5, 1.0),
    "left": (0.0, 0.5), "right": (1.0, 0.5),
    "top-left": (0.0, 0.0), "top-right": (1.0, 0.0),
    "bottom-left": (0.0, 1.0), "bottom-right": (1.0, 1.0),
}

def _crop_fractions(crop):
    """Turn a crop choice into (fx, fy), each 0..1. Accepts a name (see _NAMED) or a
    focal point like '20% 80%'. Anything unrecognized falls back to center."""
    if not crop:
        return (0.5, 0.5)
    c = str(crop).strip().lower()
    if c in _NAMED:
        return _NAMED[c]
    nums = re.findall(r"-?\d+(?:\.\d+)?", c)          # e.g. "30% 10%" -> ["30","10"]
    if len(nums) >= 2:
        clamp = lambda v: max(0.0, min(1.0, v / 100.0))
        return (clamp(float(nums[0])), clamp(float(nums[1])))
    return (0.5, 0.5)

def dims(path):
    """Return an image's (width, height) in pixels (via macOS sips)."""
    out = subprocess.check_output(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                                  text=True, stderr=subprocess.DEVNULL)
    return (int(re.search(r"pixelWidth:\s*(\d+)", out).group(1)),
            int(re.search(r"pixelHeight:\s*(\d+)", out).group(1)))

def _make_thumb_sips(source, out, size, quality):
    """Fallback used only when Pillow isn't installed. `sips` can only crop from the CENTER."""
    w, h = dims(source); side = min(w, h)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(source)[1] or ".jpg"); os.close(fd)
    shutil.copyfile(source, tmp)
    try:
        subprocess.run(["sips", "-c", str(side), str(side), tmp],           # centered square crop
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sips", "-Z", str(size), "-s", "format", "jpeg",    # resize + save JPEG
                        "-s", "formatOptions", str(quality), tmp, "--out", out],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        os.remove(tmp)
    return dims(out)

def make_thumb(source, out, size=400, quality=70, crop="center"):
    """Crop `source` to a square (keeping the part named by `crop`) and resize to `size`px,
    writing a JPEG to `out`. See the top of this file for the accepted `crop` values."""
    fx, fy = _crop_fractions(crop)
    try:
        from PIL import Image
    except ImportError:
        if (fx, fy) != (0.5, 0.5):
            print("  note: install Pillow (pip3 install Pillow) to use crop=%r; using center for now" % crop)
        return _make_thumb_sips(source, out, size, quality)

    resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS")   # works on old & new Pillow
    img = Image.open(source).convert("RGB")
    w, h = img.size
    side = min(w, h)
    # Slide the square toward the chosen spot; the axis that has no spare room just stays at 0.
    left = round(fx * (w - side))
    top = round(fy * (h - side))
    img = img.crop((left, top, left + side, top + side)).resize((size, size), resample)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out, "JPEG", quality=quality)
    return (size, size)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    src, out = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    crop = sys.argv[4] if len(sys.argv) > 4 else "center"
    print("wrote %s %s (crop=%s)" % (out, make_thumb(src, out, size, crop=crop), crop))
