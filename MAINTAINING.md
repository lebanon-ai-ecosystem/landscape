# Maintaining the landscape

How to change the Lebanon AI Ecosystem landscape, from fixing one entry to reshaping the map. For adding an organization, see [CONTRIBUTING.md](CONTRIBUTING.md); for building locally, see [README.md](README.md).

## How a change goes live

Every change merged into `main` publishes itself. The "Build and deploy" workflow validates the files, builds the site, applies category colors, and deploys to GitHub Pages in about 2 minutes. It also rebuilds nightly at 03:17 UTC.

Pull requests are validated and built but not deployed, so a broken file shows up as a red check on the PR before it can reach the site. If a build fails after merging, the previous version of the site stays up.

Check progress in the repository's Actions tab.

## Two ways to edit

**In the browser (no setup).** Open the file on GitHub, click the pencil icon, edit, then click "Commit changes" and choose "Create a new branch for this commit and start a pull request". Good for entries, descriptions, guide text, and colors.

**On your computer.** Clone the repository, create a branch, edit, preview locally (README.md, "Build locally"), push, and open a pull request. Better for structural changes and logos, because you can see the result before anyone reviews it.

Either way, every change lands through a reviewed pull request.

## Which files to touch

Names must match exactly across files, including capitalization and punctuation. Most structural mistakes come from renaming something in one file and not the others.

| Change | Files |
| --- | --- |
| Add, update, or remove an entry | `data.yml`; its SVG in `logos/` |
| Move an entry to another subcategory | `data.yml` (move the whole block) |
| List an entry in a second subcategory | `data.yml` (`second_path` on the entry) |
| Add a subcategory | `data.yml`; optionally `guide.yml` |
| Rename a subcategory | `data.yml`; `guide.yml`; any `second_path` that points to it |
| Add a category | `data.yml`; `settings.yml` (`groups`); `category-colors.json`; optionally `guide.yml` |
| Rename a category | `data.yml`; `settings.yml` (`groups`); `category-colors.json`; `guide.yml`; any `second_path` that points to it |
| Remove a category or subcategory | Same files as renaming; move or remove its entries first |
| Change a category's color | `category-colors.json` |
| Change site colors (buttons, links, fallback category colors) | `settings.yml` (`colors`, all seven required) |
| Change the views (Full landscape, AI stack, and so on) | `settings.yml` (`groups`) |
| Edit the Guide page | `guide.yml` |
| Change the project name or header logo | `settings.yml` (`foundation`, `description`); `assets/header-logo.svg` and `assets/footer-logo.svg`; `guide.yml` introduction; README.md |
| Change the favicon or link-preview image | Commit the new file in `assets/` first; then point `images` in `settings.yml` at that commit (the comment there explains why) |
| Move to a custom domain | `settings.yml` (set `url`, delete `base_path`); then Settings, Pages, Custom domain |
| Upgrade landscape2 | `.github/workflows/build.yml` (`LANDSCAPE2_VERSION`) |

## Rules worth knowing

**A category must belong to at least one view.** A category in `data.yml` that is not listed under any group in `settings.yml` builds without error but never appears on the map. Add new categories to "Full landscape" and to the view they belong to.

**Empty subcategories disappear.** A subcategory with no entries is valid and is hidden from the map automatically. Placeholder entries exist only so the scaffold shows every box; delete them freely.

**Every category needs a color.** A category missing from `category-colors.json` falls back to the two default colors in `settings.yml` and will look out of place. Pick a color that keeps white text readable: a contrast ratio of at least 4.5:1, which any online contrast checker will confirm.

**The `second_path` format** is `"Category / Subcategory"`, and neither name may contain a slash.

**Guide headings** inside a content block use levels 4 to 6 (`####`); levels 1 to 3 are reserved for the category structure.

**Upgrading landscape2** may break the category color step, which patches the generated code. The build then fails with "landscape2 output changed" instead of publishing a half-colored site. Build the new version locally first, and update `scripts/apply-category-colors.py` if needed.

## Before merging a pull request

- The "build" check is green.
- Every new or renamed name matches across all files in the table above.
- Each new entry meets the inclusion criteria and has its evidence in the PR or linked issue.
- Each new entry has an SVG logo supplied or approved by the organization.
- A second maintainer approved it, and neither approver works for, advises, or invests in the organization concerned.

## Undoing a change

Open the merged pull request on GitHub and click "Revert". That creates a new pull request that reverses it; merge it and the site rebuilds. On the command line, `git revert <commit>` does the same.
