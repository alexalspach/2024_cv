#!/usr/bin/env python3
"""
End-to-end test harness for the CV site. Drives real Chrome headlessly against a fresh,
no-cache local server so results are deterministic. It gates on JS errors and broken
assets, and asserts the behaviors fixed in Pass 1.

Run:
    tests/.venv/bin/python tests/test_cv.py
    tests/.venv/bin/python tests/test_cv.py --headed   # watch it run

Setup (once):
    python3 -m venv tests/.venv
    tests/.venv/bin/pip install playwright
    # Uses the system Google Chrome (channel="chrome"); no browser download needed.

Exit code 0 = all passed, 1 = one or more failures (details printed).
"""
import functools, http.server, os, socketserver, sys, threading

from playwright.sync_api import sync_playwright

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADED = "--headed" in sys.argv

# ---- results -------------------------------------------------------------
_results = []
def check(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  -> " + str(detail)) if detail else ""))
    return ok

# ---- no-cache static server (in-process) ---------------------------------
class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
    def log_message(self, *a):
        pass

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", 0),
        functools.partial(Handler, directory=SITE_ROOT))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]

# ---- helpers -------------------------------------------------------------
def wait_for_top(pg, anchor_id, target=20, tol=3, timeout_ms=7000):
    """Poll until the anchor settles at ~target px from the top (its correction loop is async)."""
    waited, top = 0, None
    while waited < timeout_ms:
        top = pg.evaluate("(id)=>{const e=document.getElementById(id);return e?Math.round(e.getBoundingClientRect().top):99999;}", anchor_id)
        if abs(top - target) <= tol:
            return top
        pg.wait_for_timeout(200); waited += 200
    return top

def new_page(browser, base):
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    errs, bad = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("response", lambda r: bad.append("%d %s" % (r.status, r.url)) if r.status >= 400 else None)
    pg.base, pg.errs, pg.bad = base, errs, bad
    return pg

