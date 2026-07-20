#!/usr/bin/env python3
# =============================================================================
#  build_projects.py  —  builds the "Robots, etc." page (and the homepage's
#  Featured box) from your fact file. You run this after editing a project.
#
#  In plain terms: you fill in ONE record per project, this script stamps it into
#  the big web page for you, so the picture grid, the contents list, and the full
#  write-up always match. You do NOT edit cv/projects.html by hand — this writes it.
#
#  What it reads:
#    cv/data/projects.json      one record per project (facts + its grid picture),
#                               plus 'indexFeatured' (which show on the homepage)
#    cv/projects/<id>.html      each project's write-up (the card body)
#    cv/projects.template.html  the page skeleton with {{GRID}} {{TOC}} {{CARDS}} blanks
#
#  What it writes:
#    cv/projects.html           the finished page
#    index.html                 just the "Featured projects" box on the homepage
#    ...and a square thumbnail   auto-cropped from a project's hero_img, if it has one
#
#  Order on the page = the order of records in projects.json (newest first). The
#  contents list is grouped by year. A record with no "thumb" simply has no grid
#  picture; a record with "hidden": true is shown nowhere.
#
#  How to run it:
#    python3 tools/build_projects.py                # rebuild
#    python3 tools/build_projects.py --check        # just check if it's up to date
#    python3 tools/build_projects.py --force-thumbs # also remake every thumbnail
#  (Tip: `python3 tools/build.py` runs this AND the papers/patents build together.)
# =============================================================================
import os, re, sys, subprocess

# Let this script import its siblings (the thumbnail maker + the data loader) from this folder.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_thumb import make_thumb
import dataio

# Handy folder locations (worked out from where this file lives).
CV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cv")
SITE = os.path.join(CV, "..")                                        # the site root
THUMB_DIR = os.path.join(CV, "..", "assets", "images", "projects", "thumbs")
THUMB_SIZE = 165  # match the site's existing 165x165 thumbnails (the grid shows them at this size)

# Normally a thumbnail is only (re)made when its hero image is new/changed. Pass --force-thumbs
# to remake every thumbnail from its hero image — handy after changing a "crop" setting.
FORCE_THUMBS = "--force-thumbs" in sys.argv

# The filter-tag highlight outline (editable in Illustrator). See ensure_outline_svg().
OUTLINE_SVG = os.path.join(CV, "..", "assets", "styles", "css", "tag-highlight.svg")

def ensure_outline_svg():
    """Self-heal the filter-tag outline SVG after an Illustrator re-export. Illustrator drops the
    attributes it needs and crops the artboard tight to the shape; we re-add/repair three things so
    a fresh export just works:
      1. preserveAspectRatio="none" on <svg>  -> stretches to the tag width instead of letterboxing
      2. vector-effect="non-scaling-stroke" on <path> -> even outline thickness at any width
      3. viewBox padding -> the on-screen (non-scaling) ~3px stroke is thick relative to a tiny tag,
         so with a tight artboard its outer half spills past the viewBox and gets CLIPPED into flat
         edges. We pad the viewBox ~9% on every side (aspect preserved, so no stretch) to give the
         stroke room. Only the tight "0 0 W H" form Illustrator exports is padded, so repeat builds
         don't compound it. .sort-outline in style.css scales up to match this padding."""
    if not os.path.exists(OUTLINE_SVG):
        return
    svg = open(OUTLINE_SVG, encoding="utf-8").read()
    orig = svg
    if "preserveAspectRatio" not in svg:
        svg = re.sub(r'(<svg\b[^>]*?)\s*>', r'\1 preserveAspectRatio="none">', svg, count=1)
    if "vector-effect" not in svg:
        svg = re.sub(r'<path\b', '<path vector-effect="non-scaling-stroke"', svg, count=1)
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)   # only the tight, un-padded export form
    if vb:
        w, h = float(vb.group(1)), float(vb.group(2))
        px, py = w * 0.09, h * 0.09                            # 9% each side, same fraction -> aspect kept
        svg = svg[:vb.start()] + ('viewBox="%.2f %.2f %.2f %.2f"' % (-px, -py, w + 2 * px, h + 2 * py)) + svg[vb.end():]
    if svg != orig:
        open(OUTLINE_SVG, "w", encoding="utf-8").write(svg)
        print("  patched tag-highlight.svg (preserveAspectRatio + non-scaling-stroke + viewBox padding)")

# The filter buttons, in the order they appear. We list tags in this order so every
# generated tag list reads the same way (purely cosmetic — order doesn't affect filtering).
TAG_ORDER = ["videos", "soft", "tactile", "manipulation", "hri", "humanoids", "wearable",
             "mobilerobots", "pathplanning", "navigation", "computervision", "designmfg",
             "hwdev", "swdev", "international", "korea", "drexel", "hubolab", "simlab",
             "disney", "tri", "walden", "thesis"]

