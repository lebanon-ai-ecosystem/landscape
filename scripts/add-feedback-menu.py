#!/usr/bin/env python3
"""Add FEEDBACK to the site's top menu, after STATS.

landscape2 (v1.1.0) has no setting for extra menu items. This post-build step
adds a small script to index.html that copies the STATS menu item (desktop
button and mobile link), relabels it FEEDBACK, and points it at the Feedback
page (feedback/), which scripts/make-feedback-page.py generates. The copy keeps
the original styling, so the new item looks like the others.

If a landscape2 upgrade changes the menu, the build fails instead of shipping a
site without the item.

Usage: python3 scripts/add-feedback-menu.py <build dir> <settings.yml>
"""
import sys
from pathlib import Path

import yaml

SCRIPT = """<script>
(function () {
  var url = "%(base)sfeedback/";
  function relabel(el) {
    if (el.children.length === 0) { el.textContent = "Feedback"; return; }
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    var node;
    while ((node = walker.nextNode())) {
      if (/stats/i.test(node.nodeValue)) { node.nodeValue = node.nodeValue.replace(/stats/i, "Feedback"); return; }
    }
  }
  function go(e) {
    e.preventDefault();
    e.stopPropagation();
    window.location.href = url;
  }
  function add() {
    var items = document.querySelectorAll('button[aria-label="Go to \\\\"Stats\\\\" page"], a[href$="/stats"]');
    items.forEach(function (item) {
      var parent = item.parentElement;
      var target = item.tagName === "A" && parent && parent.children.length === 1 ? parent : item;
      var next = target.nextElementSibling;
      if ((next && next.hasAttribute("data-lb-feedback")) || item.hasAttribute("data-lb-feedback")) return;
      var copy = target.cloneNode(true);
      copy.setAttribute("data-lb-feedback", "");
      var el = copy.tagName === item.tagName ? copy : copy.querySelector(item.tagName.toLowerCase());
      el.setAttribute("data-lb-feedback", "");
      el.classList.remove("activeLink", "active");
      relabel(el);
      if (el.tagName === "A") {
        el.classList.add("inactive");
        el.setAttribute("href", url);
        el.removeAttribute("state");
        el.removeAttribute("aria-current");
      } else {
        el.setAttribute("aria-label", 'Go to "Feedback" page');
      }
      el.addEventListener("click", go, true);
      target.after(copy);
    });
  }
  new MutationObserver(add).observe(document.documentElement, { childList: true, subtree: true });
  add();
})();
</script>
"""


def main(build_dir, settings_file):
    build = Path(build_dir)
    settings = yaml.safe_load(Path(settings_file).read_text())
    base = (settings.get("base_path") or "").rstrip("/") + "/"
    bundles = list((build / "assets").glob("index-*.js"))
    if len(bundles) != 1:
        sys.exit(f"add-feedback-menu: expected one assets/index-*.js bundle, found {len(bundles)}")
    js = bundles[0].read_text()
    for marker in ("Stats", "activeLink", "/stats"):
        if marker not in js:
            sys.exit(f"add-feedback-menu: '{marker}' not found in the bundle; landscape2 output changed")
    if not (build / "feedback" / "index.html").exists():
        sys.exit("add-feedback-menu: feedback/index.html missing; run make-feedback-page.py first")
    index = build / "index.html"
    html = index.read_text()
    if html.count("</body>") != 1:
        sys.exit("add-feedback-menu: could not find </body> in index.html")
    index.write_text(html.replace("</body>", SCRIPT % {"base": base} + "</body>", 1))
    print("add-feedback-menu: FEEDBACK added after STATS")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
