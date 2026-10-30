#!/usr/bin/env python3
"""Turn an approved "Add or update an entry" issue into a data.yml change.

Run by .github/workflows/issue-to-pr.yml when a maintainer adds the
`approved` label. Only "New entry" requests are automated; corrections and
removals touch existing blocks and stay manual.

The issue body is untrusted text. It is read from the ISSUE_BODY environment
variable, never interpolated into a shell command, and every value is written
into data.yml as a quoted YAML string.

Usage: ISSUE_BODY=... python3 scripts/issue-to-entry.py data.yml
Prints a JSON object: {"ok": true, "name": ..., "subcategory": ...} or
{"ok": false, "reason": ...}. Exit code is 0 either way.
"""
import datetime
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import yaml

PRESENCE = {
    "Company in Lebanon": "hq",
    "Lebanese-founded company abroad": "diaspora",
}
MAX_DESC = 200


def parse_form(body):
    """GitHub issue forms render as '### Label' then the value."""
    fields, label, buf = {}, None, []
    for line in body.replace("\r\n", "\n").split("\n"):
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            if label is not None:
                fields[label] = "\n".join(buf).strip()
            label, buf = m.group(1), []
        elif label is not None:
            buf.append(line)
    if label is not None:
        fields[label] = "\n".join(buf).strip()
    return {k: ("" if v == "_No response_" else v) for k, v in fields.items()}


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def q(value):
    """A double-quoted YAML scalar that is safe for any input."""
    return json.dumps(value, ensure_ascii=False)


def fail(reason):
    print(json.dumps({"ok": False, "reason": reason}))
    sys.exit(0)


def main():
    data_file = Path(sys.argv[1] if len(sys.argv) > 1 else "data.yml")
    f = parse_form(os.environ.get("ISSUE_BODY", ""))

    if f.get("Request type") != "New entry":
        fail("Only new entries are automated. Edit `data.yml` by hand for corrections and removals.")

    name = " ".join(f.get("Organization name", "").split())
    url = f.get("Website", "").strip()
    desc = " ".join(f.get("One-sentence description", "").split())
    etype = f.get("Entity type", "")
    wanted = " ".join(f.get("Proposed subcategory", "").split())
    city = " ".join(f.get("City", "").split())
    founded = f.get("Year founded", "").strip()

    if not name:
        fail("The issue has no organization name.")
    if not re.match(r"^https?://[^\s\"'<>]+$", url):
        fail(f"The website is not a plain http(s) URL: `{url[:100]}`.")
    if not desc:
        fail("The issue has no description.")
    if len(desc) > MAX_DESC:
        fail(f"The description is {len(desc)} characters; the limit is {MAX_DESC}. Edit the issue, then re-apply `approved`.")
    if founded and not re.match(r"^(19|20)\d\d$", founded):
        fail(f"Year founded should be a four-digit year, not `{founded[:20]}`.")

    data = yaml.safe_load(data_file.read_text())
    subs, names, logos = {}, set(), set()
    for cat in data["categories"]:
        for sub in cat.get("subcategories") or []:
            subs[sub["name"].casefold()] = (cat["name"], sub["name"])
            for it in sub.get("items") or []:
                names.add(it["name"].casefold())
                logos.add(it.get("logo", ""))
    if name.casefold() in names:
        fail(f"`{name}` is already on the map. Use a correction request instead.")
    if wanted.casefold() not in subs:
        valid = "\n".join(f"- {c} / {s}" for c, s in sorted(subs.values()))
        fail("The proposed subcategory does not match one on the map. Edit the issue so "
             "\"Proposed subcategory\" is one of these exact names, then re-apply `approved`:\n\n" + valid)
    cat_name, sub_name = subs[wanted.casefold()]
    logo = slug(name) + ".svg"
    if logo in logos:
        fail(f"Another entry already uses the logo file `{logo}`. Add this one by hand.")

    today = datetime.date.today().isoformat()
    block = [
        f"          - name: {q(name)}",
        f"            description: {q(desc)}",
        f"            homepage_url: {url}",
        f"            logo: {logo}",
        "            extra:",
        "              annotations:",
        f"                presence: {PRESENCE.get(etype, 'hq')}",
        f"                city: {q(city)}",
        f"                founded: {q(founded)}",
        "                verified_by: public-sources",
        f"                verified_on: {q(today)}",
        "                confidence: medium",
    ]

    lines = data_file.read_text().split("\n")
    # Find the subcategory inside its category (subcategory names can repeat).
    cat_at = next(i for i, l in enumerate(lines) if l == f"  - name: {q(cat_name)}")
    sub_at = next(i for i in range(cat_at + 1, len(lines))
                  if lines[i] == f"      - name: {q(sub_name)}")
    items_at = sub_at + 1
    if lines[items_at].strip() == "items: []":
        lines[items_at] = "        items:"
        insert_at = items_at + 1
    else:
        # Walk the existing items; keep alphabetical order by name.
        insert_at, i = None, items_at + 1
        while i < len(lines) and (lines[i].startswith("          ") or lines[i] == ""):
            m = re.match(r'^          - name: "(.*)"$', lines[i])
            if m and insert_at is None and m.group(1).casefold() > name.casefold():
                insert_at = i
            i += 1
        if insert_at is None:
            insert_at = i
    lines[insert_at:insert_at] = block
    data_file.write_text("\n".join(lines))

    yaml.safe_load(data_file.read_text())  # still parses
    print(json.dumps({"ok": True, "name": name, "subcategory": f"{cat_name} / {sub_name}"}))


if __name__ == "__main__":
    main()
