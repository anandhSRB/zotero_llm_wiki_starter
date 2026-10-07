# LLM Wiki — starter kit

A two-layer research wiki for Obsidian that an AI agent can maintain
with you, built so that **every claim traces back to a source you
actually have**.

Field-agnostic: the structure comes from your library, not from this kit.
It works the same for fluid dynamics, machine learning, medicine
or anything else.

```
sources/   RAW   — one note per reference. Machine-generated. Never hand-edited.
topics/    WIKI  — concept pages synthesising the sources. Every claim cited [[citekey]].
```

The split is the whole idea. `sources/` is a faithful, disposable mirror
of your reference manager — regenerate it any time. `topics/` is the part
with value in it, and it is auditable: if a sentence has no `[[citekey]]`,
it does not belong.

## Why two layers

Pointing an agent at 400 PDFs and asking a question gets you a plausible
answer you cannot check. This kit makes the agent build a **citable
intermediate layer** first. Afterwards:

- every statement names the paper it came from, so you can verify it,
- disagreements between papers are recorded rather than averaged away,
- gaps are explicit — "needs a closer read" is a valid, useful answer,
- the next session resumes from structure instead of re-reading the library.

## Requirements

- **Python 3.9+** — nothing to install. Every script is stdlib-only.
- **Obsidian 1.9+** — optional, for reading the vault and the `.base`
  index views (Bases is core from 1.9, no plugin needed).
- **An AI coding agent** — Claude Code, Cursor, Codex, Copilot, Gemini
  CLI, Aider. See [`.agents/skills/README.md`](.agents/skills/README.md).
- **A reference manager** — optional. Zotero works out of the box; you
  can also add sources by hand.

## Quickstart

### 1. Get the files

Copy this folder to wherever you keep the vault, then open it in
Obsidian ("Open folder as vault") and in your agent.

```bash
cd llm-wiki-starter
python3 scripts/wiki_lint.py          # expect: No problems found.
```

No paths to edit. The scripts locate the vault from their own location,
so a fresh copy works immediately.

### 2. Fill `sources/`

**With Zotero** — install the Better BibTeX plugin, right-click your
library → *Export Library…* → format **Better CSL JSON** → tick **Keep
updated** → save it somewhere. Enable *Settings → Advanced → Allow other
applications on this computer to communicate with Zotero*. Then:

```bash
cp wiki.config.example.json wiki.config.json   # point it at that export
python3 scripts/zotero_sync.py --once          # or omit --once to keep watching
```

**Without a reference manager** — add sources directly:

```bash
python3 scripts/new_source.py --title "Attention Is All You Need" \
    --authors "Ashish Vaswani, Noam Shazeer" --year 2017 --pdf ~/Downloads/paper.pdf

python3 scripts/new_source.py --adopt   # stub notes for PDFs already in sources/
```

Both paths write the same frontmatter, so everything downstream treats
them identically. `scripts/zotero_sync.py` documents how to write an
adapter for another manager — it is about 80 lines of work.

### 3. Build the wiki layer

Ask your agent:

> Read AGENTS.md, then run the wiki-bootstrap skill.

It will, in order:

1. **ask you what your main domains are** — it will not guess,
2. **skim** the sources (abstracts only, no PDFs) and propose concise
   topics, then wait for your approval,
3. create the approved pages, then **deep-read** the PDFs to fill them,
   writing each source's findings down before opening the next one,
4. **cross-link** topics and place sources that belong in more than one.

The gates are deliberate. Approving a topic list takes a minute; undoing
a structure built on a wrong guess takes an afternoon.

### If the agent stops midway

**Expect this on a real library.** Step 3's deep-read phase is the long
part — hundreds of PDFs — and an agent will usually hit its context or
token limit before finishing. That is normal, not a failure, and the build
is designed to survive it.

**What is protected.** The agent writes each source's findings to the page
and marks that source *before* opening the next one. So an interruption
costs at most the one source in flight — never the twelve already read.
Everything else is on disk.

**How to resume.** Start a fresh session and say:

> Read AGENTS.md, then continue the wiki-bootstrap deep read.

(Or `...continue the wiki-update`, if that is what was interrupted.)

It does not need the old conversation. Both levels of progress are stored
in the files themselves:

- **Which pages are done** — each page's `status`: `stub` → `drafted` →
  `linked`. Obsidian's *Needs filling* and *Needs linking* views in
  `topics/_index.base` list them directly.
- **Which sources within a page are done** — annotations in that page's
  `## Sources`:

```markdown
- [[citekeyA]] — deep read 2026-10-07
- [[citekeyB]] — abstract only (no PDF)
- [[citekeyC]]                              ← not read yet
```

**To see exactly where it stopped** — this works for you as well as the
agent:

```bash
python3 scripts/wiki_lint.py                            # how many pages at each status
grep -l 'status: stub' topics/*.md                      # which pages still need filling
python3 scripts/wiki_digest.py --topic <slug> --chars 0  # which sources in one page remain
```

The lint gives counts (`by status {stub: 7, drafted: 2, linked: 12}`); the
`grep` names the pages; the digest prints a `RESUME HERE` list of the
sources on one page not yet examined. A source already marked `deep read`
is never read twice, so resuming costs nothing extra.

**This is not only about the first build.** `wiki-update` follows the same
discipline, so an interrupted update resumes the same way. And if the stop
happens during step 3's *skim* phase, before any page exists, just re-run
it — nothing has been written yet, and a skim is cheap.

