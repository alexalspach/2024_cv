#!/usr/bin/env python3
# =============================================================================
#  gen_thumb.py  —  turn any photo into a neat square thumbnail (no Photoshop).
#
#  It cuts the photo to a square from the middle, shrinks it, and saves a small
#  JPEG. build_projects.py calls this for you when a project has a "hero_img",
#  but you can also run it by hand:
#
#    python3 tools/gen_thumb.py SOURCE OUT [SIZE]
#    python3 tools/gen_thumb.py ~/photo.jpg assets/images/projects/thumbs/NewProjthumb.jpg
#
#  Uses the built-in macOS `sips` tool, so there's nothing to install.
# =============================================================================
import os, re, shutil, subprocess, sys, tempfile

def dims(path):
    """Return an image's (width, height) in pixels."""
    out = subprocess.check_output(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                                  text=True, stderr=subprocess.DEVNULL)
    return (int(re.search(r"pixelWidth:\s*(\d+)", out).group(1)),
            int(re.search(r"pixelHeight:\s*(\d+)", out).group(1)))

def make_thumb(source, out, size=400, quality=70):
    """Center-crop `source` to a square and resize to `size`px, writing a JPEG to `out`."""
    w, h = dims(source)
    side = min(w, h)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(source)[1] or ".jpg")
    os.close(fd)
    shutil.copyfile(source, tmp)
    try:
        # -c crops (centered) to HEIGHT WIDTH; then -Z resizes the longest side (square stays square)
        subprocess.run(["sips", "-c", str(side), str(side), tmp],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sips", "-Z", str(size),
                        "-s", "format", "jpeg", "-s", "formatOptions", str(quality),
                        tmp, "--out", out],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        os.remove(tmp)
    return dims(out)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    src, out = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    print("wrote %s %s" % (out, make_thumb(src, out, size)))
