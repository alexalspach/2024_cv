#!/usr/bin/env python3
"""
One-time migration: extract the existing cv/projects.html into the data-driven sources the
generator (tools/build_projects.py) consumes:

  cv/data/projects.json    metadata: per-project {year, featured, tags, tocTitle},
                           the grid tile list, cardOrder, and tocOrder (year groups)
  cv/projects/<id>.html    each project card's body (verbatim inner HTML of its .well)
  cv/projects.template.html  the static scaffold with {{GRID}} {{TOC}} {{CARDS}} placeholders

Tags for each project are reconciled to the UNION of what the grid tile, TOC entry, and card
wrapper carried (fixing the drift bugs). Run:

    python3 tools/migrate_projects.py --dry     # report only, writes nothing
    python3 tools/migrate_projects.py           # writes the files above
"""
import os, re, sys, json

CV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cv")
SRC = os.path.join(CV, "projects.html")

# canonical tag order for neat, consistent class lists (mirrors the #tags filter bar)
TAG_ORDER = ["videos", "soft", "tactile", "manipulation", "hri", "humanoids", "wearable",
             "mobilerobots", "pathplanning", "navigation", "computervision", "designmfg",
             "hwdev", "swdev", "international", "korea", "drexel", "hubolab", "simlab",
             "disney", "tri", "thesis"]

def order_tags(tagset):
    known = [t for t in TAG_ORDER if t in tagset]
    extra = sorted(t for t in tagset if t not in TAG_ORDER and t not in ("all", "featured", "sortable-div"))
    return known + extra

# ---- comment-aware <div> matcher ----------------------------------------
_TAG = re.compile(r'<!--|<div\b|</div>')
def match_div_end(text, pos):
    """Given pos at a '<div', return index just past the matching '</div>' (comment-aware)."""
    depth = 0; i = pos; n = len(text)
    while i < n:
        m = _TAG.search(text, i)
        if not m:
            return n
        tok = m.group(0)
        if tok == '<!--':
            j = text.find('-->', m.end()); i = j + 3 if j != -1 else n
        elif tok == '</div>':
            depth -= 1; i = m.end()
            if depth == 0:
                return i
        else:
            depth += 1; i = m.end()
    return n

def strip_comments(s):
    return re.sub(r'<!--.*?-->', '', s, flags=re.DOTALL)

# ---- region splitting ----------------------------------------------------
def split_regions(s):
    gm = re.search(r'<ul id="da-thumbs"[^>]*>(.*?)</ul>', s, re.DOTALL)
    tm = re.search(r'<div class="toc-table[^>]*>.*?</table>\s*</div>', s, re.DOTALL)
    after_toc = tm.end()
    sm = re.search(r'<script', s[after_toc:])
    cards_end = after_toc + sm.start()
    return {
        "preamble": s[:gm.start()],
        "grid_open": s[gm.start():gm.start() + s[gm.start():].index('>') + 1],
        "grid_inner": gm.group(1),
        "mid": s[gm.end():tm.start()],
        "toc": tm.group(0),
        "cards": s[after_toc:cards_end],
        "postamble": s[cards_end:],
    }

# ---- parsers -------------------------------------------------------------
def parse_grid(grid_inner):
    tiles = []
    for li in re.findall(r'<li\b[^>]*>.*?</li>', strip_comments(grid_inner), re.DOTALL):
        cls = re.search(r'class="([^"]*)"', li)
        href = re.search(r'href="#([^"]+)"', li)
        img = re.search(r'src="[^"]*thumbs/([^"]+)"', li)
        strong = re.search(r'<strong>(.*?)</strong>', li, re.DOTALL)
        role = re.search(r'</strong>\s*<br>\s*(.*?)</span>', li, re.DOTALL)
        if not (href and img):
            continue
        tags = set(cls.group(1).split()) if cls else set()
        tags.discard("sortable-div")
        tiles.append({
            "target": href.group(1),
            "thumb": img.group(1),
            "title": (strong.group(1).strip() if strong else ""),
            "role": (role.group(1).strip() if role else ""),
            "_tags": tags,
            "_featured": "featured" in tags,
        })
    return tiles

def parse_toc(toc):
    groups = []
    per_id = {}
    for tr in re.findall(r'<tr\b.*?</tr>', toc, re.DOTALL):
        ym = re.search(r'table-title year">\s*([^<\s]+)', tr)
        if not ym:
            continue
        year = ym.group(1)
        ids = []
        for m in re.finditer(r'<div class="([^"]*)">\s*<a href="#([^"]+)"[^>]*>\s*<li>(.*?)</li>', tr, re.DOTALL):
            tags = set(m.group(1).split()); tags.discard("sortable-div")
            pid = m.group(2)
            ids.append(pid)
            per_id[pid] = {"tocTitle": re.sub(r'\s+', ' ', m.group(3)).strip(),
                           "year": year, "_tags": tags, "_featured": "featured" in tags}
        groups.append({"year": year, "ids": ids})
    return groups, per_id

