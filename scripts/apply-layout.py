#!/usr/bin/env python3
"""Cap the width of the page content so a small landscape does not stretch.

landscape2 (v1.1.0) lays the map out across the full browser width. With few
entries per box, wide screens show long empty rows. This post-build step adds
one CSS rule to index.html that caps the main content area (toolbar, map,
guide, stats) at MAX_WIDTH pixels and centers it. The header keeps its full
width. Screens narrower than MAX_WIDTH are unaffected.

Raise MAX_WIDTH as the landscape fills up; remove the step to go back to full
width.

Usage: python3 scripts/apply-layout.py <build_dir>
"""
import sys
from pathlib import Path

MAX_WIDTH = 1040  # pixels, including the page's side padding

RULE = (f"main.mainPadding{{max-width:{MAX_WIDTH}px;"
        "margin-left:auto;margin-right:auto}")


def main(build_dir: str) -> None:
    build = Path(build_dir)
    if not any("mainPadding" in f.read_text() for f in (build / "assets").glob("index-*.js")):
        sys.exit("apply-layout: class mainPadding not found; landscape2 output changed")
    index = build / "index.html"
    html = index.read_text()
    if "</head>" not in html:
        sys.exit("apply-layout: no </head> in index.html; landscape2 output changed")
    index.write_text(html.replace("</head>", f"<style>{RULE}</style>\n  </head>", 1))
    print(f"capped content width at {MAX_WIDTH}px")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