def main():
    httpd, port = start_server()
    base = "http://127.0.0.1:%d" % port
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=not HEADED)

        # === 1. Core load: no JS errors, no broken assets, jQuery sane ===
        print("\n[1] Core load / assets / jQuery")
        pg = new_page(browser, base)
        pg.goto(base + "/cv/", wait_until="load")
        pg.wait_for_timeout(1500)
        jq = pg.evaluate("() => ({v: window.jQuery && jQuery.fn.jquery, "
                         "ga: [...document.scripts].some(s=>/googleapis/.test(s.src)), "
                         "tab: typeof jQuery.fn.tab, hoverdir: typeof jQuery.fn.hoverdir})")
        check("jQuery pinned to 1.12.4", jq["v"] == "1.12.4", jq["v"])
        check("no stray googleapis jQuery", jq["ga"] is False)
        check("Bootstrap .tab plugin present", jq["tab"] == "function")
        check("hoverdir plugin present", jq["hoverdir"] == "function")
        check("no broken assets (>=400) on projects tab", not pg.bad, pg.bad[:5])

        # === 2. highlight() no longer throws on thumbnail click ===
        print("\n[2] highlight() cleanup")
        pg.evaluate("() => { const a=document.querySelector('#da-thumbs a[href^=\"#\"]'); a && a.click(); }")
        pg.wait_for_timeout(300)
        check("clicking a thumbnail throws no JS error", not pg.errs, pg.errs[:3])

        # === 3. Tag filtering parity across grid / TOC / cards ===
        print("\n[3] Tag filtering")
        pg.evaluate("() => sortAll()")
        pg.wait_for_timeout(200)
        total = pg.evaluate("() => document.querySelectorAll('div.sortable-div:not(.hidden)').length")
        pg.evaluate("() => tagSorting('soft')")
        pg.wait_for_timeout(300)
        parity = pg.evaluate("""() => {
          const vis=[...document.querySelectorAll('.sortable-div:not(.hidden)')];
          const bad=vis.filter(e=>!e.classList.contains('soft')).length;
          return {visible:vis.length, nonSoftVisible:bad};
        }""")
        check("'soft' filter hides non-matching (parity)", parity["nonSoftVisible"] == 0, parity)
        check("'soft' filter actually narrows the set", 0 < parity["visible"] < total, parity)
        pg.evaluate("() => sortAll()")

        # TOC keeps its table structure/formatting (regression guard for the generator)
        toc = pg.evaluate("""() => {
          const d=document.querySelector('.toc-table');
          if(!d) return {missing:true};
          return {hasTable: !!d.querySelector('table'),
                  years: d.querySelectorAll('td.table-title.year').length,
                  yearRendered: d.querySelector('td.year') ? Math.round(d.querySelector('td.year').getBoundingClientRect().width) : 0};
        }""")
        check("TOC has its .toc-table > table structure", toc.get("hasTable") is True and toc.get("years", 0) >= 10, toc)

        # === 4. Anchor scrolling lands at the header offset (cold path) ===
        print("\n[4] Anchor scrolling (cold, several depths)")
        for t in ["Punyo2", "SoftBubbleGrip1", "SnapBot1", "MiniHuboMfg"]:
            ap = new_page(browser, base)
            ap.goto(base + "/cv/", wait_until="load")
            ap.wait_for_timeout(500)  # cold: images not preloaded
            ap.evaluate("(id) => { const a=document.querySelector('a[href=\"#'+id+'\"]'); a && a.click(); }", t)
            top = wait_for_top(ap, t)
            check("anchor '%s' lands ~20px from top" % t, abs(top - 20) <= 3, "top=%s" % top)
            ap.close()

        # In-page clicks are SMOOTH (animated), not an instant jump
        sp = new_page(browser, base)
        sp.goto(base + "/cv/", wait_until="load")
        sp.wait_for_timeout(700)
        sp.evaluate("() => { const a=document.querySelector('a[href=\"#MiniHuboMfg\"]'); a && a.click(); }")
        seen = set()
        for _ in range(12):
            sp.wait_for_timeout(50); seen.add(sp.evaluate("() => Math.round(scrollY)"))
        check("in-page click scrolls smoothly (animated, not a jump)", len(seen) > 5, "distinct positions=%d" % len(seen))
        sp.close()

        # Correction yields to the user: a scroll during the glide is NOT overridden back to the target
        yp = new_page(browser, base)
        yp.goto(base + "/cv/", wait_until="load")
        yp.wait_for_timeout(700)
        yp.evaluate("() => { const a=document.querySelector('a[href=\"#MiniHuboMfg\"]'); a && a.click(); }")
        yp.wait_for_timeout(120)
        yp.evaluate("() => window.dispatchEvent(new WheelEvent('wheel', {deltaY:-400, bubbles:true}))")  # user intent
        yp.evaluate("() => scrollBy(0, -400)")  # actually move
        yp.wait_for_timeout(1800)
        ytop = yp.evaluate("() => Math.round(document.getElementById('MiniHuboMfg').getBoundingClientRect().top)")
        check("user scroll during glide is not overridden to the target", abs(ytop - 20) > 5, "top=%s" % ytop)
        yp.close()

        # === 5. Deep-link on fresh navigation ===
        print("\n[5] Deep-link")
        dp = new_page(browser, base)
        dp.goto(base + "/cv/#projects/Punyo2", wait_until="load")
        top = wait_for_top(dp, "Punyo2")
        hsh = dp.evaluate("() => location.hash")
        check("deep-link /cv/#projects/Punyo2 scrolls to card", abs(top - 20) <= 3, "top=%s" % top)
        check("deep-link left the hash intact", hsh == "#projects/Punyo2", hsh)
        dp.close()

        # === 6. Bounded YouTube lazy-loading (mobile-Safari crash guard) ===
        print("\n[6] Bounded YouTube lazy-loading")
        lp = new_page(browser, base)
        lp.goto(base + "/cv/", wait_until="load")
        lp.wait_for_timeout(1000)
        ph = lp.evaluate("() => document.querySelectorAll('.yt-embed').length")
        mountedTop = lp.evaluate("() => document.querySelectorAll('.yt-embed[data-mounted] iframe').length")
        check("all YouTube embeds are placeholders (48)", ph >= 40, ph)
        check("few/none mounted before scrolling", mountedTop <= 8, mountedTop)
        cap_max = 0
        for y in range(0, 30000, 600):
            lp.evaluate("(y) => window.scrollTo(0,y)", y)
            lp.wait_for_timeout(90)
            n = lp.evaluate("() => document.querySelectorAll('.yt-embed[data-mounted] iframe').length")
            cap_max = max(cap_max, n)
        check("mounted iframes never exceed cap (8) while scrolling", cap_max <= 8, "max=%d" % cap_max)
        lp.close()

        # === 7. Publications tab loads with fixed links (no 404) ===
        print("\n[7] Publications tab + fixed links")
        pubp = new_page(browser, base)
        pubp.goto(base + "/cv/#publications", wait_until="load")
        pubp.wait_for_timeout(2500)
        pub = pubp.evaluate("""() => {
          const cards=document.querySelectorAll('#includePapers .well').length;
          const pdfs=[...document.querySelectorAll('#includePapers a[href$=\".pdf\"]')].map(a=>a.href);
          return {cards, samplePdfs:pdfs.slice(0,3)};
        }""")
        check("publications cards rendered", pub["cards"] > 0, pub["cards"])
        # HEAD-check a sample of PDF links actually resolve
        pdf_ok = True; pdf_detail = []
        for u in pub["samplePdfs"]:
            r = pubp.request.head(u)
            if r.status >= 400:
                pdf_ok = False; pdf_detail.append("%d %s" % (r.status, u))
        check("sample publication PDF links resolve (no 404)", pdf_ok, pdf_detail)
        check("no broken assets (>=400) on publications tab", not pubp.bad, pubp.bad[:5])
        pubp.close()

        # === 8. Landing page featured cards (generated from shared teaser files) ===
        print("\n[8] Landing page featured cards")
        ix = new_page(browser, base)
        ix.goto(base + "/index.html", wait_until="load")
        ix.wait_for_timeout(1500)
        info = ix.evaluate("""() => ({
          cards: document.querySelectorAll('#select_content .well[id]').length,
          cvLinks: document.querySelectorAll('#select_content a[href^=\"cv/#projects/\"]').length,
          badParent: [...document.querySelectorAll('#select_content img')].some(i => (i.getAttribute('src')||'').startsWith('../'))
        })""")
        check("index featured cards rendered from teasers", info["cards"] >= 5, info)
        check("index card images are root-relative (no ../ paths)", info["badParent"] is False, info)
        check("index 'more info' links point to cv page", info["cvLinks"] > 0, info)
        check("no broken assets (>=400) on landing page", not ix.bad, ix.bad[:5])
        ix.close()

        # === 9. Floating "Top" button (hidden at top, appears on scroll, returns to top) ===
        print("\n[9] Floating Top button")
        tp = new_page(browser, base)
        tp.goto(base + "/cv/", wait_until="load")
        tp.wait_for_timeout(1000)
        hidden = tp.evaluate("() => getComputedStyle(document.querySelector('.sticky-button-container')).opacity")
        tp.evaluate("() => window.scrollTo(0, 1500)")
        tp.wait_for_timeout(500)
        shown = tp.evaluate("() => getComputedStyle(document.querySelector('.sticky-button-container')).opacity")
        # click the button's PADDING (top-left corner, not the text) to prove the whole block is tappable
        boxinfo = tp.evaluate("""() => {
          const b = document.querySelector('.sticky-top-button'); const r = b.getBoundingClientRect();
          return { tag: b.tagName, x: r.left + 4, y: r.top + 4 };  // 4px in from the corner = padding area
        }""")
        tp.mouse.click(boxinfo["x"], boxinfo["y"])
        tp.wait_for_timeout(1200)
        back = tp.evaluate("() => ({ y: Math.round(window.pageYOffset), hash: location.hash })")
        check("Top button hidden at top, visible after scroll", hidden == "0" and shown == "1", {"top": hidden, "scrolled": shown})
        check("whole Top button is the link (corner/padding click works)", boxinfo["tag"] == "A" and back["y"] < 5, {"tag": boxinfo["tag"], **back})
        check("Top button returns to top without changing the URL", back["hash"] == "", back)
        tp.close()

        browser.close()
    httpd.shutdown()

    # ---- summary ----
    passed = sum(1 for _, ok, _ in _results if ok)
    failed = len(_results) - passed
    print("\n==================== SUMMARY ====================")
    print("  %d passed, %d failed, %d total" % (passed, failed, len(_results)))
    if failed:
        for n, ok, d in _results:
            if not ok:
                print("  FAILED: %s  %s" % (n, d))
    print("================================================")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