**Doing it in deliberate chunks** is fine, and often better than one long
run — "deep-read the next three topic pages, then stop" keeps each session
well inside its limits. The build is not one atomic operation.

**One caveat for an existing vault.** Pages written before this convention
have no markers. A page already `drafted` or `linked` with no markers at
all is treated as **predating the convention, not unread** — the tooling
says so explicitly rather than printing a resume list, so a migrated vault
is never re-read from scratch.

### 4. Afterwards

```bash
python3 scripts/wiki_lint.py
```

When new sources arrive, ask the agent to run **wiki-update**. The lint's
ORPHANED list is the queue of unprocessed material, so you never have to
track what has been read.

The five skills:

| Skill | Use when |
|---|---|
| `wiki-bootstrap` | first build — the four gated phases above |
| `wiki-update` | new sources appeared; fold them in |
| `wiki-restructure` | a page outgrew itself, or two pages overlap |
| `wiki-lint` | check integrity (reports; fixes only if you ask) |
| `wiki-find-sources` | look for literature you do not have yet |

## How the wiki layer is organised

Three tiers, set by the `tags` field:

| tier | is | has a `parent` | holds synthesis |
|---|---|---|---|
| `domain` | top-level area; a map of its sub-topics | no | no |
| `hub` | optional middle tier, when a topic outgrows one page | yes | no |
| `topic` | a leaf — **the actual content** | yes | yes |

Each topic page carries a `status`, so an interrupted build is resumable
at page level, and the read markers in `## Sources` make it resumable
*within* a page too (see [If the agent stops
midway](#if-the-agent-stops-midway)):

`stub` (created from a skim) → `drafted` (filled from a deep read) →
`linked` (cross-linked, multi-homing resolved)

The domain list is agreed with you once, at bootstrap, and then held
fixed — new material becomes a new topic under an existing domain rather
than quietly growing the top level.

Obsidian's **Needs filling** and **Needs linking** views in
`topics/_index.base` are driven by exactly that field.

A source belonging to several topics is normal — each page cites it for
the part relevant there.

## The rules the agent follows

In [`AGENTS.md`](AGENTS.md), and worth knowing:

1. **`sources/` is off-limits** to the agent. It is regenerated; edits
   there are lost.
2. **Topic pages are integrated into, never rewritten.** Your hand-edits
   are the most valuable text in the vault.
3. **New topics are proposed, not created.** You approve names.
4. **The lint is ground truth** for what needs attention.
5. **Every claim carries a `[[citekey]]`.** No source support → "needs a
   closer read", not a guess.
6. **The agent never adds to your reference manager.** External finds go
   to `candidate-sources.md` for you to review.

## Commands

| Command | Does |
|---|---|
| `wiki_lint.py` | integrity check + progress. Ground truth. Read-only. |
| `wiki_lint.py --json` | the same, machine-readable |
| `wiki_lint.py --ignore-orphans` | report orphans but do not fail on them — for hooks and CI |
| `wiki_digest.py` | skimmable digest of `sources/` — the clustering pass |
| `wiki_digest.py --orphaned` | only unprocessed sources |
| `wiki_digest.py --topic SLUG` | the sources behind one topic page, and which are still unread — the resume call |
| `zotero_sync.py --once` | one Zotero sync pass (`--rebuild` to rewrite all) |
| `new_source.py` | add a source by hand (`--adopt` for loose PDFs) |
| `sync_skill_pointers.py` | refresh per-agent skill pointers (`--check` for CI) |

All read-only except `zotero_sync.py` and `new_source.py`, which write
only to `sources/`.

## Layout

```
AGENTS.md              the contract — agent-agnostic, read this first
CLAUDE.md              thin entry point pointing at AGENTS.md
sources/               RAW layer (machine-written; PDFs gitignored)
topics/                WIKI layer (agent-written, human-edited)
  uncategorized.md     staging: unclustered sources + pending proposals
templates/             frontmatter contracts, with notes on each tier
candidate-sources.md   external finds awaiting your review
scripts/               stdlib-only tooling
.agents/skills/        the four workflows — canonical
.claude/skills/        generated pointers to the above
wiki.config.example.json  copy to wiki.config.json (gitignored) if using Zotero
```

## Using git (optional)

```bash
git init && git add -A && git commit -m "LLM wiki starter"
```

`.gitignore` already excludes Obsidian local state, `wiki.config.json`
(machine paths) and `sources/*.pdf` (large, and usually not yours to
redistribute). Source *notes* are tracked, so a colleague cloning the
repo gets the library's metadata without the PDFs.

A useful pre-commit hook:

```bash
python3 scripts/wiki_lint.py --quiet --ignore-orphans && python3 scripts/sync_skill_pointers.py --check
```

`--ignore-orphans` matters here: a plain `wiki_lint.py` exits non-zero
while any source is still unprocessed, which is the *normal* state, so a
hook without the flag would block almost every commit. With it, only real
breakage — a broken link, a dangling `parent`, a malformed page — stops a
commit, and the orphan count is still printed.

## Credits

The two-layer structure and agent-skill approach follow the
[LLM Wiki Core Setup guide](https://github.com/wanderloots-tutorials/vibe-coding/blob/main/wanderloots-llm-wiki-core-setup-v1.0.0.md).
This kit keeps the flat `sources/` + `topics/` layout, adds the gated
first-build workflow, the three-tier topic structure with a resumable
`status` field, and stdlib-only tooling with no configuration.
