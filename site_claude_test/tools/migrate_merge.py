#!/usr/bin/env python3
# One-time migration: fold the separate "grid" tiles into each project record,
# drop "target"/"cardOrder", and move "indexFeatured" to the top. Reads the old
# projects.json and writes the new merged layout to the path given as argv[1].
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataio

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "cv", "data", "projects.json")

README = ("HOW TO USE: to add a project, add ONE record to 'projects' below (copy an existing one) "
          "and write its story in cv/projects/<id>.html, then run 'python3 tools/build.py'. "
          "Everything for a project lives in its record: year, tags, featured, tocTitle (the contents-list "
          "title), and -- if it should appear in the top picture grid -- a square 'thumb' image with "
          "'gridTitle'/'role', or a full-size 'hero_img' (+ optional 'crop') to auto-make the square "
          "(rebuild with 'python3 tools/build.py --force-thumbs' after changing a crop). The page order "
          "follows the order of records here (newest first); the contents list groups them by year. Omit "
          "the thumb fields for a write-up with no grid picture. Add \"hidden\": true to park a project "
          "without deleting it. 'indexFeatured' (top of file) lists the projects that also appear on the "
          "homepage. Do NOT edit cv/projects.html by hand -- it is generated. Full guide: AUTHORING.md.")

TAGS_COMMENT = ("// tags (use the friendly name OR the code in parentheses): featured, all, videos, soft, "
                "tactile, manipulation, hri, humanoids, wearable, mobile robots (mobilerobots), "
                "path planning (pathplanning), navigation, vision (computervision), design/mfg (designmfg), "
                "h/w dev (hwdev), s/w dev (swdev), international, korea, drexel, hubolab, simlab, disney, "
                "toyota (tri)")


def reindent(block, spaces):
    """Indent every line of a json.dumps block except the first by `spaces` spaces."""
    lines = block.split("\n")
    pad = " " * spaces
    return "\n".join([lines[0]] + [pad + ln for ln in lines[1:]])


def main():
    out_path = sys.argv[1]
    data = dataio.load(SRC)

    # Map each project id -> its FIRST grid tile. (For DesignOpt1 the first tile is the
    # "Tetrabot" one, which is exactly the tile we're keeping; the later duplicate is dropped.)
    tile_for = {}
    for tile in data["grid"]:
        tile_for.setdefault(tile["target"], tile)

    merged = {}
    for pid, proj in data["projects"].items():
        rec = {}
        rec["year"] = proj["year"]
        rec["featured"] = proj.get("featured", False)
        rec["tags"] = proj["tags"]
        rec["tocTitle"] = proj.get("tocTitle", "")
        tile = tile_for.get(pid)
        if tile:                                        # this project shows a grid thumbnail
            rec["thumb"] = tile["thumb"]
            rec["gridTitle"] = tile.get("title", "")
            rec["role"] = tile.get("role", "")
            if tile.get("hero_img"):
                rec["hero_img"] = tile["hero_img"]
            if tile.get("crop"):
                rec["crop"] = tile["crop"]
        if proj.get("hidden"):
            rec["hidden"] = True
        merged[pid] = rec

    # Sanity: every grid target must be a real project (catches typos like the old Tetrabot bug).
    for t in tile_for:
        if t not in data["projects"]:
            print("  WARNING: grid tile target %r has no project record" % t)

    projects_block = reindent(json.dumps(merged, indent=2, ensure_ascii=False), 2)
    featured_block = reindent(json.dumps(data["indexFeatured"], indent=2, ensure_ascii=False), 2)

    text = ("{\n"
            '  "_README": %s,\n\n' % json.dumps(README, ensure_ascii=False)
            + "  " + TAGS_COMMENT + "\n\n"
            + '  "indexFeatured": ' + featured_block + ",\n\n"
            + '  "projects": ' + projects_block + "\n"
            + "}\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    thumbs = sum(1 for r in merged.values() if r.get("thumb"))
    print("wrote %s: %d projects (%d with a grid thumbnail), %d homepage picks"
          % (out_path, len(merged), thumbs, len(data["indexFeatured"])))


if __name__ == "__main__":
    main()
