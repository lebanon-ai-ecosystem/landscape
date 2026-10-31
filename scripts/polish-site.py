#!/usr/bin/env python3
"""Design fixes applied to the built site (design review, 2026-10-31).

landscape2 (v1.1.0) exposes none of these as settings, so this post-build
step adds one <style> and one <script> to index.html:

- Explore: a two-sentence introduction above the toolbar, with the entry
  count, the date data.yml last changed and a link to the Feedback page.
- Map tiles: white, with a top rule in the category color, and 25 percent
  larger at every zoom level so names render at about 13px instead of 10.5px.
- Toolbar labels (GROUP, VIEW MODE, ZOOM, CLASSIFY, SORT) at 12px, and the
  search placeholder darkened from 2.3:1 to 4.7:1 contrast.
- Rotated category labels use the full row height, so most fit on one line.
- Item detail, hover card and search results: the name image is hidden (the
  name is already the title). The detail view adds a facts line: city, year and the date the
  entry was last checked.
- Card view: sentence-case subcategory names, no duplicate name image, and
  no "All" group (Full landscape already shows everything).
- Zoom view: the close button sits on the panel instead of the screen corner.
- Screen readers: map tiles no longer announce "<name> logo".
- Guide: text column capped at about 75 characters per line, and every
  section without entries is marked "No entries yet" with a link to suggest
  one. Both are computed from data.yml, so they stay current.
- Search typed on the Feedback page is carried over to the Explore search.

landscape2 class names carry build hashes. They are pinned to v1.1.0 and
checked here: if an upgrade changes any of them, the build fails instead of
shipping a site where the fixes silently stopped working.

Usage: python3 scripts/polish-site.py <build dir> <data.yml> <guide.yml> <settings.yml>
"""
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

# Hashed landscape2 v1.1.0 class names this script depends on.
CLASSES = [
    "_card_10iff_1", "whithoutRepo", "_logo_10iff_34", "_btnGroupLegend_1vg5k_36",
    "_catTitle_1rhfx_1", "_ellipsis_1rhfx_44", "_subcatTitle_o8010_6",
    "_subcategoryBtn_kqjn2_48", "_navLink_1vg5k_21", "_logoWrapper_1kumh_1",
    "_itemInfo_1kumh_14", "_closeWrapper_117tp_6", "_modal_117tp_1",
    "_guide_i93fj_1", "_section_i93fj_5", "_btn_17o67_38", "_filterBtn_1k8g1_13",
    "_desktopPlaceholder_ll0nr_22", "_desktopPlaceholderIcon_ll0nr_28", "_miniImageWrapper_ll0nr_63",
]

# Tile size per zoom level in landscape2 v1.1.0 (width, height), measured.
ZOOM = [(55, 50), (60, 54), (65, 59), (70, 63), (75, 68), (80, 72),
        (85, 77), (90, 81), (95, 85), (100, 90), (105, 94)]
SCALE = 1.25

STYLE = """<style id="lb-polish">
#lb-intro{font-size:15px;line-height:1.5;color:#212529;margin:14px 0 2px;max-width:62rem}
#lb-intro a{color:#007A48}
#lb-intro .lb-meta{color:#5c636a}
._card_10iff_1.whithoutRepo{background-color:#fff}
._card_10iff_1{border:1px solid #cfd6dc!important;border-top:3px solid var(--lb-cat,#455A64)!important}
%(zoom)s
._btnGroupLegend_1vg5k_36,._btnGroupLegend_1vg5k_36 small{font-size:12px!important}
._desktopPlaceholder_ll0nr_22,._desktopPlaceholderIcon_ll0nr_28{color:#6c757d!important}
._catTitle_1rhfx_1{height:calc(100%% - 1rem)!important}
button._subcategoryBtn_kqjn2_48.text-capitalize{text-transform:none!important}
button._navLink_1vg5k_21[aria-label="All"]{display:none!important}
._logoWrapper_1kumh_1,._miniImageWrapper_ll0nr_63,[data-lb-hide]{display:none!important}
._itemInfo_1kumh_14,[data-lb-info]{margin-left:0!important;width:100%%}
#item-view .lb-facts{font-size:14px;color:#5c636a;margin-top:6px}
._guide_i93fj_1{max-width:38rem}
.lb-empty-note{font-size:14px;color:#5c636a;margin:-4px 0 12px}
.lb-empty-note a{color:#007A48}
button._btn_17o67_38[data-lb-empty]{color:#8a9198!important;padding-right:5.5rem!important}
button._btn_17o67_38 .lb-empty-badge{position:absolute;right:12px;top:50%%;transform:translateY(-50%%);font-size:11px;font-weight:400;color:#6c757d}
</style>
"""

