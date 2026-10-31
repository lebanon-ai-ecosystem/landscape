# Maintaining the landscape

How to change the Lebanon AI Ecosystem landscape, from fixing one entry to reshaping the map. For adding an organization, see [CONTRIBUTING.md](CONTRIBUTING.md); for building locally, see [README.md](README.md).

## How a change goes live

Every change merged into `main` publishes itself. The "Build and deploy" workflow validates the files, builds the site, applies category colors, and deploys to GitHub Pages in about 2 minutes. It also rebuilds nightly at 03:17 UTC.

Pull requests are validated and built but not deployed, so a broken file shows up as a red check on the PR before it can reach the site. If a build fails after merging, the previous version of the site stays up.

Check progress in the repository's Actions tab.

## Two ways to edit

**In the browser (no setup).** Open the file on GitHub, click the pencil icon, edit, then click "Commit changes" and choose "Create a new branch for this commit and start a pull request". Good for entries, descriptions, guide text, and colors.

**On your computer.** Clone the repository, create a branch, edit, preview locally (README.md, "Build locally"), push, and open a pull request. Better for structural changes, because you can see the result before anyone reviews it.

Either way, every change lands through a reviewed pull request.

## Which files to touch

Names must match exactly across files, including capitalization and punctuation. Most structural mistakes come from renaming something in one file and not the others.

| Change | Files |
| --- | --- |
| Add, update, or remove an entry | `data.yml` only; the logo is generated from the name |
| Move an entry to another subcategory | `data.yml` (move the whole block) |
| List an entry in a second subcategory | `data.yml` (`second_path` on the entry) |
| Add a subcategory | `data.yml`; optionally `guide.yml` |
| Rename a subcategory | `data.yml`; `guide.yml`; any `second_path` that points to it |
| Add a category | `data.yml`; `settings.yml` (`groups`); `category-colors.json`; `scripts/make-slide.py` (`COLUMNS`); optionally `guide.yml` |
| Rename a category | `data.yml`; `settings.yml` (`groups`); `category-colors.json`; `scripts/make-slide.py` (`COLUMNS`); `guide.yml`; any `second_path` that points to it |
| Remove a category or subcategory | Same files as renaming; move or remove its entries first |
| Change a category's color | `category-colors.json` |
| Change site colors (buttons, links, fallback category colors) | `settings.yml` (`colors`, all seven required) |
| Change the views (Full landscape, AI stack, and so on) | `settings.yml` (`groups`) |
| Edit the Guide page | `guide.yml` |
| Change the project name or header logo | `settings.yml` (`foundation`, `description`); `assets/header-logo.svg` and `assets/footer-logo.svg`; `guide.yml` introduction; README.md |
| Change the favicon or link-preview image | Commit the new file in `assets/` first; then point `images` in `settings.yml` at that commit (the comment there explains why) |
| Move to a custom domain | `settings.yml` (set `url`, delete `base_path`, and update the absolute links in `header.motd` and `footer.text`); then Settings, Pages, Custom domain |
| Change the Feedback page or its settings | `scripts/make-feedback-page.py`; `feedback.yml` |
| Change the introduction above the map, tile styling, the item facts line, or the guide's empty-section notes | `scripts/polish-site.py` |
| Show or hide menu items (STATS is hidden, FEEDBACK added) | `scripts/add-feedback-menu.py` |
| Change or remove the banner above the header | `settings.yml` (`header.motd`); the Feedback page mirrors it |
| Change the footer text | `settings.yml` (`footer.text`); the Feedback page mirrors it |
| Turn the visit counter on or off | `counter.yml` (`goatcounter_code`; empty means off) |
| Change the 16:9 slide layout (which category goes in which column) | `scripts/make-slide.py` (`COLUMNS`) |
| Upgrade landscape2 | `.github/workflows/build.yml` (`LANDSCAPE2_VERSION`) |

## Rules worth knowing

**The 16:9 slide is rebuilt on every deploy.** The build lays the whole map out on one 1920x1080 slide in three columns and publishes it as `downloads/lebanon-ai-ecosystem-slide.png` and `.pdf`, and as `docs/landscape.png` and `.pdf`, which the download menu in the site header serves. Without those two files the menu spins forever. It picks the largest name tile that fits (112px today). If entries no longer fit at 60px, the build fails and asks for a change to `COLUMNS` in `scripts/make-slide.py`. A category missing from `COLUMNS` also fails the build.

