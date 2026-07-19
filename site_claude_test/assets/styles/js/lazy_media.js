/*
 * lazy_media.js — bounded lazy-loading of YouTube embeds.
 *
 * Problem: the projects page had ~48 live <iframe> YouTube players in one very tall DOM.
 * Each is a full browsing context; mounting many at once (e.g. a fast scroll through the
 * page) blows past iOS Safari's per-tab memory ceiling and crashes/reloads the tab.
 *
 * Approach (per requirements: keep it lazy-load, but never let a fast scroll mount them all):
 *   - Each embed is authored as a same-size placeholder <div class="yt-embed" data-embed="ID">
 *     that shows the video's thumbnail + play glyph — visually identical to an un-played embed.
 *   - An IntersectionObserver mounts the real iframe only after the placeholder has SETTLED in
 *     view for SETTLE_MS. Scrolling straight past never settles, so nothing mounts during a
 *     fast scroll.
 *   - At most CAP iframes are mounted at once. Mounting an (N+1)th evicts the farthest
 *     off-screen player (restoring its placeholder), so memory stays bounded no matter how the
 *     user scrolls. The player the user is currently interacting with (focused) and any player
 *     still on screen are never evicted.
 *   - Clicking a placeholder mounts immediately and autoplays (responsive click-to-play).
 *
 * Call window.initLazyMedia(rootEl) after injecting new content (the CV loads fragments via
 * AJAX). It is idempotent per element.
 */
(function () {
  var CAP = 8;            // max simultaneously-mounted players
  var SETTLE_MS = 200;    // must remain in view this long before auto-mounting
  var MOUNT_MARGIN = '200px';

  var live = [];          // mounted placeholders, oldest first
  var timers = new WeakMap();

  // Show the placeholder's still image. We prefer the sharp 16:9 "maxresdefault" (which matches
  // the real player exactly, so there's no reframe when the video fades in); if the video has no
  // HD thumbnail we fall back to "hqdefault" (always exists). This avoids the low-res / wrong-crop
  // flicker on load.
  function setThumb(ph, id) {
    var base = 'https://i.ytimg.com/vi/' + id + '/';
    var probe = new Image();
    probe.onload = function () {
      var hd = probe.naturalWidth > 300;   // a "missing maxres" reply is a tiny grey image
      ph.style.backgroundImage = "url('" + base + (hd ? 'maxresdefault.jpg' : 'hqdefault.jpg') + "')";
    };
    probe.onerror = function () {
      ph.style.backgroundImage = "url('" + base + "hqdefault.jpg')";
    };
    probe.src = base + 'maxresdefault.jpg';
  }

  function distFromViewport(el) {
    var r = el.getBoundingClientRect();
    var vh = window.innerHeight || document.documentElement.clientHeight;
    if (r.bottom < 0) return -r.bottom;      // above the viewport
    if (r.top > vh) return r.top - vh;       // below the viewport
    return 0;                                // on screen
  }

  function enforceCap() {
    if (live.length <= CAP) return;
    var evictable = live.filter(function (ph) {
      return distFromViewport(ph) > 0 &&
             document.activeElement !== ph.querySelector('iframe');
    });
    evictable.sort(function (a, b) { return distFromViewport(b) - distFromViewport(a); });
    while (live.length > CAP && evictable.length) {
      unmount(evictable.shift());
    }
  }

  function mount(ph, autoplay) {
    if (ph.getAttribute('data-mounted')) return;
    var id = ph.getAttribute('data-embed');
    if (!id) return;
    ph.setAttribute('data-mounted', '1');
    var iframe = document.createElement('iframe');
    iframe.src = 'https://www.youtube.com/embed/' + id + '?rel=0' + (autoplay ? '&autoplay=1' : '');
    iframe.setAttribute('frameborder', '0');
    iframe.setAttribute('allowfullscreen', '');
    iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
    iframe.setAttribute('title', 'YouTube video');
    // Fade the player in once it has actually loaded (see the .yt-loaded CSS). Until then the
    // thumbnail stays visible underneath, so there's no blank flash during the swap.
    iframe.addEventListener('load', function () { ph.classList.add('yt-loaded'); });
    ph.appendChild(iframe);
    live.push(ph);
    enforceCap();
  }

  function unmount(ph) {
    var f = ph.querySelector('iframe');
    if (f) { f.src = 'about:blank'; f.remove(); }
    ph.removeAttribute('data-mounted');
    ph.classList.remove('yt-loaded');   // so it fades in again if it's ever remounted
    var i = live.indexOf(ph);
    if (i >= 0) live.splice(i, 1);
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var ph = e.target;
      if (e.isIntersecting) {
        if (!ph.getAttribute('data-thumb') && ph.getAttribute('data-embed')) {
          ph.setAttribute('data-thumb', '1');
          setThumb(ph, ph.getAttribute('data-embed'));
        }
        if (!ph.getAttribute('data-mounted') && !timers.get(ph)) {
          timers.set(ph, setTimeout(function () {
            timers.delete(ph);
            mount(ph, false);
          }, SETTLE_MS));
        }
      } else {
        var t = timers.get(ph);
        if (t) { clearTimeout(t); timers.delete(ph); }
      }
    });
  }, { rootMargin: MOUNT_MARGIN, threshold: 0.01 });

  function attach(ph) {
    if (ph.getAttribute('data-observed')) return;
    ph.setAttribute('data-observed', '1');
    ph.addEventListener('click', function () {
      var t = timers.get(ph);
      if (t) { clearTimeout(t); timers.delete(ph); }
      mount(ph, true);   // click-to-play: mount immediately and autoplay
    });
    io.observe(ph);
  }

  function init(root) {
    var scope = root || document;
    var list = scope.querySelectorAll ? scope.querySelectorAll('.yt-embed[data-embed]') : [];
    Array.prototype.forEach.call(list, attach);
  }

  window.initLazyMedia = init;
  if (document.readyState !== 'loading') init();
  else document.addEventListener('DOMContentLoaded', function () { init(); });
})();