# A few tags have a friendly spelling on the buttons but a short "code" in the HTML class.
# Everything else just loses its spaces/punctuation. So you can write either spelling.
_TAG_ALIASES = {"vision": "computervision", "toyota": "tri", "toyotatri": "tri"}


# --- small helpers -----------------------------------------------------------

def norm_tag(t):
    """Turn a tag into its CSS class: lowercase and drop spaces/punctuation, then map the few
    friendly names to their code. So 'design/mfg'->'designmfg', 'h/w dev'->'hwdev',
    'vision'->'computervision', 'toyota (tri)'->'tri'. Codes like 'designmfg' pass straight through."""
    key = re.sub(r"[^a-z0-9]", "", str(t).strip().lower())
    return _TAG_ALIASES.get(key, key)

_dim_cache = {}  # remember image sizes we've already measured (don't re-run sips)
def dims(path):
    """Return an image's (width, height) in pixels using the built-in macOS `sips` tool,
    or None if it can't be read. We stamp these onto <img> tags so the page doesn't jump
    around while images load."""
    if path in _dim_cache:
        return _dim_cache[path]
    try:
        out = subprocess.check_output(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                                      stderr=subprocess.DEVNULL, text=True)
        w = int(re.search(r"pixelWidth:\s*(\d+)", out).group(1))
        h = int(re.search(r"pixelHeight:\s*(\d+)", out).group(1))
        _dim_cache[path] = (w, h)
    except Exception:
        _dim_cache[path] = None
    return _dim_cache[path]

# Content-image classes whose CSS sets the display WIDTH as a percentage, so the height follows
# the picture's real aspect ratio. These MUST carry the file's true pixel size or the reserved
# space is the wrong shape and the page jumps as they load. (Fixed-size square thumbnails like
# img-quad are deliberately NOT here — their 200x200 is intentional, not the file's real ratio.)
WIDTH_SIZED_CLASSES = {"media-flex-img-fullwidth", "media-flex-img-halfwidth",
                       "media-flex-img-thirdwidth", "media-flex-img-quarterwidth"}

def correct_img_dims(body, base_dir):
    """Stamp the real file width/height onto width-sized content images, replacing any hand-typed
    values. Those images size by CSS width + aspect ratio, so wrong dimensions reserve the wrong
    height and the page jumps as they load (which also breaks anchor scrolling). The rendered size
    doesn't change — only the reserved space becomes correct. Fixed-height images / stickers are
    left alone (they aren't in WIDTH_SIZED_CLASSES)."""
    def repl(m):
        tag = m.group(0)
        cls = re.search(r'class="([^"]*)"', tag, re.IGNORECASE)
        if not cls or not (set(cls.group(1).split()) & WIDTH_SIZED_CLASSES):
            return tag
        src = re.search(r'src="([^"]*)"', tag, re.IGNORECASE)
        if not src:
            return tag
        d = dims(os.path.normpath(os.path.join(base_dir, src.group(1))))
        if not d:
            print("  WARNING: could not read image for size: %s" % src.group(1))
            return tag
        tag = re.sub(r'\s+(?:width|height)\s*=\s*"[^"]*"', "", tag)   # drop any mistyped dims
        return re.sub(r"<img\b", '<img width="%d" height="%d"' % d, tag, count=1)
    return re.sub(r"<img\b[^>]*?>", repl, body, flags=re.IGNORECASE | re.DOTALL)

def reserve_img_space(body):
    """Make hand-written <img> sizes actually reserve space so the page doesn't jump as images
    load (which also throws off anchor scrolling). HTML width/height attributes must be bare
    numbers — a CSS-style unit like height="290px" is INVALID and silently ignored by browsers,
    leaving the image with no reserved height. Strip that stray px/em/pt so height="290px"
    becomes a valid height="290". (Percentages are left alone — those are honored.)"""
    return re.sub(r'(\b(?:width|height)\s*=\s*")(\d+)(?:px|em|rem|pt)(\s*")',
                  r'\1\2\3', body, flags=re.IGNORECASE)

def classes(proj):
    """Build the CSS class list for a project (this is what the filter buttons match on).
    Tags come from ONE place — the project's record — so the grid tile, the contents row,
    and the card all get the exact same tags. That's what stops them drifting apart."""
    toks = ["sortable-div"]
    if proj.get("featured"):
        toks.append("featured")
    toks.append("all")                                        # every item is in "all"
    tags = []
    for t in proj.get("tags", []):
        nt = norm_tag(t)
        if nt and nt not in ("featured", "all") and nt not in tags:   # structural, not content tags
            tags.append(nt)
    toks += [t for t in TAG_ORDER if t in tags]               # known tags, in button order
    toks += [t for t in tags if t not in TAG_ORDER]           # any extra tags after
    return " ".join(toks)

