---
name: wiki-restructure
description: Review topics/ for pages that have grown too broad to read easily or that substantially overlap each other, and propose splitting them into hub plus sub-topic pages, merging them, or just cross-linking. Use when asked to restructure, reorganise, split up, tidy or reconcile the topics. Proposes everything first and changes nothing without explicit per-item approval.
---

# wiki-restructure

Maintenance on the *shape* of the wiki, not its content. Read
`AGENTS.md` first.

Reviews every page in `topics/` except the staging files
(`uncategorized.md`) for two problems: pages that have grown too broad
for one readable page, and pages that substantially overlap.

**Domain pages (`tags: [domain]`) are never split or merged here.** They
are the fixed top-level structure agreed at bootstrap. If a domain looks
too broad, say so as an observation in your final report — changing the
domain list is a deliberate, separate decision with the user, outside
this skill's scope.

---

## Phase 1 — Propose, then stop

For each `topic` or `hub` page (domain pages may be read for context but
are not candidates), note:

- its length and how many `[[citekey]]` sources it cites,
- whether `## What the literature says` is genuinely one narrative or is
  quietly covering two or more distinct sub-themes.

### SPLIT candidates

A page covering 2+ sub-themes where **each sub-theme has roughly 3+ of
its sources behind it**. Do not split off a sub-theme backed by only one
or two sources — that produces a page too thin to be worth opening.

### OVERLAP candidates

Two or more pages restating the same material or citing mostly the same
sources. For each, propose either:

- a **MERGE**, if they are really one topic, or
- **cross-links only**, if they are distinct but adjacent.

If the pages have different `parent` domains, **say so explicitly**. That
is either a sign one was misclassified, or a sign they are related but
not the same topic — in which case a cross-link is the better fit than a
merge. Do not quietly reassign a domain as part of a merge.

### Present the plan and STOP

Do not create, split or merge anything yet:

- **Splits** — hub name, proposed sub-topic names (2–4 words each), which
  citekeys go to each, one-line rationale.
- **Merges** — which pages, which survives (or a new combined name),
  one-line rationale.
- **Cross-link only** — which pages, one-line rationale.

**Wait for explicit approval on each item.** Approval of one split is not
approval of the others; the user may well take some and reject others.

---

## Phase 2 — Execute only what was approved

### An approved SPLIT

1. Create one child page per sub-theme from `templates/topic-page.md`,
   with `parent:` set to the **original page's own parent** and
   `tags: [topic]`.
2. Turn the original page into a hub: a short Overview of the broader
   theme, then `## Sub-topics` linking each child with a one-line
   description. **Keep its existing `parent` unchanged** — it still
   belongs to the same domain — and set `tags: [hub]`.
3. **Every citekey the original page cited must end up cited by exactly
   one child**, or by the hub itself if genuinely relevant to all of
   them. None may be dropped. This is the check that matters most: a
   dropped citation turns a processed source back into an orphan and
   loses the synthesis that was written about it.
4. Carry the *prose* across, do not re-derive it. The original wording
   may have been hand-edited; move it, do not rewrite it.

### An approved MERGE

1. Combine into the surviving page, **integrating rather than
   concatenating** — resolve redundant restatement, keep every citekey
   from both.
2. Keep the surviving page's original `parent` unless the approval said
   otherwise.
3. Replace the page that did not survive with a short stub: one line
   saying it was merged, and a `[[link]]` to the survivor. **Do not
   delete the file** — anything still linking to the old name would
   break silently, and outside this vault (your notes, a paper draft)
   you cannot see what links to it.

### An approved cross-link-only pair

Add a `## Cross-links` entry naming the other page on **both** sides,
in prose: `overlaps with [[other]], which covers the X side`. Do not move
or duplicate content between them.

---

## Finishing

Set `last_updated` on every page you created or edited. Never touch
`sources/` (rule 1).

```bash
python3 scripts/wiki_lint.py
```

Confirm specifically:

- **no broken links** — a merge stub still resolves, so links to the old
  name keep working,
- **no source went from cited to orphaned.** Compare the orphan count
  before and after: a rise means a citation was dropped in the reshuffle.
  Find it rather than reporting the new number.
- `by_tag` counts moved as expected — a split turns one `topic` into one
  `hub` plus N `topic`s.

Report what was split, merged and cross-linked, and why; anything
proposed but not approved, so it is not silently lost; and any domain
page you think is too broad, as an observation only.
