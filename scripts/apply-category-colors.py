"""Give each landscape category its own header color.

landscape2 (v1.1.0) alternates every category between two colors (settings
color5 and color6). This post-build step patches the generated web app so a
category's color is looked up by name in category-colors.json, falling back to
the default alternation for any category not listed. Colors stay the same in
every view (full landscape and each group).

The patch targets two code patterns in the minified bundle. If a landscape2
upgrade changes them, this script fails the build instead of shipping a
half-patched site; update the patterns or drop the step.

Usage: python3 scripts/apply-category-colors.py <build_dir> <colors_json>
"""
import json
import re
import sys
from pathlib import Path

PATCHES = [
    # Grid view, full landscape
    ("categoryName:m,get bgColor(){return[...t()][f()]}",
     "categoryName:m,get bgColor(){return(window.__lbColors&&window.__lbColors[m])||[...t()][f()]}"),
    # Grid view, per group
    ("x=()=>o()[f()];return b(",
     "x=()=>(window.__lbColors&&window.__lbColors[m])||o()[f()];return b("),
]

COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def main(build_dir: str, colors_file: str) -> None:
    build = Path(build_dir)
    raw = json.loads(Path(colors_file).read_text())
    colors = {k: v for k, v in raw.items() if not k.startswith("_")}
    bad = [k for k, v in colors.items() if not COLOR.match(v)]
    if bad:
        sys.exit(f"invalid hex color for: {', '.join(bad)}")

    bundles = list((build / "assets").glob("index-*.js"))
    if len(bundles) != 1:
        sys.exit(f"expected one assets/index-*.js bundle, found {len(bundles)}")
    js = bundles[0].read_text()
    for old, new in PATCHES:
        count = js.count(old)
        if count != 1:
            sys.exit(f"pattern found {count} times (expected 1); landscape2 output changed: {old}")
        js = js.replace(old, new)
    bundles[0].write_text(js)

    index = build / "index.html"
    html = index.read_text()
    marker = '<script type="module"'
    if html.count(marker) != 1:
        sys.exit("could not find the app script tag in index.html")
    tag = f"<script>window.__lbColors={json.dumps(colors)};</script>\n    "
    index.write_text(html.replace(marker, tag + marker, 1))
    print(f"applied {len(colors)} category colors to {bundles[0].name}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
