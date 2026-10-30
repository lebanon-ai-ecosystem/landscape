#!/usr/bin/env python3
"""Render the landscape as a 16:9 slide (1920x1080), as PNG and PDF.

The interactive map stacks categories in full-width rows, which does not fit a
slide. This script lays the same data out in three columns, using the same
name tiles and category colors, and picks the largest tile size at which
everything fits on one 16:9 page. Run in CI after the name logos are
generated; the files are published with the site under downloads/.

Usage: python3 scripts/make-slide.py <data.yml> <logos dir> <category-colors.json> <out dir>
Needs PyYAML and Playwright with Chromium.
"""
import base64
import datetime
import json
import sys
from html import escape
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

W, H = 1920, 1080
NAME = "lebanon-ai-ecosystem-slide"
FONT = Path(__file__).with_name("fonts") / "Inter-SemiBold.otf"
URL = "lebanon-ai-ecosystem.github.io/landscape"

# Column layout. AI stack categories share one wrapped row at the top of the
# first column. Every category in data.yml must appear here, or the build
# fails, so a new category is never left off the slide by accident.
AI_STACK = ["Infrastructure and compute", "Data", "Models and core AI", "Tools and platforms"]
COLUMNS = [
    {"stack": AI_STACK, "below": ["Applied AI"]},
    {"stack": [], "below": ["Research and academia", "Lebanese-founded abroad"]},
    {"stack": [], "below": ["Ecosystem enablers"]},
]
TILE_MAX, TILE_MIN = 160, 60  # pixels; below TILE_MIN the build fails

CSS = """
@font-face{font-family:Inter;src:url(data:font/otf;base64,FONT64) format('opentype');font-weight:600}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;overflow:hidden}
body{--t:100px;font-family:Inter,Arial,sans-serif;font-weight:600;background:#fff;color:#111;
  padding:36px 44px;display:flex;flex-direction:column}
header{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid #007A48;
  padding-bottom:14px;margin-bottom:18px}
h1{font-size:40px;font-weight:600;letter-spacing:-.5px}
.lede{font-size:20px;color:#444;margin-top:4px}
.url{font-size:20px;color:#007A48}
main{flex:1;display:flex;gap:14px;min-height:0}
.col{flex:1;display:flex;flex-direction:column;gap:14px;min-width:0}
.pair{display:flex;flex-wrap:wrap;gap:14px}
.pair>.cat{flex:1 1 auto}
.col>.cat{flex:0 0 auto}
.col>.cat:last-child{flex:1 1 auto}
.cat{display:flex;border:2px solid var(--c);min-width:0;overflow:hidden}
.ch{background:var(--c);color:#fff;font-size:17px;writing-mode:vertical-rl;transform:rotate(180deg);
  padding:10px 8px;text-align:center}
.subs{display:flex;flex-wrap:wrap;align-content:flex-start;gap:10px;padding:10px;flex:1;min-width:0}
.sub{border:1px solid #ddd;background:#fafafa;max-width:100%}
.sh{background:var(--c);color:#fff;font-size:14px;padding:5px 9px;white-space:nowrap}
.tiles{display:flex;flex-wrap:wrap;gap:8px;padding:8px}
.tile{width:var(--t);height:var(--t);background:#fff;border:1px solid #ccc}
.tile svg{display:block;width:100%;height:100%}
footer{font-size:15px;color:#555;margin-top:12px;display:flex;justify-content:space-between}
"""

FITS = """t => {
  document.body.style.setProperty('--t', t + 'px');
  const de = document.documentElement;
  if (de.scrollHeight > 1080 || de.scrollWidth > 1920) return false;
  for (const el of document.querySelectorAll('main,.col,.cat,.sub,.tiles'))
    if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) return false;
  const m = document.querySelector('main').getBoundingClientRect();
  for (const el of document.querySelectorAll('.tile')) {
    const r = el.getBoundingClientRect();
    if (r.bottom > m.bottom + 1 || r.right > m.right + 1) return false;
  }
  return true;
}"""


def build_html(data_file, logos_dir, colors_file):
    data = yaml.safe_load(Path(data_file).read_text())
    raw = json.loads(Path(colors_file).read_text())
    colors = {k: v for k, v in raw.items() if not k.startswith("_")}
    cats = {}
    for c in data["categories"]:
        subs = [(s["name"], s["items"]) for s in c.get("subcategories") or [] if s.get("items")]
        cats[c["name"]] = subs
    placed = {n for col in COLUMNS for n in col["stack"] + col["below"]}
    missing = sorted(set(cats) - placed)
    if missing:
        sys.exit(f"make-slide: add these categories to COLUMNS: {', '.join(missing)}")

    def tile(item):
        svg = (Path(logos_dir) / item["logo"]).read_text()
        return f'<div class="tile">{svg}</div>'

    def block(cat):
        if not cats.get(cat):
            return ""
        c = colors.get(cat, "#455A64")
        subs = "".join(
            f'<div class="sub"><div class="sh">{escape(n)}</div>'
            f'<div class="tiles">{"".join(tile(i) for i in items)}</div></div>'
            for n, items in cats[cat])
        return (f'<section class="cat" style="--c:{c}"><div class="ch">{escape(cat)}</div>'
                f'<div class="subs">{subs}</div></section>')

    cols = []
    for col in COLUMNS:
        stack = "".join(block(c) for c in col["stack"])
        below = "".join(block(c) for c in col["below"])
        cols.append(f'<div class="col">{f"<div class=pair>{stack}</div>" if stack else ""}{below}</div>')

    total = sum(len(i) for subs in cats.values() for _, i in subs)
    month = datetime.date.today().strftime("%B %Y")
    css = CSS.replace("FONT64", base64.b64encode(FONT.read_bytes()).decode())
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head><body>
<header><div><h1>Lebanon AI Ecosystem</h1>
<div class="lede">{total} organizations building, researching and backing AI in Lebanon and across its diaspora</div></div>
<div class="url">{URL}</div></header>
<main>{"".join(cols)}</main>
<footer><span>Every organization appears as its name; listing is free and follows published rules.</span>
<span>{month}</span></footer></body></html>"""


def main(data_file, logos_dir, colors_file, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    html_file = out / f"{NAME}.html"
    html_file.write_text(build_html(data_file, logos_dir, colors_file))
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        page.goto(html_file.resolve().as_uri())
        page.evaluate("document.fonts.ready")
        size = next((t for t in range(TILE_MAX, TILE_MIN - 1, -2) if page.evaluate(FITS, t)), None)
        if size is None:
            sys.exit(f"make-slide: entries no longer fit one slide at a {TILE_MIN}px tile; "
                     "adjust COLUMNS in scripts/make-slide.py")
        page.screenshot(path=str(out / f"{NAME}.png"))
        page.pdf(path=str(out / f"{NAME}.pdf"), width=f"{W}px", height=f"{H}px",
                 print_background=True, page_ranges="1")
        browser.close()
    html_file.unlink()
    print(f"make-slide: {NAME}.png and .pdf at a {size}px tile")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
