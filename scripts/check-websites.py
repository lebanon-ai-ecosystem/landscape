#!/usr/bin/env python3
"""Open every homepage_url in data.yml and report the ones that fail.

Listing rule 2 says every entry has a working website. This keeps it true
after launch. Run weekly by .github/workflows/website-check.yml.

Usage: python3 scripts/check-websites.py [data.yml] [report.md]
Exit code 0 always; the report file is written only when something fails.
"""
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36 lebanon-ai-ecosystem-website-check")
TIMEOUT = 25
# Codes that usually mean "a bot was turned away", not "the site is gone".
SOFT = {401, 403, 405, 429, 503}


def fetch_once(url):
    """One try: HEAD, then GET if the server dislikes HEAD."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, ""
        except urllib.error.HTTPError as e:
            if method == "HEAD":
                continue
            return e.code, str(e)
        except Exception as e:  # DNS, TLS, timeout, connection refused
            if method == "HEAD":
                continue
            return None, f"{type(e).__name__}: {e}"
    return None, "no response"


def fetch(url):
    """Return (status or None, error text) after up to three tries."""
    for attempt in range(3):
        status, err = fetch_once(url)
        if status is not None and (status < 400 or status in (404, 410)):
            return status, err
        time.sleep(5 * (attempt + 1))
    return status, err


def entries(data_file):
    data = yaml.safe_load(Path(data_file).read_text())
    for cat in data.get("categories") or []:
        for sub in cat.get("subcategories") or []:
            for item in sub.get("items") or []:
                yield item["name"], item.get("homepage_url", ""), f'{cat["name"]} / {sub["name"]}'


def main():
    data_file = sys.argv[1] if len(sys.argv) > 1 else "data.yml"
    report = Path(sys.argv[2] if len(sys.argv) > 2 else "website-check.md")
    broken, soft, total = [], [], 0
    for name, url, where in entries(data_file):
        total += 1
        status, err = fetch(url)
        if status is not None and status < 400:
            continue
        row = f"| {name} | {where} | {url} | {status or err} |"
        (soft if status in SOFT else broken).append(row)
    print(f"checked {total}: {len(broken)} broken, {len(soft)} to check by hand")
    if not broken and not soft:
        report.unlink(missing_ok=True)
        return
    lines = [f"The weekly website check opened {total} homepages.", ""]
    if broken:
        lines += ["## Broken", "",
                  "These did not load (DNS, TLS, timeout, 404 or server error) after three tries.",
                  "Listing rule 2: fix the URL in `data.yml` or remove the entry.", "",
                  "| Entry | Where | URL | Result |", "| --- | --- | --- | --- |", *broken, ""]
    if soft:
        lines += ["## Check by hand", "",
                  "These refused the automated check (often bot protection). Open them in a browser.", "",
                  "| Entry | Where | URL | Result |", "| --- | --- | --- | --- |", *soft, ""]
    report.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
