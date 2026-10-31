#!/usr/bin/env python3
"""Add a cookie-free visit counter (GoatCounter) to the built site.

Counts page views on the landscape app and on the Feedback page. The app is a
single-page app, so each route change is counted too: Explore, Guide, and each
entry's detail view (as /landscape/?item=<id>). Closing a detail view is not a
new visit. Other query parameters (group, view mode, filters) are left out so
the counts stay readable.

GoatCounter sets no cookies and stores no personal data; it does not count
visits from localhost. The site code lives in counter.yml; while it is empty
this step does nothing, so the site ships without a counter.

Usage: python3 scripts/add-counter.py <build dir> <counter.yml>
"""
import json
import re
import sys
from pathlib import Path

import yaml

SNIPPET = """<script>
(function () {
  window.goatcounter = { no_onload: true };
  var lastPage = null, lastItem = null;
  function count() {
    var page = location.pathname;
    var item = new URLSearchParams(location.search).get("item");
    if (item ? item === lastItem : page === lastPage) { if (!item) lastItem = null; return; }
    if (!window.goatcounter || !window.goatcounter.count) { setTimeout(count, 300); return; }
    lastPage = page;
    lastItem = item;
    window.goatcounter.count({ path: page + (item ? "?item=" + item : ""), title: document.title });
  }
  ["pushState", "replaceState"].forEach(function (fn) {
    var orig = history[fn];
    history[fn] = function () { var r = orig.apply(this, arguments); setTimeout(count, 0); return r; };
  });
  window.addEventListener("popstate", count);
  count();
})();
</script>
<script data-goatcounter=%(endpoint)s async src="https://gc.zgo.at/count.js"></script>
"""


def main(build_dir, config_file):
    config = yaml.safe_load(Path(config_file).read_text()) or {}
    code = (config.get("goatcounter_code") or "").strip()
    if not code:
        print("add-counter: no goatcounter_code in counter.yml; no counter added")
        return
    if not re.fullmatch(r"[a-z0-9-]{2,50}", code):
        sys.exit(f"add-counter: '{code}' is not a valid GoatCounter site code")
    snippet = SNIPPET % {"endpoint": json.dumps(f"https://{code}.goatcounter.com/count")}
    pages = [Path(build_dir) / "index.html", Path(build_dir) / "feedback" / "index.html"]
    for page in pages:
        html = page.read_text()
        if html.count("</body>") != 1:
            sys.exit(f"add-counter: could not find </body> in {page}")
        page.write_text(html.replace("</body>", snippet + "</body>", 1))
    print(f"add-counter: GoatCounter ({code}) added to {len(pages)} pages")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
