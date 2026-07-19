#!/usr/bin/env python3
# =============================================================================
#  build_pubs.py  —  builds the "Pubs and Patents" page from your fact files.
#  Run this after adding a paper or a patent. You do NOT edit cv/paperspatents.html
#  by hand — this script writes it.
#
#  What it reads:
#    cv/data/publications.json   the facts: a list of papers, and a list of patents
#    cv/pubs/<id>.html           each paper's write-up (the card body)
#
#  What it writes:
#    cv/paperspatents.html       the finished page
#
#  The page has: one contents section per kind of publication (Blog / Journal /
#  Conference / Thesis / Book Chapters), each grouped by year; then a "Granted
#  Patents" list (just links — no write-ups); then the full paper write-ups.
#
#  How to run it:
#    python3 tools/build_pubs.py            # rebuild
#    python3 tools/build_pubs.py --check    # just check if it's up to date
#  (Or `python3 tools/build.py` to build this AND the projects page at once.)
# =============================================================================
import os, json, sys

CV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cv")
OUT = os.path.join(CV, "paperspatents.html")

# The publication sections, in the order they appear on the page. The left word is the
# "type" you put in publications.json; the right word is the heading shown on the page.
SECTIONS = [("blog", "Blog Posts"), ("journal", "Journal Publications"),
            ("conference", "Conference Publications"), ("thesis", "Thesis"),
            ("bookchapter", "Book Chapters")]
STYLE = 'style="margin-left:20px; margin-right: 20px;"'          # the indentation on each table
TROPHY = ' <i class="fa fa-trophy" aria-hidden="true"></i>'      # the 🏆 for award-winning papers

def year_key(y):
    """Sort key so years go newest-first (2025 before 2024...)."""
    try: return -int(y)
    except Exception: return 0

def toc_table(entries):
    """Build one contents table (used for each publication section): rows are years, each
    listing that year's papers. A paper with a card links to '#id'; a blog post (no card)
    links out to its url. Adds a 🏆 when award is set."""
    years = sorted({e["year"] for e in entries}, key=year_key)
    rows = []
    for y in years:
        lis = []
        for e in entries:
            if e["year"] != y:
                continue
            trophy = TROPHY if e.get("award") else ""
            if e.get("card"):                              # has a write-up -> in-page link
                a = '<a href="#%s" title="%s">%s%s</a>' % (e["id"], e["id"], e["tocTitle"], trophy)
            else:                                          # e.g. a blog post -> external link
                a = '<a target="_blank" href="%s">%s%s</a>' % (e.get("url", ""), e["tocTitle"], trophy)
            lis.append('        <li><span>%s</span></li>' % a)
        rows.append('    <tr>\n      <td class="table-title year">%s</td>\n'
                    '      <td class="table-links">\n        <ul>\n%s\n        </ul>\n'
                    '      </td>\n    </tr>' % (y, "\n".join(lis)))
    return '<div class="toc-table" %s>\n  <table>\n\n%s\n\n  </table>\n</div>' % (STYLE, "\n\n".join(rows))

def patents_table(patents):
    """Build the Granted Patents list (years -> patents). The freepatentsonline link and the
    '(US…)' number are built automatically from each patent's `number`, so you only type the
    number and title."""
    years = sorted({p["year"] for p in patents}, key=year_key)
    rows = []
    for y in years:
        lis = []
        for p in patents:
            if p["year"] != y:
                continue
            url = "https://www.freepatentsonline.com/%s.html" % p["number"]
            lis.append('          <li><span><a target="_blank" href="%s">\n'
                       '             %s (US%s)\n          </a></span></li>'
                       % (url, p["title"], p["number"]))
        rows.append('    <tr>\n      <td class="table-title year">%s</td>\n'
                    '      <td class="table-links">\n        <ul>\n%s\n        </ul>\n'
                    '      </td>\n    </tr>' % (y, "\n".join(lis)))
    return '<div class="toc-table" %s>\n  <table>\n\n%s\n\n  </table>\n</div>' % (STYLE, "\n\n".join(rows))

def cards(data):
    """Build the full paper write-ups (the cards down the page), in cardOrder. Each is an
    anchor + the hand-written body from cv/pubs/<id>.html."""
    out = []
    for cid in data["cardOrder"]:
        body = open(os.path.join(CV, "pubs", cid + ".html"), encoding="utf-8").read().rstrip("\n")
        out.append('<a name="%s" id="%s"></a>\n<div class="well">\n%s\n</div>' % (cid, cid, body))
    return "\n\n\n".join(out)

def render(data):
    """Stitch the whole page together: a contents section per kind, then patents, then cards."""
    parts = []
    for typ, heading in SECTIONS:
        ents = [e for e in data["entries"] if e["type"] == typ]
        if not ents:
            continue                                       # skip a section with nothing in it
        parts.append('<h2>%s<small> </small></h2>\n\n%s' % (heading, toc_table(ents)))
    parts.append('<h2>Granted Patents<small> </small></h2>\n\n%s' % patents_table(data["patents"]))
    parts.append('<h2>Publications<small> </small></h2>\n\n\n%s' % cards(data))
    return "\n\n\n\n".join(parts) + "\n"

def main():
    check = "--check" in sys.argv          # --check = don't write, just say if it's stale
    data = json.load(open(os.path.join(CV, "data", "publications.json"), encoding="utf-8"))
    html = render(data)
    current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if check:
        print("up to date" if current == html else "OUT OF DATE (run build_pubs.py)")
        sys.exit(0 if current == html else 1)
    open(OUT, "w", encoding="utf-8").write(html)
    print("wrote cv/paperspatents.html (%d TOC entries, %d patents, %d cards)"
          % (len(data["entries"]), len(data["patents"]), len(data["cardOrder"])))

if __name__ == "__main__":
    main()
