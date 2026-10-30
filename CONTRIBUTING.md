# Contributing

Listing is free and follows the criteria below. Nobody pays for placement, and the same rules apply to every organization, including those the maintainers work for.

## Three ways to submit

1. **Pull request.** Add your entry to `data.yml`. No logo file is needed.
2. **Issue form.** Open a new issue with the "Add or update an entry" form. A maintainer turns it into a pull request.
3. **Web form.** For contributors without a GitHub account: FORM_URL_TBD.

Every change, from any route, lands as a reviewed commit.

## Who qualifies

| Entity type | Qualifies when | Evidence we need |
| --- | --- | --- |
| Company in Lebanon | AI is core to a live product or service customers can use today; headquartered in Lebanon or runs a working team there (at least TEAM_FLOOR_TBD full-time people) | Public product page; Lebanese registration or a team visible on public profiles |
| Diaspora company | Same product bar; at least one Lebanese founder or co-founder; headquarters and team abroad | Public product page; founder's public profile |
| Research | University lab or research center with AI research output in the last 24 months | Publications, funded projects, or released code |
| Investor | At least one investment in an AI company that qualifies above | Portfolio page or announcement |
| Accelerator or incubator | At least one AI company in a cohort in the last 24 months | Cohort page or announcement |
| Community or nonprofit | AI events or programs held in the last 12 months | Event pages or posts |
| Government body | A formal AI mandate or program | Official page or decree |

**Out of scope:** agencies and consultancies selling AI services without a product, resellers of foreign AI tools, companies in stealth, and organizations with no visible activity in 12 months.

## Entry format

```yaml
- name: "Example Co"
  description: "One plain sentence on what the product does. 200 characters maximum."
  homepage_url: https://example.com
  logo: example-co.svg     # file name only; the image is generated from the name
  # Optional: show the entry in a second subcategory too.
  # second_path:
  #   - "Applied AI / Health and life sciences"
  extra:
    linkedin_url: https://www.linkedin.com/company/example-co
    annotations:
      presence: hq            # hq | team | diaspora
      city: "Beirut"
      founded: "2021"
      verified_by: entity     # entity | public-sources | pending
      verified_on: "2026-12-01"
```

Place the entry in the one subcategory that best describes what the product does, not who buys it. Keep entries in alphabetical order within a subcategory.

## Names, not logos

The landscape shows no organization logos. Every entry appears as its name, in black Inter SemiBold, so no organization stands out because of its branding and no trademark is reproduced.

- Set `logo` to the organization's name in lowercase with hyphens (`example-co.svg`). The build generates that file from `name`; do not add files to `logos/`.
- All names share one type size: the size the longest name needs to fit. A new long name can make every name a little smaller. If a name would push the size below a readable minimum, the build fails and asks for a shorter display name, such as the name the organization uses on its own site.
- `name` is the display name. Use the organization's own spelling and capitalization.

## Verification and review

- Each entry is confirmed by the organization or by two independent public sources before it goes live.
- Adding, moving, or removing an entry needs approval from two maintainers.
- A maintainer never approves changes to an organization they work for, advise, or invest in.

## Corrections and removals

Use the issue form or email CONTACT_EMAIL_TBD. Maintainers answer within 7 days and record the decision in the issue.
