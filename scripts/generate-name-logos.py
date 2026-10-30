#!/usr/bin/env python3
"""Generate the logo for every entry from its name.

The landscape shows no organization logos. Each entry's "logo" is its name,
set in black Inter SemiBold and outlined to SVG paths, so the files never
depend on installed fonts and no trademark is reproduced.

One type size for every entry: the script finds the size each name needs to
fit (at most MAX_SIZE, wrapped to at most MAX_LINES lines, breaking after a
hyphen only when a name cannot fit otherwise) and renders every
name at the smallest of those sizes. No entry is set larger than another.

Usage: python3 scripts/generate-name-logos.py [data.yml] [logos dir]
Runs in CI before the build. Generated files are not committed.
"""
import re
import sys
from html import escape
from itertools import combinations
from pathlib import Path

import yaml
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT = Path(__file__).with_name("fonts") / "Inter-SemiBold.otf"
W, H = 240, 240      # canvas; landscape2 scales it to the grid tile
PAD = 6              # side padding
MAX_W = W - 2 * PAD
MAX_SIZE = 39.5      # largest type size any name can get (decided 2026-10-30)
MIN_SIZE = 22        # below this the map gets hard to read; fail instead
MAX_LINES = 4
LEADING = 1.22
FILL = "#000000"

# landscape2 trims each logo's viewBox to its visible content, which would
# enlarge short names and shrink long ones. Two near-invisible corner dots
# keep the box at the full canvas so the shared type size survives.
ANCHORS = (f'<rect x="0" y="0" width="1" height="1" fill="#000" fill-opacity="0.01"/>'
           f'<rect x="{W - 1}" y="{H - 1}" width="1" height="1" fill="#000" fill-opacity="0.01"/>')


class Face:
    def __init__(self, path):
        font = TTFont(path)
        self.gs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self.upm = font["head"].unitsPerEm
        self.cap = getattr(font["OS/2"], "sCapHeight", 0) or self.upm * 0.7

    def missing(self, text):
        return sorted({c for c in text if not c.isspace() and ord(c) not in self.cmap})

    def width(self, text, size):
        s = size / self.upm
        return sum(self.gs[self.cmap[ord(c)]].width * s for c in text if ord(c) in self.cmap)

    def path(self, text, size, x, baseline):
        s = size / self.upm
        out, cur = [], x
        for c in text:
            g = self.cmap.get(ord(c))
            if g is None:
                continue
            pen = SVGPathPen(self.gs)
            self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cur, baseline)))
            if pen.getCommands():
                out.append(pen.getCommands())
            cur += self.gs[g].width * s
        return " ".join(out)


def tokens(name):
    """Words, with hyphenated words also breakable after the hyphen."""
    return [t for t in re.split(r"(?<=-)(?=\S)|\s+", name) if t]


def join(parts):
    """Rejoin tokens: no space after a token that ends in a hyphen."""
    out = parts[0]
    for prev, t in zip(parts, parts[1:]):
        out += t if prev.endswith("-") else " " + t
    return out


def wrap(face, name, size):
    """Fewest lines that fit at this size; then fewest breaks at a hyphen;
    then the most even line lengths."""
    words = tokens(name)
    for n in range(1, min(MAX_LINES, len(words)) + 1):
        if n * size * LEADING > H - 2 * PAD:
            return None
        best = None
        for cuts in combinations(range(1, len(words)), n - 1):
            idx = (0, *cuts, len(words))
            lines = [join(words[idx[i]:idx[i + 1]]) for i in range(n)]
            widest = max(face.width(l, size) for l in lines)
            hyphen_breaks = sum(words[c - 1].endswith("-") for c in cuts)
            key = (hyphen_breaks, widest)
            if widest <= MAX_W and (best is None or key < best[0]):
                best = (key, lines)
        if best:
            return best[1]
    return None


def fit_size(face, name):
    size = MAX_SIZE
    while size >= 1:
        if wrap(face, name, size):
            return size
        size -= 0.5
    return 0


def render(face, name, size):
    lines = wrap(face, name, size)
    cap = face.cap * size / face.upm
    gap = size * LEADING
    first = (H - (cap + gap * (len(lines) - 1))) / 2 + cap
    d = " ".join(face.path(l, size, (W - face.width(l, size)) / 2, first + i * gap)
                 for i, l in enumerate(lines))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
            f'<title>{escape(name)}</title>{ANCHORS}<path fill="{FILL}" d="{d}"/></svg>\n')


def entries(data_file):
    data = yaml.safe_load(Path(data_file).read_text())
    for cat in data.get("categories") or []:
        for sub in cat.get("subcategories") or []:
            for item in sub.get("items") or []:
                yield item["name"], item.get("logo", "")


def main():
    data_file = sys.argv[1] if len(sys.argv) > 1 else "data.yml"
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "logos")
    face = Face(FONT)
    items, errors, seen = list(entries(data_file)), [], {}
    for name, logo in items:
        if not logo.endswith(".svg") or "/" in logo:
            errors.append(f'{name}: logo must be a file name ending in .svg, got "{logo}"')
        elif logo in seen and seen[logo] != name:
            errors.append(f'{name}: logo "{logo}" is already used by {seen[logo]}')
        seen.setdefault(logo, name)
        if face.missing(name):
            errors.append(f"{name}: characters not in the font: {' '.join(face.missing(name))}")
    if errors:
        sys.exit("generate-name-logos: " + "\n  ".join(["fix data.yml:"] + errors))

    sizes = {name: fit_size(face, name) for name, _ in items}
    size = min(sizes.values(), default=MAX_SIZE)
    smallest = [n for n, s in sizes.items() if s == size]
    if size < MIN_SIZE:
        sys.exit(f"generate-name-logos: {', '.join(smallest)} only fits at {size}; every name "
                 f"would shrink below {MIN_SIZE}. Use a shorter display name in data.yml.")

    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.svg"):
        old.unlink()
    for name, logo in items:
        (out / logo).write_text(render(face, name, size))
    who = "" if size == MAX_SIZE else f", set by {', '.join(smallest)}"
    print(f"generate-name-logos: {len(items)} logos at size {size}{who}")


if __name__ == "__main__":
    main()
