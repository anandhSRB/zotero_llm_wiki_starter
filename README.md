# LLM Wiki — starter kit

A two-layer research wiki for Obsidian that an AI agent can maintain
with you, built so that **every claim traces back to a source you
actually have**.

Field-agnostic: the structure comes from your library, not from this kit.
It works the same for medicine, law, materials science, machine learning
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
4. **cross-link** topics and place sources that belong in more than one.

The gates are deliberate. Approving a topic list takes a minute; undoing
a structure built on a wrong guess takes an afternoon.

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
and you can see at a glance what is left:

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
| `wiki_digest.py` | skimmable digest of `sources/` — the clustering pass |
| `wiki_digest.py --orphaned` | only unprocessed sources |
| `wiki_digest.py --topic SLUG` | the sources behind one topic page |
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
python3 scripts/wiki_lint.py --quiet && python3 scripts/sync_skill_pointers.py --check
```

## Credits

The two-layer structure and agent-skill approach follow the
[LLM Wiki Core Setup guide](https://github.com/wanderloots-tutorials/vibe-coding/blob/main/wanderloots-llm-wiki-core-setup-v1.0.0.md).
This kit keeps the flat `sources/` + `topics/` layout, adds the gated
first-build workflow, the three-tier topic structure with a resumable
`status` field, and stdlib-only tooling with no configuration.