**A category must belong to at least one view.** A category in `data.yml` that is not listed under any group in `settings.yml` builds without error but never appears on the map. Add new categories to "Full landscape" and to the view they belong to.

**Empty subcategories disappear.** A subcategory with no entries is valid and is hidden from the map automatically. Placeholder entries exist only so the scaffold shows every box; delete them freely.

**Every category needs a color.** A category missing from `category-colors.json` falls back to the two default colors in `settings.yml` and will look out of place. Pick a color that keeps white text readable: a contrast ratio of at least 4.5:1, which any online contrast checker will confirm.

**The `second_path` format** is `"Category / Subcategory"`, and neither name may contain a slash.

**Guide headings** inside a content block use levels 4 to 6 (`####`); levels 1 to 3 are reserved for the category structure.

**Upgrading landscape2** may break the category color step, which patches the generated code. The build then fails with "landscape2 output changed" instead of publishing a half-colored site. Build the new version locally first, and update `scripts/apply-category-colors.py` if needed. `scripts/polish-site.py` and `scripts/add-feedback-menu.py` depend on landscape2 class names in the same way and fail the build the same way.

## Before merging a pull request

- The "build" check is green.
- Every new or renamed name matches across all files in the table above.
- Each new entry meets the inclusion criteria and has its evidence in the PR or linked issue.
- Each new entry passes the three listing rules in CONTRIBUTING.md: high or medium confidence, a homepage you opened, and the product is AI software, not software, a service or a device that uses AI (no consultancies).
- No files were added to `logos/` (they are generated; see CONTRIBUTING.md, "Names, not logos").
- A second maintainer approved it, and neither approver works for, advises, or invests in the organization concerned.

## Automations

Three workflows besides "Build and deploy" run on their own. Each is a file in `.github/workflows/`.

**Issue to pull request** (`issue-to-pr.yml`). Add the `approved` label to an "Add or update an entry" issue for a new entry and the workflow adds the entry to `data.yml` in its subcategory, in alphabetical order, validates it, and opens a pull request that closes the issue. It sets `confidence: medium` and `verified_by: public-sources`; adjust them in the pull request if needed. If the issue cannot be converted (unknown subcategory, description over 200 characters, name already listed), the workflow explains why in the issue and removes the label; fix the issue and add the label again. Corrections and removals stay manual.

Pull requests opened by a workflow do not start other workflows, so the "build" check does not run on its own. Close and reopen the pull request to start it. If the workflow pushes the branch but cannot open the pull request, turn on Settings, Actions, General, "Allow GitHub Actions to create and approve pull requests".

**Website check** (`website-check.yml`). Every Monday it opens every homepage on the map and keeps one issue, labeled `website-check`, listing the ones that failed. "Broken" means the site did not load after three tries: fix the URL or remove the entry (listing rule 2). "Check by hand" means the site turned the check away, usually bot protection; open it in a browser. The issue closes itself when everything loads. Run it any time from the Actions tab.

**Conduct concern** (`conduct.yml`). An issue labeled `coc`, or any issue with "CoC" in its title, is assigned to the maintainers in `CONDUCT_MAINTAINERS`, acknowledged and locked. Then:

1. Within 3 days, contact the reporter the way they chose on the form. For a private repository, create one in the organization named `conduct-<issue number>`, set it to private, and invite only the reporter and the maintainers handling the report.
2. If the reporter put details in the public issue, edit them out.
3. Close the public issue once the private conversation has started.
4. Do not handle a report you are involved in, or that concerns an organization you work for, advise or invest in. Hand it to another maintainer.
5. Delete the private repository when the report is closed, unless the reporter asks to keep it.

## Feedback page submissions

The Feedback page (`feedback/`, built by `scripts/make-feedback-page.py`) sends each submission by email through Web3Forms to the project inbox, or opens a prefilled GitHub issue for people with an account.

For each emailed submission, within 7 days:

1. Open a public issue with its content, using the "Add or update an entry" form for entries and a blank issue for general feedback. Leave out the sender's name and email. Credit the sender by name only if they ticked "Credit me by name".
2. Add the `from-form` label, then review it like any other issue.
3. If the sender left an email, reply with the issue link.

Settings live in `feedback.yml`. The Web3Forms access key there is public by design: it only lets the form send to the project inbox. While the key is empty, the page offers the GitHub route only. The free Web3Forms plan allows 250 submissions a month and keeps 30 days of history.

## Undoing a change

Open the merged pull request on GitHub and click "Revert". That creates a new pull request that reverses it; merge it and the site rebuilds. On the command line, `git revert <commit>` does the same.