def renderable(projects):
    """The projects to actually put on the page, in file order. Skips ones marked
    "hidden", and skips (with a friendly note) any whose write-up file isn't there yet —
    so a half-added project doesn't crash the whole build. Returns a list of (id, record)."""
    items = []
    for pid, proj in projects.items():
        if proj.get("hidden"):
            continue                                          # parked with "hidden": true
        if not os.path.exists(os.path.join(CV, "projects", pid + ".html")):
            print("  NOTE: %s has no write-up yet (cv/projects/%s.html missing) — skipped. "
                  "Add that file to put it on the page." % (pid, pid))
            continue
        items.append((pid, proj))
    return items


# --- the three pieces of the projects page -----------------------------------

def gen_grid(items):
    """Build the picture grid at the top (one square thumbnail tile per project that has one)."""
    out = []
    for pid, proj in items:
        if not proj.get("thumb"):
            continue  # this write-up simply has no grid picture
        thumb = proj["thumb"]
        thumb_path = os.path.join(THUMB_DIR, thumb)
        # If the record gives a full-size "hero_img", auto-make the square thumbnail from it.
        # Its optional "crop" picks WHICH square to keep (center by default; see gen_thumb.py).
        # We remake it when the thumbnail is missing, the hero is newer, or you pass --force-thumbs.
        hero = proj.get("hero_img")
        if hero:
            hero_path = os.path.join(SITE, hero)
            if not os.path.exists(hero_path):
                # Don't fail silently: a wrong path/spelling (e.g. .jpg vs .jpeg) is easy to make.
                print("  WARNING: %s hero_img not found — no thumbnail made: %s" % (pid, hero))
            else:
                stale = (not os.path.exists(thumb_path)
                         or os.path.getmtime(hero_path) > os.path.getmtime(thumb_path))
                if stale or FORCE_THUMBS:
                    crop = proj.get("crop", "center")
                    make_thumb(hero_path, thumb_path, THUMB_SIZE, crop=crop)
                    print("  generated thumbnail %s from %s (crop=%s)" % (thumb, hero, crop))
        # If the thumbnail image still isn't on disk, the grid would show a broken picture — say so.
        if not os.path.exists(thumb_path):
            print("  WARNING: %s has no thumbnail at assets/images/projects/thumbs/%s "
                  "— add a 'hero_img' to auto-make it, or put that file there." % (pid, thumb))
        # Stamp the image's real width/height so the browser reserves space for it up front.
        d = dims(thumb_path)
        wh = (' width="%d" height="%d"' % d) if d else ""
        title = "<strong>%s</strong>" % proj.get("gridTitle", "")
        role = ("<br>%s" % proj["role"]) if proj.get("role") else ""   # optional 2nd line
        out.append(
            '    <li class="%s">\n'
            '        <a href="#%s">\n'
            '            <img%s src="../assets/images/projects/thumbs/%s" />\n'
            '            <div><span>%s%s</span></div>\n'
            '        </a>\n'
            '    </li>' % (classes(proj), pid, wh, thumb, title, role))
    return "\n\n".join(out)

def gen_toc(items):
    """Build the year-by-year contents list. It's DERIVED, not hand-listed: take the projects in
    their file order, group them by year, newest year first. So there's nothing extra to keep
    in sync — reorder a record and the contents follow."""
    years = sorted({proj["year"] for _, proj in items}, key=lambda y: -int(y))  # newest first
    rows = []
    for year in years:
        entries = []
        for pid, proj in items:                          # keep each year's items in file order
            if proj["year"] != year:
                continue
            entries.append(
                '                    <div class="%s">\n'
                '                        <a href="#%s" title="%s">\n'
                '                            <li>%s</li>\n'
                '                        </a>\n'
                '                    </div>' % (classes(proj), pid, pid, proj.get("tocTitle", "")))
        rows.append(
            '        <tr>\n'
            '            <td class="table-title year">%s</td>\n'
            '            <td class="table-links">\n'
            '                <ul>\n%s\n                </ul>\n'
            '            </td>\n'
            '        </tr>' % (year, "\n\n".join(entries)))
    # The whole table is itself tagged with EVERY tag, so it never gets hidden by a filter.
    # "all" and "featured" are structural filter tags (no entry in TAG_ORDER) but still need to be here.
    wrap_cls = " ".join(["toc-table", "sortable-div", "all", "featured"] + TAG_ORDER)
    return ('<div class="%s">\n    <table>\n\n%s\n\n    </table>\n</div>'
            % (wrap_cls, "\n\n".join(rows)))

