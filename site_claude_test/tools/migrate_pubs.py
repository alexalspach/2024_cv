#!/usr/bin/env python3
"""
One-time migration: extract cv/paperspatents.html into data-driven sources for the pubs/patents
generator (tools/build_pubs.py):

  cv/data/publications.json   { entries[], cardOrder[], patents[] }
      entries: one per TOC line -> {type, year, id|url, tocTitle, award, card}
      patents: {year, number, title}   (url derived from number)
  cv/pubs/<id>.html           each publication's detail-card body (verbatim inner of its .well)

Publication cards are anchored by <a name="ID" id="ID"></a> before a <div class="well">.
Run:  python3 tools/migrate_pubs.py [--dry]
"""
import os, re, sys, json

CV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cv")
SRC = os.path.join(CV, "paperspatents.html")

SECTIONS = [("blog", "Blog Posts"), ("journal", "Journal Publications"),
            ("conference", "Conference Publications"), ("thesis", "Thesis"),
            ("bookchapter", "Book Chapters")]

_TAG = re.compile(r'<!--|<div\b|</div>')
def match_div_end(text, pos):
    depth, i, n = 0, pos, len(text)
    while i < n:
        m = _TAG.search(text, i)
        if not m: return n
        t = m.group(0)
        if t == '<!--':
            j = text.find('-->', m.end()); i = j + 3 if j != -1 else n
        elif t == '</div>':
            depth -= 1; i = m.end()
            if depth == 0: return i
        else:
            depth += 1; i = m.end()
    return n

def clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()

def in_comment(s, pos):
    return s.rfind('<!--', 0, pos) > s.rfind('-->', 0, pos)

def find_live(pattern, s):
    """First match of pattern that is NOT inside an HTML comment."""
    for m in re.finditer(pattern, s):
        if not in_comment(s, m.start()):
            return m
    return None

def first_toc_after(s, pos):
    """Return (start,end) of the first live .toc-table after pos (skipping commented ones)."""
    i = pos
    while True:
        m = re.compile(r'<div class="toc-table"[^>]*>').search(s, i)
        if not m: return None
        # is it inside a comment that opened before it?
        prev_open = s.rfind('<!--', 0, m.start())
        prev_close = s.rfind('-->', 0, m.start())
        if prev_open > prev_close:   # inside a comment -> skip past comment
            i = s.find('-->', m.start()); i = i + 3 if i != -1 else len(s); continue
        return (m.start(), match_div_end(s, m.start()))

def parse_toc_rows(block, section_type):
    entries = []
    for tr in re.findall(r'<tr\b.*?</tr>', block, re.DOTALL):
        ym = re.search(r'table-title year">\s*([^<\s]+)', tr)
        if not ym: continue
        year = ym.group(1)
        for li in re.findall(r'<li>.*?</li>', tr, re.DOTALL):
            a = re.search(r'<a\b([^>]*)>(.*?)</a>', li, re.DOTALL)
            if not a: continue
            attrs, inner = a.group(1), a.group(2)
            href = re.search(r'href="([^"]*)"', attrs)
            href = href.group(1) if href else ""
            award = 'fa-trophy' in li
            title = clean(inner)
            e = {"type": section_type, "year": year, "tocTitle": title, "award": award}
            if href.startswith('#'):
                e["id"] = href[1:]; e["card"] = True
            else:
                e["url"] = href; e["card"] = False
            entries.append(e)
    return entries

def main():
    dry = "--dry" in sys.argv
    s = open(SRC, encoding="utf-8").read()

    # --- TOC entries per section ---
    entries = []
    for typ, heading in SECTIONS:
        h = find_live(r'<h2>\s*' + re.escape(heading), s)
        if not h:
            print("  (section not found: %s)" % heading); continue
        span = first_toc_after(s, h.end())
        if not span:
            continue
        entries += parse_toc_rows(s[span[0]:span[1]], typ)

    # --- patents ---
    patents = []
    hp = find_live(r'<h2>\s*Granted Patents', s)
    span = first_toc_after(s, hp.end()) if hp else None
    if span:
        for tr in re.findall(r'<tr\b.*?</tr>', s[span[0]:span[1]], re.DOTALL):
            ym = re.search(r'table-title year">\s*([^<\s]+)', tr)
            if not ym: continue
            year = ym.group(1)
            for a in re.finditer(r'<a\b[^>]*href="([^"]*freepatentsonline[^"]*)"[^>]*>(.*?)</a>', tr, re.DOTALL):
                url, text = a.group(1), clean(a.group(2))
                num = re.search(r'/(\d+)\.html', url)
                number = num.group(1) if num else ""
                title = re.sub(r'\s*\(US\s*' + re.escape(number) + r'\)\s*$', '', text).strip()
                patents.append({"year": year, "number": number, "title": title})

    # --- cards (a name/id + following .well) ---
    card_order = []
    for m in re.finditer(r'<a name="([^"]+)" id="\1">\s*</a>\s*(<div class="well">)', s):
        cid = m.group(1)
        well_start = m.start(2)
        body = s[m.end(2): match_div_end(s, well_start) - len('</div>')]
        card_order.append(cid)
        if not dry:
            os.makedirs(os.path.join(CV, "pubs"), exist_ok=True)
            open(os.path.join(CV, "pubs", cid + ".html"), "w", encoding="utf-8").write(body.strip("\n") + "\n")

    # --- report ---
    toc_ids = [e["id"] for e in entries if e.get("id")]
    print("TOC entries: %d (blog/journal/conf/thesis/chapter)" % len(entries))
    for typ, _ in SECTIONS:
        print("   %-12s %d" % (typ, sum(1 for e in entries if e["type"] == typ)))
    print("patents: %d" % len(patents))
    print("cards: %d" % len(card_order))
    print("TOC ids without a card:", sorted(set(i for i in toc_ids if i not in card_order)))
    print("cards without a TOC entry:", sorted(set(c for c in card_order if c not in toc_ids)))
    dups = sorted(set(i for i in toc_ids if toc_ids.count(i) > 1))
    print("ids appearing in >1 TOC entry:", dups)

    if dry:
        print("\n[dry run] no files written."); return

    data = {"entries": entries, "cardOrder": card_order, "patents": patents}
    os.makedirs(os.path.join(CV, "data"), exist_ok=True)
    json.dump(data, open(os.path.join(CV, "data", "publications.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("\nwrote cv/data/publications.json and %d card bodies to cv/pubs/" % len(card_order))

if __name__ == "__main__":
    main()
