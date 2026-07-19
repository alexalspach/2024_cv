#!/usr/bin/env python3
"""
In plain terms: this writes each picture's real width & height onto its <img> tag so the
browser leaves the right amount of space for it BEFORE it loads. That stops the page from
jumping around as images pop in (which is also what makes "jump to a project" land correctly).
You normally don't run this yourself — it's a one-time helper; the everyday build already
reserves space for the thumbnails it makes.

--- technical details ---
Stamp intrinsic width/height on <img> tags so images reserve layout space before they
load (no layout shift -> accurate in-page anchor landing, less scroll jank).

We ONLY stamp images whose size is controlled by width (with auto height): the grid
thumbnails and the card-media sizing classes. We deliberately SKIP:
  - sticker images (.*-well-sticker / class contains "sticker") -> they use a FIXED CSS
    height with auto width, so a height attribute + the height:auto guard would break them.
  - images that already carry a width/height attribute (idempotent re-runs).
  - images with an inline style that sets width/height (bespoke, hand-tuned).

Pair this with the CSS guard (added to style.css):
    .well img[width][height], #da-thumbs img[width][height] { height: auto; }
so a CSS/attribute width scales height by the intrinsic ratio instead of using the raw
px height attribute. Run from anywhere; paths are resolved relative to the cv/ folder.

Usage:  python3 tools/stamp_image_dims.py [--check]
        --check : report what WOULD change, write nothing (exit 1 if changes pending).
"""
import os, re, sys, subprocess

CV_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cv")
import glob
# Project card bodies now live in cv/projects/*.html (assembled into projects.html by the
# generator), so stamp those; plus the still-hand-written experience.html / me.html.
FILES = (sorted(glob.glob(os.path.join(CV_DIR, "projects", "*.html")))
         + [os.path.join(CV_DIR, "experience.html"), os.path.join(CV_DIR, "me.html")])

# width-controlled, auto-height classes that are safe to stamp
SIZING_CLASSES = {
    "img-quad", "well-img", "well-img-half",
    "media-flex-img", "media-flex-img-fullwidth", "media-flex-img-halfwidth",
    "media-flex-img-thirdwidth", "media-flex-img-quarterwidth",
    "media-shadow",  # generic content-image shadow (e.g. inline-width art in cards)
}
GRID_THUMB_RE = re.compile(r"/projects/thumbs/[^\"']+")

IMG_RE = re.compile(r"<img\b[^>]*?>", re.IGNORECASE | re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
ATTR_RE = lambda name: re.compile(r'%s\s*=\s*"([^"]*)"' % name, re.IGNORECASE | re.DOTALL)

_dim_cache = {}
def dims(path):
    if path in _dim_cache:
        return _dim_cache[path]
    try:
        out = subprocess.check_output(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
            stderr=subprocess.DEVNULL, text=True)
        w = int(re.search(r"pixelWidth:\s*(\d+)", out).group(1))
        h = int(re.search(r"pixelHeight:\s*(\d+)", out).group(1))
        _dim_cache[path] = (w, h)
        return (w, h)
    except Exception:
        _dim_cache[path] = None
        return None

def should_stamp(tag):
    if ATTR_RE("width").search(tag) or ATTR_RE("height").search(tag):
        return False  # already stamped / hand-set
    style = ATTR_RE("style").search(tag)
    if style and re.search(r"\bheight\s*:", style.group(1), re.IGNORECASE):
        return False  # bespoke inline HEIGHT -> leave alone (would conflict with height:auto)
    # An inline width-only style is fine: the stamped attributes give the aspect ratio and the
    # CSS `.well img[width][height]{height:auto}` guard keeps height proportional to that width.
    cls = ATTR_RE("class").search(tag)
    classes = set(cls.group(1).split()) if cls else set()
    if any("sticker" in c for c in classes):
        return False
    src = ATTR_RE("src").search(tag)
    src_val = src.group(1) if src else ""
    if classes & SIZING_CLASSES:
        return True
    if GRID_THUMB_RE.search(src_val):
        return True
    return False

def process(text, base_dir, report):
    def repl(m):
        tag = m.group(0)
        if not should_stamp(tag):
            return tag
        src = ATTR_RE("src").search(tag)
        if not src:
            return tag
        path = os.path.normpath(os.path.join(base_dir, src.group(1)))
        d = dims(path)
        if not d:
            report["missing"].append(src.group(1))
            return tag
        w, h = d
        report["stamped"] += 1
        # insert right after "<img"
        return re.sub(r"<img\b", '<img width="%d" height="%d"' % (w, h), tag, count=1)
    # Transform only OUTSIDE HTML comments so commented-out (dead) markup is left alone.
    out, pos = [], 0
    for c in COMMENT_RE.finditer(text):
        out.append(IMG_RE.sub(repl, text[pos:c.start()]))
        out.append(c.group(0))  # comment untouched
        pos = c.end()
    out.append(IMG_RE.sub(repl, text[pos:]))
    return "".join(out)

def main():
    check = "--check" in sys.argv
    grand = 0
    for p in FILES:
        if not os.path.exists(p):
            continue
        text = open(p, encoding="utf-8").read()
        report = {"stamped": 0, "missing": []}
        new = process(text, CV_DIR, report)
        grand += report["stamped"]
        status = "would stamp" if check else "stamped"
        rel = os.path.relpath(p, CV_DIR)
        if report["stamped"] or report["missing"]:
            print("%-26s %s %d <img>%s" % (rel, status, report["stamped"],
                  ("  MISSING FILES: %s" % report["missing"][:5]) if report["missing"] else ""))
        if not check and new != text:
            open(p, "w", encoding="utf-8").write(new)
    if check and grand:
        sys.exit(1)

if __name__ == "__main__":
    main()