def gen_cards(items):
    """Build the full write-up cards, in file order. Each card = the wrapper (with the shared
    tags + id) around the hand-written body from cv/projects/<id>.html."""
    out = []
    for pid, proj in items:
        body_path = os.path.join(CV, "projects", pid + ".html")
        body = open(body_path, encoding="utf-8").read().rstrip("\n")
        body = reserve_img_space(correct_img_dims(body, CV))   # cards live in cv/, so ../assets resolves from CV
        out.append(
            '<div class="%s">\n'
            '    <div class="well" name="%s" id="%s">\n'
            '%s\n'
            '    </div>\n'
            '</div>' % (classes(proj), pid, pid, body))
    return "\n\n\n".join(out)

def gen_index_featured(data):
    """Build the homepage's "Featured projects" cards from the short teaser files
    (cv/projects/<id>.teaser.html), in the order listed in 'indexFeatured'. The homepage sits at
    the site root, so we swap the card bodies' `../assets/` paths for `assets/`; the
    `cv/#projects/x` "more info" links already work from the root and are left alone."""
    out = []
    for pid in data.get("indexFeatured", []):
        proj = data["projects"].get(pid, {"tags": [], "featured": False})
        teaser = os.path.join(CV, "projects", pid + ".teaser.html")
        if not os.path.exists(teaser):
            print("  WARNING: missing teaser %s.teaser.html — skipped" % pid)
            continue
        body = open(teaser, encoding="utf-8").read().rstrip("\n")
        body = correct_img_dims(body, CV)       # stamp real dims (paths are still ../assets here)
        body = reserve_img_space(body.replace("../assets/", "assets/"))   # then rebase + fix 290px
        # The homepage has no lazy-loader script (the CV page does). So if a teaser was copied from
        # a full card and still has the lazy ".yt-embed" placeholder, turn it into a plain YouTube
        # iframe that plays on its own here. (Teasers that already use a plain iframe are untouched.)
        body = re.sub(
            r'<div class="yt-embed" data-embed="([^"]+)"\s*></div>',
            r'<iframe loading="lazy" src="https://www.youtube.com/embed/\1?rel=0" frameborder="0" '
            r'allowfullscreen style="width: 100%; height: 100%;"></iframe>',
            body)
        out.append(
            '                <div class="%s">\n'
            '                    <div class="well" name="%s" id="%s">\n'
            '%s\n'
            '                    </div>\n'
            '                </div>' % (classes(proj), pid, pid, body))
    return "\n\n".join(out)


# --- putting it all together -------------------------------------------------

def main():
    check = "--check" in sys.argv          # --check = don't write, just say if it's stale
    if not check:
        ensure_outline_svg()               # self-heal the filter-tag outline after an Illustrator export
    data = dataio.load(os.path.join(CV, "data", "projects.json"))
    items = renderable(data["projects"])   # the projects to show, in file order (computed once)

    # Fill the three blanks in the page skeleton with the pieces we just built.
    template = open(os.path.join(CV, "projects.template.html"), encoding="utf-8").read()
    html = (template
            .replace("{{GRID}}", gen_grid(items))
            .replace("{{TOC}}", gen_toc(items))
            .replace("{{CARDS}}", gen_cards(items)))
    out_path = os.path.join(CV, "projects.html")
    current = open(out_path, encoding="utf-8").read() if os.path.exists(out_path) else ""

    # Also refill the homepage's "Featured projects" box (the bit between the FEATURED markers).
    INDEX = os.path.join(SITE, "index.html")
    idx = idx_new = None
    if os.path.exists(INDEX):
        idx = open(INDEX, encoding="utf-8").read()
        m = re.search(r'(<!-- FEATURED:START.*?-->)(.*?)(<!-- FEATURED:END -->)', idx, re.DOTALL)
        if m:
            featured = gen_index_featured(data)
            idx_new = idx[:m.start()] + m.group(1) + "\n\n" + featured + "\n\n                " + m.group(3) + idx[m.end():]

    if check:  # in --check mode we only report; we never write
        stale = (current != html) or (idx_new is not None and idx_new != idx)
        print("up to date" if not stale else "OUT OF DATE (run build_projects.py)")
        sys.exit(1 if stale else 0)

    # Write the finished pages.
    open(out_path, "w", encoding="utf-8").write(html)
    grid_n = sum(1 for _, proj in items if proj.get("thumb"))
    hidden = sum(1 for p in data["projects"].values() if p.get("hidden"))
    print("wrote cv/projects.html (%d grid tiles, %d cards%s; order follows projects.json, TOC by year)"
          % (grid_n, len(items), (" + %d hidden" % hidden) if hidden else ""))
    if idx_new is not None:
        open(INDEX, "w", encoding="utf-8").write(idx_new)
        print("wrote index.html featured section (%d teaser cards)" % len(data.get("indexFeatured", [])))

if __name__ == "__main__":
    main()
