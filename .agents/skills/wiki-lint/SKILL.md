---
name: wiki-lint
description: Run the read-only integrity check over the vault and report what it finds, grouped by type — broken wikilinks, malformed frontmatter, missing or dangling parent links, has_pdf mismatches, duplicate note names, unknown status values, orphaned sources, overlong slugs. Use when asked to lint, check or validate the wiki. Reports by default and fixes nothing unless separately asked.
---

# wiki-lint

```bash
python3 scripts/wiki_lint.py            # report
python3 scripts/wiki_lint.py --json     # machine-readable
python3 scripts/wiki_lint.py --quiet    # problems only
python3 scripts/wiki_lint.py --ignore-orphans   # do not fail on orphans
```

`--ignore-orphans` still *reports* the orphan count but keeps it out of the
exit code. It exists for pre-commit hooks and CI, where unprocessed
material is the normal state and only real breakage should block. Do not
use it to make a report look clean.

Read-only and stdlib-only; safe to run as often as you like. Exit 0 means
no problems.

## Report; do not fix unless asked

**Default behaviour is to report, not repair.** Group findings by type
rather than repeating the raw list, and say which would need changes
under `topics/` versus `sources/`. Then stop.

Fix something only when the user asks for it separately. Read `AGENTS.md`
before any fix, and make the **smallest edit** that resolves it —
integrate, never rewrite a page to fix a one-line link (rule 2). A
whole-file rewrite to repair a typo is how hand-written synthesis gets
destroyed.

Two things are never fixed, whoever asks:
- anything under `sources/` — those are adapter bugs (rule 1),
- an orphan "resolved" by inventing a topic (rule 3).

## Problems vs warnings vs progress

- **Problems** — broken. Exit 1.
- **Warnings** — style, chiefly overlong slugs and missing `status`.
  **Never auto-fix a slug**: renaming a page breaks every `[[link]]` to
  it, including from outside the vault. Mention it; the user decides.
- **Progress** — counts of sources, topic pages by tag and status,
  orphans, multi-homed sources. Not a failure. An unfinished wiki is not
  a broken one, and `by_status` tells you how much of a build remains.

## How to read each problem

**BROKEN LINK: `page` → `[[target]]`**
- Target looks like a citekey → the source is not in `sources/`: never
  synced, or renamed by the reference manager. **Do not create the source
  note** (rule 1). Report it; the user fixes it in their library.
- Target looks like a topic slug → a typo, or a renamed page. Check
  whether other pages point at the same stale slug.
- Target ends `.pdf` → a source note's embed points at a missing file.
  That is in `sources/`: flag as a sync issue. Commonly it means the
  vault was copied between machines without the PDFs.

**MISSING / AMBIGUOUS topic tag** — the page has no `tags` entry from
`domain | hub | topic`, or several. It follows from structure: has a
`parent`? has its own `## Sub-topics`? See the table in `wiki-update`.

**MISSING parent / PARENT NOT FOUND** — set it to the domain or hub whose
`## Sub-topics` actually links this page. If nothing links to it, that is
the real problem — an unreachable page. Say so.

**UNKNOWN status** — must be `stub`, `drafted` or `linked`. Do not mark a
page `linked` because it looks finished; check it has real
`## Cross-links` content.

**MISSING citekey / citekey-filename MISMATCH / MISSING title / has_pdf
mismatch** — all under `sources/`. Report as adapter bugs with the file
names, and stop (rule 1).

**DUPLICATE NAME** — two notes share a stem, so `[[stem]]` resolves
ambiguously. Usually a topic page accidentally named after a citekey.
Rename the *topic* page, never the source, and update every link to it.

**ORPHANED** — sources no topic page cites: unprocessed material, not a
defect. Hand off to `wiki-update`, or just list them if the user asked
only for a health check. Cross-check `topics/uncategorized.md`, which
records why anything there is still waiting.

## Reporting

Give the problem count by type, the progress counts, and — if you were
asked to fix — before/after counts plus what you deliberately left,
especially slug warnings.
