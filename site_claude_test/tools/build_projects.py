#!/usr/bin/env python3
# =============================================================================
#  build_projects.py  —  builds the "Robots, etc." page (and the homepage's
#  Featured box) from your fact files. You run this after editing a project.
#
#  In plain terms: you fill in small files, this script stamps them into the big
#  web page for you, so the picture grid, the contents list, and the full write-up
#  always match. You do NOT edit cv/projects.html by hand — this script writes it.
#
#  What it reads:
#    cv/data/projects.json      the facts (year, tags, titles, order, homepage list)
#    cv/projects/<id>.html      each project's write-up (the card body)
#    cv/projects.template.html  the page skeleton with {{GRID}} {{TOC}} {{CARDS}} blanks
#
#  What it writes:
#    cv/projects.html           the finished page
#    index.html                 just the "Featured projects" box on the homepage
#    ...and a square thumbnail   auto-cropped from each project's hero_img
#
#  How to run it:
#    python3 tools/build_projects.py            # rebuild
#    python3 tools/build_projects.py --check    # just check if it's up to date
#
#  (Tip: `python3 tools/build.py` runs this AND the papers/patents build together.)
# =============================================================================
import json, os, re, sys, subprocess

# Let this script import its sibling helper (the thumbnail maker) from the same folder.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_thumb import make_thumb

# Handy folder locations (worked out from where this file lives).
CV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cv")
SITE = os.path.join(CV, "..")                                        # the site root
THUMB_DIR = os.path.join(CV, "..", "assets", "images", "projects", "thumbs")
THUMB_SIZE = 400  # thumbnails are made 400x400; shown ~165px, so they're sharp on retina

# The filter buttons, in the order they appear. We list tags in this order so every
# generated tag list reads the same way (purely cosmetic — order doesn't affect filtering).
TAG_ORDER = ["videos", "soft", "tactile", "manipulation", "hri", "humanoids", "wearable",
             "mobilerobots", "pathplanning", "navigation", "computervision", "designmfg",
             "hwdev", "swdev", "international", "korea", "drexel", "hubolab", "simlab",
             "disney", "tri", "thesis"]


# --- small helpers -----------------------------------------------------------

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

def esc(s):
    """Escape the handful of characters that are special in HTML."""
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def classes(proj):
    """Build the CSS class list for a project (this is what the filter buttons match on).
    Tags come from ONE place — the project's record — so the grid tile, the contents row,
    and the card all get the exact same tags. That's what stops them drifting apart."""
    toks = ["sortable-div"]
    if proj.get("featured"):
        toks.append("featured")
    toks.append("all")                                        # every item is in "all"
    toks += [t for t in TAG_ORDER if t in proj.get("tags", [])]        # known tags, in order
    toks += [t for t in proj.get("tags", []) if t not in TAG_ORDER]    # any extra tags after
    return " ".join(toks)


# --- the three pieces of the projects page -----------------------------------

def gen_grid(data):
    """Build the picture grid at the top (one square thumbnail tile per entry)."""
    out = []
    for tile in data["grid"]:
        proj = data["projects"].get(tile["target"], {"tags": [], "featured": False})
        if proj.get("hidden"):
            continue  # a project switched off with "hidden": true is shown nowhere
        cls = classes(proj)
        thumb = tile["thumb"]
        thumb_path = os.path.join(THUMB_DIR, thumb)
        # If the tile points at a full-size "hero_img", auto-make the square thumbnail from it
        # (only when the thumbnail is missing or the hero is newer). No Photoshop needed.
        hero = tile.get("hero_img")
        if hero:
            hero_path = os.path.join(SITE, hero)
            if os.path.exists(hero_path) and (
                    not os.path.exists(thumb_path)
                    or os.path.getmtime(hero_path) > os.path.getmtime(thumb_path)):
                make_thumb(hero_path, thumb_path, THUMB_SIZE)
                print("  generated thumbnail %s from %s" % (thumb, hero))
        # Stamp the image's real width/height so the browser reserves space for it up front.
        d = dims(thumb_path)
        wh = (' width="%d" height="%d"' % d) if d else ""
        title = "<strong>%s</strong>" % tile.get("title", "")
        role = ("<br>%s" % tile["role"]) if tile.get("role") else ""   # optional 2nd line
        out.append(
            '    <li class="%s">\n'
            '        <a href="#%s">\n'
            '            <img%s src="../assets/images/projects/thumbs/%s" />\n'
            '            <div><span>%s%s</span></div>\n'
            '        </a>\n'
            '    </li>' % (cls, tile["target"], wh, thumb, title, role))
    return "\n\n".join(out)

