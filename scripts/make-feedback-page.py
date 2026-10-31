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
map. The site header (EXPLORE, GUIDE, STATS, FEEDBACK) is redrawn here because
this page sits outside the landscape2 app.

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
header{{display:flex;align-items:center;gap:56px;padding:14px 28px;border-bottom:1px solid #e5e5e5;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
header img{{height:32px;display:block}}
nav{{display:flex;gap:34px;flex-wrap:wrap}}
nav a{{color:#007A48;text-decoration:none;text-transform:uppercase;font-weight:700;letter-spacing:.15em;font-size:18px;padding-bottom:4px}}
nav a.on{{border-bottom:3px solid #007A48}}
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
@media (max-width:640px){{header{{flex-direction:column;align-items:flex-start;gap:12px}} nav{{gap:18px}} nav a{{font-size:15px}}}}
</style></head>
<body>
<header>
  <a href="{base}"><img src="{base}images/header-logo.svg" alt="Lebanon AI Ecosystem"></a>
  <nav><a href="{base}">Explore</a><a href="{base}guide">Guide</a><a href="{base}stats">Stats</a><a class="on" href="{base}feedback/">Feedback</a></nav>
</header>
<main>
<h1>Feedback</h1>
<p class="lede">Suggest an organization or project, correct an entry, ask for a removal, or tell us what to improve. Every suggestion is reviewed against the published <a href="{base}guide">listing rules</a>, and maintainers answer within 7 days.</p>

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
  <div id="status" role="status" aria-live="polite"></div>
</div>
</form>

<p class="privacy">Send forwards your message by email through Web3Forms, a third-party service. Your name and email are used only to reply and, if you ask, to credit you. They are never published. A maintainer records your suggestion as a public issue in the <a href="https://github.com/lebanon-ai-ecosystem/landscape">project repository</a> without your details, so every change stays on the public record. The public-issue route opens GitHub, where your GitHub account is shown.</p>
</main>

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
