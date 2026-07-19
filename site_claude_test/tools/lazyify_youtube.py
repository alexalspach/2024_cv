#!/usr/bin/env python3
"""
Convert live YouTube <iframe> embeds into lazy placeholders handled by lazy_media.js.

    <iframe ... src="https://www.youtube.com/embed/VIDEOID?..." ...></iframe>
        ->
    <div class="yt-embed" data-embed="VIDEOID"></div>

The placeholder fills the same parent box (.media-youtube-fullwidth / -halfwidth) and shows
the thumbnail + play glyph via CSS, so there is no visual change; lazy_media.js mounts the
real iframe when it settles in view (bounded to a max concurrency). Skips <iframe>s inside
HTML comments. Idempotent (no iframes remain after a run).

Usage:  python3 tools/lazyify_youtube.py [--check]
"""
import os, re, sys

CV_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cv")
FILES = ["projects.html", "experience.html"]

IFRAME_RE = re.compile(r"<iframe\b[^>]*>\s*</iframe>", re.IGNORECASE | re.DOTALL)
SRC_RE = re.compile(r'src\s*=\s*"([^"]*)"', re.IGNORECASE)
EMBED_ID_RE = re.compile(r"youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]+)", re.IGNORECASE)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def convert_segment(text, report):
    def repl(m):
        tag = m.group(0)
        src = SRC_RE.search(tag)
        if not src:
            return tag
        mid = EMBED_ID_RE.search(src.group(1))
        if not mid:
            return tag  # not a youtube embed; leave untouched
        report["converted"] += 1
        return '<div class="yt-embed" data-embed="%s"></div>' % mid.group(1)
    return IFRAME_RE.sub(repl, text)


def process(text, report):
    out, pos = [], 0
    for c in COMMENT_RE.finditer(text):
        out.append(convert_segment(text[pos:c.start()], report))
        out.append(c.group(0))  # leave commented markup alone
        pos = c.end()
    out.append(convert_segment(text[pos:], report))
    return "".join(out)


def main():
    check = "--check" in sys.argv
    total = 0
    for fn in FILES:
        p = os.path.join(CV_DIR, fn)
        if not os.path.exists(p):
            continue
        text = open(p, encoding="utf-8").read()
        report = {"converted": 0}
        new = process(text, report)
        total += report["converted"]
        print("%-20s %s %d youtube iframe(s)" %
              (fn, "would convert" if check else "converted", report["converted"]))
        if not check and new != text:
            open(p, "w", encoding="utf-8").write(new)
    if check and total:
        sys.exit(1)


if __name__ == "__main__":
    main()