def gen_toc(data):
    """Build the year-by-year contents list. It's DERIVED, not hand-listed: take the cards in
    their order, group them by their year, newest year first. So there's nothing extra to keep
    in sync — reorder a card and the contents follow."""
    projects = data["projects"]
    order = [pid for pid in data["cardOrder"] if not projects[pid].get("hidden")]
    years = sorted({projects[pid]["year"] for pid in order}, key=lambda y: -int(y))  # newest first
    rows = []
    for year in years:
        entries = []
        for pid in order:                                # keep each year's items in card order
            if projects[pid]["year"] != year:
                continue
            proj = projects[pid]
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
    wrap_cls = " ".join(["toc-table", "sortable-div", "all"] + TAG_ORDER)
    return ('<div class="%s">\n    <table>\n\n%s\n\n    </table>\n</div>'
            % (wrap_cls, "\n\n".join(rows)))

def gen_cards(data):
    """Build the full write-up cards, in card order. Each card = the wrapper (with the shared
    tags + id) around the hand-written body from cv/projects/<id>.html."""
    out = []
    for pid in data["cardOrder"]:
        proj = data["projects"][pid]
        if proj.get("hidden"):
            continue  # kept in the data (in place), just not shown
        body_path = os.path.join(CV, "projects", pid + ".html")
        body = open(body_path, encoding="utf-8").read().rstrip("\n")
        out.append(
            '<div class="%s">\n'
            '    <div class="well" name="%s" id="%s">\n'
            '%s\n'
            '    </div>\n'
            '</div>' % (classes(proj), pid, pid, body))
    return "\n\n\n".join(out)

def gen_index_featured(data):
    """Build the homepage's "Featured projects" cards from the short teaser files
    (cv/projects/<id>.teaser.html). The homepage sits at the site root, so we swap the card
    bodies' `../assets/` paths for `assets/`; the `cv/#projects/x` "more info" links already
    work from the root and are left alone."""
    out = []
    for pid in data.get("indexFeatured", []):
        proj = data["projects"].get(pid, {"tags": [], "featured": False})
        teaser = os.path.join(CV, "projects", pid + ".teaser.html")
        if not os.path.exists(teaser):
            print("  WARNING: missing teaser %s.teaser.html — skipped" % pid)
            continue
        body = open(teaser, encoding="utf-8").read().rstrip("\n").replace("../assets/", "assets/")
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
    data = json.load(open(os.path.join(CV, "data", "projects.json"), encoding="utf-8"))

    # Fill the three blanks in the page skeleton with the pieces we just built.
    template = open(os.path.join(CV, "projects.template.html"), encoding="utf-8").read()
    html = (template
            .replace("{{GRID}}", gen_grid(data))
            .replace("{{TOC}}", gen_toc(data))
            .replace("{{CARDS}}", gen_cards(data)))
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
    shown = sum(1 for pid in data["cardOrder"] if not data["projects"][pid].get("hidden"))
    hidden = len(data["cardOrder"]) - shown
    print("wrote cv/projects.html (%d grid tiles, %d cards%s; TOC derived from card order)" % (
        len(data["grid"]), shown, (" + %d hidden" % hidden) if hidden else ""))
    if idx_new is not None:
        open(INDEX, "w", encoding="utf-8").write(idx_new)
        print("wrote index.html featured section (%d teaser cards)" % len(data.get("indexFeatured", [])))

if __name__ == "__main__":
    main()