def parse_cards(cards_region):
    out = []
    i, n = 0, len(cards_region)
    while i < n:
        if cards_region.startswith('<!--', i):
            j = cards_region.find('-->', i); i = j + 3 if j != -1 else n; continue
        m = re.match(r'<div class="sortable-div ([^"]*)">', cards_region[i:])
        if m:
            end = match_div_end(cards_region, i)
            block = cards_region[i:end]
            wm = re.search(r'<div class="well" name="([^"]*)" id="([^"]*)">', block)
            if wm:
                wid = wm.group(2)
                tags = set(m.group(1).split()); tags.discard("sortable-div")
                well_abs = i + wm.start()
                well_body_start = i + wm.end()
                well_end = match_div_end(cards_region, well_abs)
                body = cards_region[well_body_start:well_end - len('</div>')]
                out.append({"id": wid, "_tags": tags, "_featured": "featured" in tags, "body": body})
            i = end; continue
        i += 1
    return out

# ---- main ----------------------------------------------------------------
def main():
    dry = "--dry" in sys.argv
    s = open(SRC, encoding="utf-8").read()
    R = split_regions(s)
    tiles = parse_grid(R["grid_inner"])
    toc_groups, toc_ids = parse_toc(R["toc"])
    cards = parse_cards(R["cards"])

    card_ids = [c["id"] for c in cards]
    grid_targets = [t["target"] for t in tiles]

    # reconcile tags per project id (union of card + toc + grid tile that target it)
    projects = {}
    for c in cards:
        projects[c["id"]] = {"tags": set(c["_tags"]), "featured": c["_featured"]}
    for pid, meta in toc_ids.items():
        p = projects.setdefault(pid, {"tags": set(), "featured": False})
        p["tags"] |= meta["_tags"]; p["featured"] = p["featured"] or meta["_featured"]
        p["year"] = meta["year"]; p["tocTitle"] = meta["tocTitle"]
    for t in tiles:
        p = projects.get(t["target"])
        if p:
            p["tags"] |= t["_tags"]; p["featured"] = p["featured"] or t["_featured"]

    # finalize project records (cards only; the TOC is derived from cardOrder + year at build
    # time, so a TOC-only entry with no card is dropped — such links are broken anyway)
    proj_out = {}
    for pid in card_ids:
        p = projects.get(pid, {"tags": set(), "featured": False})
        proj_out[pid] = {
            "year": p.get("year"),
            "featured": bool(p.get("featured")),
            "tags": order_tags(p["tags"]),
            "tocTitle": p.get("tocTitle", ""),
        }

    # grid tiles: tags derived from target project (fallback to own if alias w/o project)
    grid_out = []
    for t in tiles:
        grid_out.append({"target": t["target"], "thumb": t["thumb"],
                         "title": t["title"], "role": t["role"]})

    # ---- report ----
    print("grid tiles:      %d" % len(tiles))
    print("toc entries:     %d across %d years" % (sum(len(g["ids"]) for g in toc_groups), len(toc_groups)))
    print("cards:           %d" % len(cards))
    missing_card = [t["target"] for t in tiles if t["target"] not in card_ids]
    print("grid tiles whose target has NO card (aliases):", missing_card)
    toc_no_card = [i for g in toc_groups for i in g["ids"] if i not in card_ids]
    print("toc entries with NO card:", toc_no_card)
    card_no_toc = [c for c in card_ids if c not in toc_ids]
    print("cards with NO toc entry:", card_no_toc)
    dup = [x for x in card_ids if card_ids.count(x) > 1]
    print("duplicate card ids:", sorted(set(dup)))

    if dry:
        print("\n[dry run] no files written.")
        return

    # ---- write files ----
    os.makedirs(os.path.join(CV, "data"), exist_ok=True)
    os.makedirs(os.path.join(CV, "projects"), exist_ok=True)
    for c in cards:
        with open(os.path.join(CV, "projects", c["id"] + ".html"), "w", encoding="utf-8") as f:
            f.write(c["body"].strip("\n") + "\n")
    data = {
        "projects": proj_out,
        "grid": grid_out,
        "cardOrder": card_ids,
    }
    with open(os.path.join(CV, "data", "projects.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    template = (R["preamble"] + R["grid_open"] + "\n{{GRID}}\n  </ul>" +
                R["mid"] + "{{TOC}}" + "\n\n\n{{CARDS}}\n\n" + R["postamble"])
    with open(os.path.join(CV, "projects.template.html"), "w", encoding="utf-8") as f:
        f.write(template)
    print("\nwrote cv/data/projects.json, cv/projects.template.html, and %d body files." % len(cards))

if __name__ == "__main__":
    main()
