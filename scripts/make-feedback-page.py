#!/usr/bin/env python3
"""Generate the Feedback page: build/feedback/index.html.

Readers can suggest a new entry, correct or ask to remove an entry, or send
general feedback. Two routes, both from one form:

  Send            posts to Web3Forms, which forwards it to the project inbox
                  (needs web3forms_access_key in feedback.yml). Maintainers log
                  each one as a public issue without the sender's details.
  Open as issue   opens a GitHub issue with the same answers filled in, using
                  the "Add or update an entry" issue form.

The entry list, the subcategory list and the entity types are read from
data.yml and the issue form on every build, so the page never drifts from the
map. The site header and footer are redrawn here because this page sits
outside the landscape2 app. They copy the app's measurements (72px header,
search box, download menu, GitHub link, black footer) so the menu does not
jump between pages. A search typed here is handed to the Explore page.

Usage: python3 scripts/make-feedback-page.py <data.yml> <feedback.yml> <settings.yml> <build dir>
"""
import json
import sys
from html import escape
from pathlib import Path

import yaml

ISSUE_FORM = Path(__file__).resolve().parent.parent / ".github" / "ISSUE_TEMPLATE" / "add-entry.yml"


def options_from_issue_form(field_id):
    form = yaml.safe_load(ISSUE_FORM.read_text())
    for field in form["body"]:
        if field.get("id") == field_id:
            return field["attributes"]["options"]
    sys.exit(f"make-feedback-page: field '{field_id}' not found in {ISSUE_FORM.name}")


def main(data_file, config_file, settings_file, build_dir):
    data = yaml.safe_load(Path(data_file).read_text())
    config = yaml.safe_load(Path(config_file).read_text())
    settings = yaml.safe_load(Path(settings_file).read_text())
    base = (settings.get("base_path") or "").rstrip("/") + "/"

    groups, entries = [], []
    for cat in data["categories"]:
        subs = [s["name"] for s in cat.get("subcategories") or []]
        groups.append((cat["name"], subs))
        for sub in cat.get("subcategories") or []:
            for item in sub.get("items") or []:
                entries.append({"name": item["name"], "url": item.get("homepage_url", "")})
    entries.sort(key=lambda e: e["name"].casefold())

    types = options_from_issue_form("type")
    requests = options_from_issue_form("request")
    relationships = options_from_issue_form("relationship")
    if len(requests) != 3:
        sys.exit("make-feedback-page: expected 3 request types in the issue form")

    sub_options = "".join(
        f'<optgroup label="{escape(c)}">' + "".join(f"<option>{escape(s)}</option>" for s in subs) + "</optgroup>"
        for c, subs in groups)
    entry_options = "".join(f'<option>{escape(e["name"])}</option>' for e in entries)
    type_options = "".join(f"<option>{escape(t)}</option>" for t in types)
    rel_options = "".join(f"<option>{escape(r)}</option>" for r in relationships)

    cfg = {
        "key": config.get("web3forms_access_key") or "",
        "repo": config["repository"],
        "requests": requests,
        "homepages": {e["name"]: e["url"] for e in entries},
    }

    html = PAGE.format(
        base=base, sub_options=sub_options, entry_options=entry_options,
        type_options=type_options, rel_options=rel_options,
        cfg=json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"),
        repo=escape(config["repository"]),
    )
    out = Path(build_dir) / "feedback"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html)
    route = "email and GitHub" if cfg["key"] else "GitHub only (no Web3Forms key yet)"
    print(f"make-feedback-page: feedback/index.html with {len(entries)} entries; routes: {route}")


PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Feedback | Lebanon AI Ecosystem</title>
<link rel="icon" href="{base}images/favicon.png">
<style>
*{{box-sizing:border-box}}
a{{color:#007A48}}
body{{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:#1c1c1c;background:#fff}}
.sitehdr{{height:72px;padding:8px 0;margin-bottom:8px;background:#fff;border-bottom:1px solid #dee2e6;box-shadow:0 2px 4px rgba(0,0,0,.075)}}
.sitehdr .in{{display:flex;align-items:center;height:100%;padding:0 24px}}
.sitehdr .logo{{display:block;padding:0 16px 0 1px;line-height:0}}
.sitehdr .logo img{{height:34px;display:block}}
.sitehdr nav{{display:flex;gap:32px;margin-left:65px}}
.sitehdr nav a{{position:relative;color:#007A48;text-decoration:none;text-transform:uppercase;font-weight:700;letter-spacing:2px;font-size:16px;line-height:1.5;border:1px solid transparent;border-bottom-width:6px}}
.sitehdr nav a.on::before{{content:"";position:absolute;left:0;right:0;bottom:-4px;height:3px;background:#007A48}}
.sitehdr nav a:hover{{color:#00331F}}
.search{{position:relative;display:flex;align-items:center;width:500px;height:30px;margin-left:auto;margin-right:32px;background:#fff;box-shadow:0 0 0 2.4px #e9ecef}}
.search input[type=text]{{flex-grow:1;border:0;outline:0;width:auto;background:transparent;font:inherit;font-size:12.8px;padding:0 0 0 16px;height:100%}}
.search .ph{{position:absolute;left:16px;top:0;bottom:0;display:flex;align-items:center;font-size:12.8px;color:#6c757d;pointer-events:none}}
.search .ph small{{font-size:8.96px;line-height:13.44px;padding:2.4px 8px;margin:0 4px;border:1px solid #dee2e6;border-radius:6px}}
.search input:focus + .ph, .search input:not(:placeholder-shown) + .ph{{display:none}}
.search .icon{{padding:4px 8px;color:#00331F;font-size:12.8px;line-height:0}}
.search:focus-within{{box-shadow:0 0 0 2.4px #4da078}}
.icons{{display:flex;align-items:center}}
.icons button,.icons a{{background:none;border:0;padding:0;margin:0;color:#212529;font-size:20px;line-height:0;cursor:pointer}}
.icons a{{margin-left:16px;font-size:22px}}
.dl{{position:relative}}
.dl .menu{{display:none;position:absolute;right:-12px;top:38px;width:350px;background:#fff;border:1px solid #6c757d;box-shadow:0 8px 16px rgba(0,0,0,.5);font-size:14.4px;z-index:10;line-height:1.5}}
.dl.open .menu{{display:block}}
.dl .menu .hd{{text-transform:uppercase;text-align:center;font-weight:600;padding:8px;background:#f8f9fa}}
.dl .menu a{{display:block;margin:0;padding:16px;border-top:1px solid #dee2e6;color:#212529;text-decoration:none;font-size:14.4px;line-height:1.5}}
.dl .menu a:hover{{background:#e9ecef}}
.dl .menu b{{display:block;font-weight:600;margin-bottom:4px}}
.dl .menu i{{color:#6c757d;font-size:12.8px}}
footer{{margin-top:24px;padding:48px 64px;background:#000;color:#fff}}
footer .top{{display:flex;align-items:center;justify-content:space-between}}
footer .top img{{height:40px;display:block}}
footer .top a{{color:#fff;font-size:28px;line-height:0}}
footer hr{{border:0;border-top:1px solid #fff;opacity:.25;margin:32px 0}}
footer .legend{{font-size:11.2px;color:#ced4da;padding-top:8px}}
footer .legend a{{color:#fff;font-weight:600}}
main{{max-width:760px;margin:0 auto;padding:36px 24px 64px}}
h1{{color:#007A48;font-weight:500;font-size:40px;margin:0 0 12px}}
.lede{{font-size:17px;line-height:1.55;margin:0 0 28px}}
fieldset{{border:0;padding:0;margin:0 0 22px}}
legend,label.q{{display:block;font-weight:600;margin-bottom:8px}}
.hint{{font-size:14px;color:#555;margin:-4px 0 8px}}
.choices label{{display:block;padding:6px 0;cursor:pointer}}
input[type=text],input[type=url],input[type=email],select,textarea{{width:100%;font:inherit;padding:10px 12px;border:1px solid #bbb;border-radius:0}}
textarea{{min-height:110px;resize:vertical}}
input:focus,select:focus,textarea:focus{{outline:2px solid #007A48;outline-offset:1px}}
.section{{display:none}} .section.show{{display:block}}
.optional{{font-weight:400;color:#666}}
.check{{display:flex;gap:10px;align-items:flex-start}}
.actions{{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}}
button{{font:inherit;font-weight:600;padding:12px 22px;border:2px solid #007A48;cursor:pointer}}
#send{{background:#007A48;color:#fff}} #send:disabled{{opacity:.45;cursor:not-allowed}}
#issue{{background:#fff;color:#007A48}}
#status{{margin-top:18px;font-weight:600}}
.privacy{{font-size:14px;color:#555;margin-top:28px;line-height:1.5;border-top:1px solid #e5e5e5;padding-top:16px}}
.hp{{position:absolute;left:-5000px}}
@media (max-width:991px){{.sitehdr{{height:auto}} .sitehdr .in{{flex-wrap:wrap;gap:12px;padding:8px 16px}} .sitehdr nav{{order:2;width:100%;margin-left:0;gap:20px}} .search{{order:3;width:100%;margin:4px 0}} .icons{{order:1;margin-left:auto}} footer{{padding:32px 24px}}}}
</style></head>
<body>
<header class="sitehdr"><div class="in">
  <a class="logo" href="{base}"><img src="{base}images/header-logo.svg" alt="Lebanon AI Ecosystem" height="34"></a>
  <nav aria-label="Main"><a href="{base}">Explore</a><a href="{base}guide">Guide</a><a class="on" href="{base}feedback/" aria-current="page">Feedback</a></nav>
  <form class="search" role="search" id="search" action="{base}">
    <input type="text" id="q" placeholder=" " autocomplete="off" aria-label="Search items">
    <div class="ph" aria-hidden="true">Type <small>/</small> to search items</div>
    <span class="icon" aria-hidden="true"><svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
  </form>
  <div class="icons">
    <div class="dl" id="dl">
      <button type="button" aria-label="Open downloads" aria-expanded="false" aria-controls="dlmenu"><svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></button>
      <div class="menu" id="dlmenu">
        <div class="hd">Landscape</div>
        <a href="{base}docs/landscape.pdf" download><b>landscape.pdf</b><i>Landscape in PDF format</i></a>
        <a href="{base}docs/landscape.png" download><b>landscape.png</b><i>Landscape in PNG format</i></a>
        <div class="hd">Data files</div>
        <a href="{base}"><b>items.csv and projects.csv</b><i>From the download menu on the Explore page</i></a>
      </div>
    </div>
    <a href="https://github.com/{repo}" target="_blank" rel="noopener noreferrer" aria-label="Project repository on GitHub"><svg viewBox="0 0 496 512" width="1em" height="1em" fill="currentColor"><path id="gh" d="M165.9 397.4c0 2-2.3 3.6-5.2 3.6-3.3.3-5.6-1.3-5.6-3.6 0-2 2.3-3.6 5.2-3.6 3-.3 5.6 1.3 5.6 3.6zm-31.1-4.5c-.7 2 1.3 4.3 4.3 4.9 2.6 1 5.6 0 6.2-2s-1.3-4.3-4.3-5.2c-2.6-.7-5.5.3-6.2 2.3zm44.2-1.7c-2.9.7-4.9 2.6-4.6 4.9.3 2 2.9 3.3 5.9 2.6 2.9-.7 4.9-2.6 4.6-4.6-.3-1.9-3-3.2-5.9-2.9zM244.8 8C106.1 8 0 113.3 0 252c0 110.9 69.8 205.8 169.5 239.2 12.8 2.3 17.3-5.6 17.3-12.1 0-6.2-.3-40.4-.3-61.4 0 0-70 15-84.7-29.8 0 0-11.4-29.1-27.8-36.6 0 0-22.9-15.7 1.6-15.4 0 0 24.9 2 38.6 25.8 21.9 38.6 58.6 27.5 72.9 20.9 2.3-16 8.8-27.1 16-33.7-55.9-6.2-112.3-14.3-112.3-110.5 0-27.5 7.6-41.3 23.6-58.9-2.6-6.5-11.1-33.3 2.6-67.9 20.9-6.5 69 27 69 27 20-5.6 41.5-8.5 62.8-8.5s42.8 2.9 62.8 8.5c0 0 48.1-33.6 69-27 13.7 34.7 5.2 61.4 2.6 67.9 16 17.7 25.8 31.5 25.8 58.9 0 96.5-58.9 104.2-114.8 110.5 9.2 7.9 17 22.9 17 46.4 0 33.7-.3 75.4-.3 83.6 0 6.5 4.6 14.4 17.3 12.1C428.2 457.8 496 362.9 496 252 496 113.3 383.5 8 244.8 8z"/></svg></a>
  </div>
</div></header>
<main>
<h1>Feedback</h1>
<p class="lede">Suggest an organization or project, correct an entry, ask for a removal, or tell us what to improve. Every suggestion is reviewed against the published <a href="{base}guide#introduction--listing-rules">listing rules</a>, and maintainers answer within 7 days.</p>

<form id="f" novalidate>
<fieldset>
  <legend>What is this about?</legend>
  <div class="choices">
    <label><input type="radio" name="kind" value="new"> Suggest a new entry</label>
    <label><input type="radio" name="kind" value="correction"> Correct an existing entry</label>
    <label><input type="radio" name="kind" value="removal"> Request a removal</label>
    <label><input type="radio" name="kind" value="feedback"> Feedback on the map or the rules</label>
  </div>
</fieldset>

<div class="section" data-for="new">
  <fieldset><label class="q" for="n_name">Organization or project name</label><input type="text" id="n_name" data-req></fieldset>
  <fieldset><label class="q" for="n_url">Website</label><p class="hint">For companies, the page that describes the AI product. For open-source projects, the repository or model page.</p><input type="url" id="n_url" placeholder="https://" data-req></fieldset>
  <fieldset><label class="q" for="n_type">Type</label><select id="n_type" data-req><option value="">Choose one</option>{type_options}</select></fieldset>
  <fieldset><label class="q" for="n_sub">Where it belongs on the map <span class="optional">(optional)</span></label><select id="n_sub"><option value="">Not sure</option>{sub_options}</select></fieldset>
  <fieldset><label class="q" for="n_desc">What its AI does, in one sentence</label><p class="hint">200 characters maximum.</p><textarea id="n_desc" maxlength="200" data-req></textarea></fieldset>
  <fieldset><label class="q" for="n_ev">Evidence</label><p class="hint">Links that show it meets the criteria: the live product, the team in Lebanon or the Lebanese founder, publications, or the portfolio page.</p><textarea id="n_ev" data-req></textarea></fieldset>
  <fieldset><label class="check"><input type="checkbox" id="n_ai" data-req> <span>The product is AI software, not software, a service or a device that uses AI.</span></label></fieldset>
</div>

<div class="section" data-for="correction">
  <fieldset><label class="q" for="c_entry">Entry</label><select id="c_entry" data-req><option value="">Choose one</option>{entry_options}</select></fieldset>
  <fieldset><label class="q" for="c_what">What is wrong, and what should it say?</label><textarea id="c_what" data-req></textarea></fieldset>
  <fieldset><label class="q" for="c_src">Source that shows the correct information</label><input type="url" id="c_src" placeholder="https://" data-req></fieldset>
</div>

<div class="section" data-for="removal">
  <fieldset><label class="q" for="r_entry">Entry</label><select id="r_entry" data-req><option value="">Choose one</option>{entry_options}</select></fieldset>
  <fieldset><label class="q" for="r_why">Reason</label><textarea id="r_why" data-req></textarea></fieldset>
</div>

<div class="section" data-for="feedback">
  <fieldset><label class="q" for="g_text">Your feedback</label><textarea id="g_text" data-req></textarea></fieldset>
</div>

<div class="section" data-for="new correction removal">
  <fieldset><label class="q" for="rel">Your relationship to the organization</label><p class="hint">Maintainers never review entries for organizations they are tied to; we ask contributors the same question.</p><select id="rel" data-req><option value="">Choose one</option>{rel_options}</select></fieldset>
</div>

<div class="section" data-for="new correction removal feedback">
  <fieldset><label class="q" for="who">Your name <span class="optional">(optional)</span></label><input type="text" id="who"></fieldset>
  <fieldset><label class="q" for="mail">Your email <span class="optional">(optional, only if you want a reply)</span></label><input type="email" id="mail"></fieldset>
  <fieldset><label class="check"><input type="checkbox" id="credit"> <span>Credit me by name if this is used.</span></label></fieldset>
  <input type="checkbox" name="botcheck" id="botcheck" class="hp" tabindex="-1" autocomplete="off">
  <div class="actions">
    <button type="submit" id="send">Send</button>
    <button type="button" id="issue">Have a GitHub account? Open it as a public issue</button>
  </div>
</div>
<div id="status" role="status" aria-live="polite"></div>
</form>

<p class="privacy">Send forwards your message by email through Web3Forms, a third-party service. Your name and email are used only to reply and, if you ask, to credit you. They are never published. A maintainer records your suggestion as a public issue in the <a href="https://github.com/lebanon-ai-ecosystem/landscape">project repository</a> without your details, so every change stays on the public record. The public-issue route opens GitHub, where your GitHub account is shown.</p>
</main>

<footer>
  <div class="top">
    <a href="{base}" style="font-size:0"><img src="{base}images/footer-logo.svg" alt="Lebanon AI Ecosystem"></a>
    <a href="https://github.com/{repo}" target="_blank" rel="noopener noreferrer" aria-label="Project repository on GitHub"><svg viewBox="0 0 496 512" width="1em" height="1em" fill="currentColor"><use href="#gh"/></svg></a>
  </div>
  <hr>
  <div class="legend">Powered by <a href="https://github.com/cncf/landscape2" target="_blank" rel="noopener noreferrer">CNCF interactive landscapes generator</a>.</div>
</footer>

<script>
// Header: search hands the query to the Explore page; "/" focuses it; download menu.
(function () {{
  var q = document.getElementById("q");
  document.getElementById("search").addEventListener("submit", function (e) {{
    e.preventDefault();
    var v = q.value.trim();
    try {{ if (v) sessionStorage.setItem("lb-search", v); }} catch (err) {{}}
    location.href = "{base}";
  }});
  document.addEventListener("keydown", function (e) {{
    var t = e.target.tagName;
    if (e.key === "/" && t !== "INPUT" && t !== "TEXTAREA" && t !== "SELECT") {{ e.preventDefault(); q.focus(); }}
    if (e.key === "Escape") close();
  }});
  var dl = document.getElementById("dl"), btn = dl.querySelector("button");
  function close() {{ dl.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); }}
  btn.addEventListener("click", function (e) {{
    e.stopPropagation();
    var open = dl.classList.toggle("open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  }});
  document.addEventListener("click", function (e) {{ if (!dl.contains(e.target)) close(); }});
}})();
</script>

<script>
const CFG = {cfg};
const $ = id => document.getElementById(id);
const form = $("f"), status = $("status");
let kind = "";

function show() {{
  document.querySelectorAll(".section").forEach(s => s.classList.toggle("show", s.dataset.for.split(" ").includes(kind)));
}}
document.querySelectorAll('input[name=kind]').forEach(r => r.addEventListener("change", e => {{ kind = e.target.value; status.textContent = ""; show(); }}));
if (!CFG.key) {{
  $("send").disabled = true;
  $("send").title = "Email sending is not set up yet; use the GitHub route.";
}}

function visibleRequired() {{
  return [...document.querySelectorAll(".section.show [data-req]")];
}}
function valid() {{
  for (const el of visibleRequired()) {{
    const empty = el.type === "checkbox" ? !el.checked : !el.value.trim();
    if (empty) {{ el.focus(); status.textContent = "Please complete the highlighted field."; return false; }}
    if (el.type === "url" && !/^https?:\\/\\/\\S+$/.test(el.value.trim())) {{ el.focus(); status.textContent = "Please enter a full link starting with https://"; return false; }}
  }}
  return true;
}}

function answers() {{
  const v = id => $(id).value.trim();
  if (kind === "new") return {{
    request: CFG.requests[0], name: v("n_name"), homepage: v("n_url"), type: v("n_type"),
    subcategory: v("n_sub"), description: v("n_desc"), evidence: v("n_ev"), relationship: v("rel") }};
  if (kind === "correction") return {{
    request: CFG.requests[1], name: v("c_entry"), homepage: CFG.homepages[v("c_entry")] || "",
    description: v("c_what"), evidence: v("c_src"), relationship: v("rel") }};
  if (kind === "removal") return {{
    request: CFG.requests[2], name: v("r_entry"), homepage: CFG.homepages[v("r_entry")] || "",
    description: v("r_why"), evidence: "", relationship: v("rel") }};
  return {{ feedback: v("g_text") }};
}}

function issueUrl(a) {{
  const base = "https://github.com/" + CFG.repo + "/issues/new";
  if (kind === "feedback") {{
    const q = new URLSearchParams({{ title: "[Feedback] " + a.feedback.slice(0, 60), body: a.feedback }});
    return base + "?" + q.toString();
  }}
  const q = new URLSearchParams({{ template: "add-entry.yml", title: "[Entry] " + a.name }});
  for (const k of ["request", "name", "homepage", "type", "subcategory", "description", "evidence", "relationship"])
    if (a[k]) q.set(k, a[k]);
  return base + "?" + q.toString();
}}

$("issue").addEventListener("click", () => {{
  if (!kind) {{ status.textContent = "Choose what this is about first."; return; }}
  if (!valid()) return;
  window.open(issueUrl(answers()), "_blank", "noopener");
}});

form.addEventListener("submit", async e => {{
  e.preventDefault();
  if (!kind) {{ status.textContent = "Choose what this is about first."; return; }}
  if (!CFG.key || !valid()) return;
  const a = answers();
  const label = {{ new: "New entry", correction: "Correction", removal: "Removal request", feedback: "Feedback" }}[kind];
  const payload = {{
    access_key: CFG.key,
    subject: "[Lebanon AI Ecosystem] " + label + (a.name ? ": " + a.name : ""),
    from_name: $("who").value.trim() || "Lebanon AI Ecosystem feedback form",
    kind: label, ...Object.fromEntries(Object.entries(a).map(([k, v]) => [k === "name" ? "entry" : k, v])),
    sender_name: $("who").value.trim(), credit_by_name: $("credit").checked ? "yes" : "no",
    botcheck: $("botcheck").checked,
  }};
  if ($("mail").value.trim()) payload.email = $("mail").value.trim();
  $("send").disabled = true; status.textContent = "Sending...";
  try {{
    const r = await fetch("https://api.web3forms.com/submit", {{
      method: "POST", headers: {{ "Content-Type": "application/json", Accept: "application/json" }},
      body: JSON.stringify(payload) }});
    const j = await r.json();
    if (j.success) {{ form.reset(); kind = ""; show(); status.textContent = "Thank you. A maintainer will review it within 7 days."; }}
    else status.textContent = "Sending failed. Please try again, or use the GitHub route.";
  }} catch (err) {{
    status.textContent = "Sending failed. Please try again, or use the GitHub route.";
  }} finally {{ $("send").disabled = !CFG.key; }}
}});
</script>
</body></html>
"""

if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
