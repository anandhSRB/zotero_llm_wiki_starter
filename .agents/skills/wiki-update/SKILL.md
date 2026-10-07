---
name: wiki-update
description: Integrate newly synced or previously uncategorized sources into topics/, file every topic page under one of the established domains, normalise the tag scheme, and cross-link related topics. Use when asked to update, sync or refresh the wiki after adding references to the library. For a first build from an empty topics/, use wiki-bootstrap instead.
---

# wiki-update

The routine ingest loop. Read `AGENTS.md` first.

## When this applies

`topics/` already has a domain structure, and new sources have appeared.
If `topics/` is empty, use `wiki-bootstrap` to establish the domains
first.

## The domain list is fixed

The domain pages (`tags: [domain]`, no `parent`) are the established
top-level structure, agreed with the user at bootstrap. **Do not invent a
new domain in this skill, and do not quietly retire one.** New material
goes into a new *topic* under an existing domain.

If material genuinely fits no domain, that is a signal worth raising —
report it as an observation and let the user decide whether the domain
list should change. Changing it is a deliberate, separate conversation.

Read the current list before starting; do not assume it from memory.
`AGENTS.md` names them under `### The domains in this vault` — that is
what "do not invent a new domain" is checked against. Then confirm
against the vault itself, which is authoritative if the two disagree:

```bash
grep -l 'tags: \[domain\]' topics/*.md
```

If they disagree, say so: either `AGENTS.md` has fallen behind a domain
page, or a domain page was added without being recorded. Both are worth
raising rather than silently picking one.

For a page that could fit two domains, **read its actual content** rather
than guessing from the filename, and pick the one its core content is
really about.

## The tag scheme

Mutually exclusive — exactly one on every page in the hierarchy, and it
follows from two structural facts: does the page have a `parent`, and
does it have its own `## Sub-topics` section?

| tags | has `parent` | has `## Sub-topics` |
|---|---|---|
| `[domain]` | no | yes |
| `[hub]` | yes | yes |
| `[topic]` | yes | no |

`uncategorized.md` is a staging file, not part of the hierarchy, and
carries neither.

---

## Steps

### 1. Check the structure is intact

Confirm every domain page exists and that `topics/_index.base` is
present. **Create `_index.base` only if missing; never overwrite an
existing one** — it holds view customisations the user may have made
through Obsidian's Bases UI.

### 2. Normalise tags

For every page in `topics/` except the staging files, check its `tags`
against the table above, judged by whether it has a `parent` and a
`## Sub-topics` section, and fix any mismatch.

**Change only the `tags` field. Leave everything else byte-for-byte**
(rule 2). This is a no-op once things are correct, so it is safe to run
every time.

### 3. Classify the backlog

Any page other than a domain or staging file that still lacks a `parent`:
read it, set `parent: "<domain-slug>"`, set `tags` per the table, and add
it as a `[[link]]` under that domain's `## Sub-topics` — editing that
section in place.

Run the cross-link check (step 7) for each page classified here, exactly
as for newly touched pages. **This is how an existing backlog gets
linked, not just today's new content.**

### 4. Build the worklist

```bash
python3 scripts/wiki_lint.py
python3 scripts/wiki_digest.py --orphaned --chars 400
```

The **ORPHANED** list is the worklist. Combine it with anything listed in
`topics/uncategorized.md` and treat the whole set as live: **a source
that did not cluster last time may cluster with today's arrivals.**

Fix any genuine *problem* the lint reports before adding material. If the
problem is in `sources/`, flag it and stop (rule 1).

### 5. Read each source — one at a time, writing as you go

Frontmatter, `## Abstract`, `## Notes`, and the embedded PDF where
`has_pdf` is true. Where it is false, work from the abstract and **say on
the page that it is abstract-only** rather than inferring detail.

**Write each source's findings to its page before opening the next one**,
and mark it in that page's `## Sources`:

```markdown
- [[citekey]] — deep read 2026-10-07
- [[citekey]] — abstract only (no PDF)
```

See `AGENTS.md` → **Checkpointing**. A deep read held only in context is
lost when the session ends; one written down is not. Resume an interrupted
run with:

```bash
python3 scripts/wiki_digest.py --topic <slug> --chars 0
```

which prints exactly which sources on that page are still unexamined.

### 6. Decide, per source

**(a) Fits an existing topic.** Integrate its findings into
`## What the literature says` alongside what is there — **never rewrite
the page** (rule 2). Add its `[[citekey]]` to `## Sources` **with a read
marker**, set `last_updated`, and write all of that before moving to the
next source. Remove it from `uncategorized.md` once integrated.

If the page was `drafted` or `linked`, it stays so — adding a marked
source does not demote it. Only a page with *unmarked* sources is `stub`.

If it *disagrees* with what the page says, keep both and attribute each
side. A newer paper is not automatically right.

**(b) Fits more than one topic.** Expected, not a problem. Add it to each
page, citing it **for the part relevant there**. Never paste the same
paragraph twice.

**(c) Fits no existing topic.** Look for clusters among what is left —
2+ sources sharing a real theme. **Do not create the page yourself**
(rule 3). List each candidate cluster: name (2–4 words; see `AGENTS.md`
→ Naming topics), one-line rationale, citekeys, and which domain it would
sit under. Then stop and wait.

**(d) Fits nothing and does not cluster.** Leave it. An orphan is the
correct state for undecided material — it stays visible in the lint.

### 7. Create approved pages

From `templates/topic-page.md`, with `parent` and `tags: [topic]` already
set, and add each as a `[[link]]` under its domain's `## Sub-topics`.

### 8. Cross-link

For every page created, edited or newly classified this run, check for a
**substantive dependency** with another topic — shared citekeys, or one
page's mechanism or model being applied or evaluated by the other.

The bar is "a reader of one page would genuinely want to jump to the
other", not "both touch the same broad subject". Where it is met, add a
`## Cross-links` entry on **both** pages if not already there, in prose
naming what the relationship is.

Cross-links may cross domain boundaries. That is expected, not an error.

### 9. Update the staging file

Rewrite `topics/uncategorized.md`: drop anything integrated, keep what is
still unclustered, and add or update a **"Proposed clusters (pending
approval)"** section for this run's candidates, each with its proposed
domain — **so nothing is lost if the user does not act immediately.**

### 10. Never touch `sources/`

Including `sources/_index.base` (rule 1).

### 11. Verify and report

```bash
python3 scripts/wiki_lint.py
```

Report: tags normalised, pages classified under a domain for the first
time, topic pages edited and with which citekeys, new topics created and
their domain, cross-links added and why, sources multi-homed, clusters
awaiting approval, what remains in `uncategorized.md`, and anything
marked "needs a closer read".

Never claim the lint is clean without running it.