SCRIPT = """<script>
(function () {
  var BASE = %(base)s, FACTS = %(facts)s, EMPTY = %(empty)s, INTRO = %(intro)s;
  function path() { return location.pathname.replace(/\\/+$/, "/"); }
  function onExplore() { return path() === BASE || path() === BASE + "index.html"; }
  function onGuide() { return path().indexOf(BASE + "guide") === 0; }

  function intro() {
    var el = document.getElementById("lb-intro");
    var filter = document.querySelector("button._filterBtn_1k8g1_13");
    var bar = filter && filter.closest(".flex-lg-row");
    if (!onExplore() || !bar) { if (el) el.remove(); return; }
    if (el && el.nextElementSibling === bar) return;
    if (!el) { el = document.createElement("p"); el.id = "lb-intro"; el.innerHTML = INTRO; }
    bar.before(el);
  }

  function tiles() {
    document.querySelectorAll("._card_10iff_1:not([data-lb])").forEach(function (card) {
      var zoomView = card.closest("._modal_117tp_1");
      var title = null;
      if (zoomView) {
        title = zoomView.querySelector('[style*="background-color"]');
      } else {
        var col = card.parentElement;
        while (col && col !== document.body && !col.querySelector("._subcatTitle_o8010_6")) col = col.parentElement;
        title = col && col !== document.body ? col.querySelector("._subcatTitle_o8010_6") : null;
      }
      if (title && title.style.backgroundColor) card.style.setProperty("--lb-cat", title.style.backgroundColor);
      var img = card.querySelector("img._logo_10iff_34");
      if (img && card.querySelector("button[aria-label]")) img.alt = "";
      card.setAttribute("data-lb", "");
    });
  }

  function itemView() {
    var view = document.getElementById("item-view");
    if (!view || view.querySelector(".lb-facts")) return;
    var img = view.querySelector('img[src*="logos/"]');
    var name = view.querySelector(".fw-semibold.text-truncate");
    if (!img || !name) return;
    var logo = img.parentElement;
    var info = logo.nextElementSibling;
    if (info && info.contains(name)) {
      logo.setAttribute("data-lb-hide", "");
      info.setAttribute("data-lb-info", "");
    }
    var f = FACTS[name.textContent.trim()];
    if (!f) return;
    var line = document.createElement("div");
    line.className = "lb-facts";
    line.textContent = f;
    (info && info.contains(name) ? info : name.parentElement).appendChild(line);
  }

  function zoomClose() {
    var dialog = document.querySelector('[role="dialog"]._modal_117tp_1');
    if (!dialog) return;
    var close = dialog.querySelector("._closeWrapper_117tp_6");
    var holder = dialog.querySelector(".justify-content-center.h-100");
    var panel = holder && holder.firstElementChild;
    if (!close || !panel) return;
    var r = panel.getBoundingClientRect();
    if (!r.width) return;
    close.style.position = "fixed";
    close.style.top = (r.top + 2) + "px";
    close.style.left = (r.right - 34) + "px";
    close.style.right = "auto";
    close.style.zIndex = "10";
  }

  function guide() {
    if (!onGuide()) return;
    EMPTY.forEach(function (e) {
      document.querySelectorAll('[id="btn_' + e.id + '"]').forEach(function (btn) {
        if (btn.querySelector(".lb-empty-badge")) return;
        btn.setAttribute("data-lb-empty", "");
        var b = document.createElement("span");
        b.className = "lb-empty-badge";
        b.textContent = "No entries yet";
        btn.appendChild(b);
      });
      if (e.leaf) {
        var sec = document.getElementById("section_" + e.id);
        var h = sec && sec.querySelector("h1, h2, h3");
        if (h && !sec.querySelector(".lb-empty-note")) {
          var p = document.createElement("p");
          p.className = "lb-empty-note";
          p.innerHTML = 'No entries yet. Know one? <a href="' + BASE + 'feedback/">Suggest an entry</a>.';
          h.after(p);
        }
      }
    });
  }

  function handoff() {
    var v = null;
    try { v = sessionStorage.getItem("lb-search"); } catch (err) { return; }
    var input = document.getElementById("searchbar-desktop");
    if (!v || !onExplore() || !input) return;
    sessionStorage.removeItem("lb-search");
    input.focus();
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(input, v);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, key: v.slice(-1) }));
  }

  function run() { intro(); tiles(); itemView(); zoomClose(); guide(); handoff(); }
  var queued = false;
  new MutationObserver(function () {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; run(); });
  }).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener("resize", zoomClose);
  run();
})();
</script>
"""


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def human_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def short_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


def data_date(data_file):
    """Date data.yml last changed, from git; today if git has no answer."""
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", data_file],
                             capture_output=True, text=True, check=True).stdout.strip()
        if out:
            return out
    except (OSError, subprocess.CalledProcessError):
        pass
    return datetime.date.today().isoformat()


def main(build_dir, data_file, guide_file, settings_file):
    build = Path(build_dir)
    settings = yaml.safe_load(Path(settings_file).read_text())
    base = (settings.get("base_path") or "").rstrip("/") + "/"
    data = yaml.safe_load(Path(data_file).read_text())
    guide = yaml.safe_load(Path(guide_file).read_text())

    assets = build / "assets"
    bundle = "".join(p.read_text() for p in list(assets.glob("index-*.css")) + list(assets.glob("index-*.js")))
    missing = [c for c in CLASSES + ["item-view", "zoom-"] if c not in bundle]
    if missing:
        sys.exit(f"polish-site: not found in the landscape2 bundle: {', '.join(missing)}; landscape2 output changed")

    facts, filled, count = {}, set(), 0
    for cat in data["categories"]:
        for sub in cat.get("subcategories") or []:
            items = sub.get("items") or []
            if items:
                filled.add((cat["name"], sub["name"]))
            for item in items:
                count += 1
                a = (item.get("extra") or {}).get("annotations") or {}
                parts = []
                if a.get("city"):
                    parts.append(str(a["city"]))
                if a.get("founded"):
                    parts.append(f"Since {a['founded']}")
                if a.get("verified_on"):
                    parts.append(f"Last checked {short_date(str(a['verified_on']))}")
                if parts:
                    facts[item["name"]] = " · ".join(parts)

    empty = []
    map_categories = {c["name"] for c in data["categories"]}
    for cat in guide.get("categories") or []:
        if cat["category"] not in map_categories:
            continue  # Introduction and other text-only sections

        subs = [s["subcategory"] for s in cat.get("subcategories") or []]
        cat_empty = True
        for sub in subs:
            if (cat["category"], sub) in filled:
                cat_empty = False
            else:
                empty.append({"id": f"{slug(cat['category'])}--{slug(sub)}", "leaf": True})
        if subs and cat_empty:
            empty.append({"id": slug(cat["category"]), "leaf": False})

    updated = human_date(data_date(data_file))
    intro = (
        f"{count} organizations and open-source projects building, researching and backing AI "
        f"in Lebanon and across its diaspora. A neutral community map: listing is free and follows "
        f'<a href="{base}guide#introduction--listing-rules">published rules</a>. '
        f'<span class="lb-meta">Updated {updated} · </span>'
        f'<a href="{base}feedback/">Suggest an entry or a correction</a>'
    )

    zoom = "\n".join(
        f".zoom-{i}{{--card-size-width:{round(w * SCALE)}px!important;--card-size-height:{round(h * SCALE)}px!important}}"
        for i, (w, h) in enumerate(ZOOM)
    )
    style = STYLE % {"zoom": zoom}
    script = SCRIPT % {
        "base": json.dumps(base),
        "facts": json.dumps(facts, ensure_ascii=False),
        "empty": json.dumps(empty),
        "intro": json.dumps(intro, ensure_ascii=False),
    }

    index = build / "index.html"
    html = index.read_text()
    if html.count("</head>") != 1 or html.count("</body>") != 1:
        sys.exit("polish-site: could not find </head> and </body> in index.html")
    html = html.replace("</head>", style + "</head>", 1).replace("</body>", script + "</body>", 1)
    index.write_text(html)
    print(f"polish-site: {count} entries, {len(facts)} facts lines, "
          f"{sum(e['leaf'] for e in empty)} empty guide sections, updated {updated}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
