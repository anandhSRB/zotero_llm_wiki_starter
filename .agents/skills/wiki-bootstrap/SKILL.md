---
name: wiki-bootstrap
description: First-time build of the wiki layer from a freshly synced sources/ folder. Use when topics/ is empty or nearly empty and sources/ has content. Runs four gated phases — agree the domains, skim-cluster into concise topics, deep-read to fill them, then cross-link and multi-home. Not for folding in a handful of new sources; use wiki-update for that.
---

# wiki-bootstrap

Builds the wiki layer from scratch. Read `AGENTS.md` first — its
non-negotiable rules apply throughout, especially: never touch
`sources/`, never create a topic without approval, every claim carries a
`[[citekey]]`.

## When this applies

`topics/` is empty or has only a stray page, and `sources/` has content.
If `topics/` already has a real structure and you are folding in new
sources, stop and use `wiki-update` instead.

## Shape of the build

Four phases, in order, each ending at a **gate** where you stop and wait
for the user. The order is the point: domains before topics, topics
before deep reading, deep reading before cross-linking. Skipping ahead
produces a structure that has to be thrown away.

```
0  Preflight        →  1  Domains (ASK)  →  2  Skim-cluster (PROPOSE)
                                                      ↓
   4  Cross-link    ←  3  Deep read & fill  ←  create stub pages
```

A real library takes **several sessions**. That is expected. Phases 3
and 4 are resumable: `status` in each page's frontmatter records where
you stopped, so always start a session by reading the current state
rather than assuming.

Afterwards the vault is maintained by the other skills: `wiki-update` for
new sources, `wiki-restructure` when a page outgrows itself, `wiki-lint`
to check integrity, `wiki-find-sources` to look for what is missing.

---

## Phase 0 — Preflight

```bash
python3 scripts/wiki_lint.py
python3 scripts/wiki_digest.py --chars 0 | tail -5
```

Note from the summary line:
- how many sources there are,
- how many have **no abstract** (cannot be clustered from metadata — they
  need a human decision or a closer look),
- how many have **no PDF** (a deep read will be impossible; those pages
  must say so rather than inflating an abstract into a finding).

Report these three numbers before going further. If `sources/` is empty,
stop: the user needs to run their sync adapter first.

---

## Phase 1 — Agree the domains (ASK, never infer)

**Ask the user explicitly what the main domains of their wiki should
be.** Do not infer them from the sources and proceed. This is the one
decision that shapes everything downstream, and it encodes how the user
thinks about their own field — which the library's contents do not fully
reveal.

Ask as a real question and wait for an answer. To make it easy to answer
rather than open-ended, you may offer a *draft* from the digest, clearly
labelled as a starting point:

> Before I build anything: what are the main domains of your wiki? These
> become the 3–8 top-level areas everything else hangs off.
>
> From skimming titles, the library looks like it might split into
> roughly: A, B, C. But you know the field — do you want those, or a
> different cut? Shall I use yours, mine, or a mix?

Rules for this phase:
- **3–8 domains.** Fewer than 3 and the tree adds nothing; more than 8
  and it stops being a map.
- Domains are *areas*, not individual topics. If a proposed domain would
  hold one or two sources, it is a topic.
- Where two domains could be confused, get the **boundary** in words now
  — "X covers the mechanism, Y covers systems that use it". That sentence
  goes on both domain pages and prevents most misfiling later.
- Use the user's own terminology verbatim, even where you would phrase it
  differently.

**Once agreed, this list is fixed.** Every later session treats it as
established: `wiki-update` files new material into existing domains and
does not invent new ones, and `wiki-restructure` never splits or merges a
domain page. Changing the list later is a deliberate conversation with
the user. That is why this gate is worth the minute it costs.

**Gate: do not continue until the user has confirmed the domain list.**

Then create one page per domain from `templates/domain-page.md`, with
`tags: [domain]`, `status: stub`, the agreed boundary sentence in the
Overview, and an empty Sub-topics list. Keep slugs to 2–3 words.

---

## Phase 2 — Skim-cluster into topics (PROPOSE, do not create)

**Skim only. Do not open a single PDF in this phase.** You are deciding
*where things belong*, not what they say — and a deep read of a whole
library before the structure exists is wasted work.

```bash
python3 scripts/wiki_digest.py --chars 300
```

One call surveys the whole library: citekey, year, title, and a trimmed
abstract. Raise `--chars` only for the subset that is genuinely
ambiguous. For a very large library, work domain by domain.

Cluster the sources into candidate topics. A good cluster:
- holds **3–15 sources** that would be read together,
- answers one question, not three,
- sits clearly under exactly one domain (sources that genuinely span two
  are fine — they get multi-homed in Phase 4; the *topic* belongs to one
  parent),
- is named the way a practitioner would say it out loud.

### Naming — concise, and the lint checks this

**2–4 words, 5 maximum.** Slugs appear inside wikilinks mid-sentence and
in the graph view, where long names are unreadable. Drop filler words
("overview", "studies", "technologies", "and"), drop the field's name
when every page would carry it, and drop words implied by the parent
domain.

| Prefer | Not |
|---|---|
| `wall-boiling-closures` | `cfd-wall-boiling-closure-models-for-two-fluid-simulations` |
| `nanofluid-coolants` | `nanofluid-coolants-for-fuel-cell-thermal-management` |
| `altitude-performance` | `pemfc-altitude-and-low-pressure-performance-studies` |

Then **present the full set and stop**:

> Proposed topics under **<domain>**:
>
> - **`slug-one`** (6 sources) — one line on what it covers.
>   `citekeyA`, `citekeyB`, …
> - **`slug-two`** (4 sources) — …
>
> Unplaced: `citekeyX` (no abstract), `citekeyY` (fits nothing yet — own
> topic, or park it?)

Flag explicitly:
- sources you could not place, and why,
- clusters of one or two sources — propose merging rather than creating a
  near-empty page,
- any domain that got no sources, which usually means Phase 1's cut was
  slightly off and is worth saying out loud.

**Gate: `AGENTS.md` rule 3. Do not create topic pages until the user
approves the list.** Expect the names to be edited — that is the point of
the gate.

### After approval

Create each approved page from `templates/topic-page.md`:
- `tags: [topic]`, `parent:` set, **`status: stub`**, `last_updated` today,
- Overview: two or three sentences from the abstracts, cited,
- `## Sources`: the full `[[citekey]]` list,
- leave `## What the literature says` with a single line:
  `_Awaiting deep read._`

Then add each new page to its domain's `## Sub-topics` list — **editing
that section in place, not rewriting the file** (rule 2).

Verify before moving on:

```bash
python3 scripts/wiki_lint.py
```

Orphan count should now be near zero. Every remaining orphan is a source
you consciously could not place — name them for the user, and record each
in `topics/uncategorized.md` with one line on why nothing fits, together
with any cluster still awaiting approval. That file is staging, not a
catch-all: the sources stay orphaned in the lint, which is the correct
state for undecided material, and the note is there so a later session
knows what was already considered. Do not invent a topic to absorb them.

---

## Phase 3 — Deep read and fill

Now the expensive part. Work **one topic page at a time**, so progress
survives an interrupted session.

For each page with `status: stub`:

```bash
python3 scripts/wiki_digest.py --topic <slug> --chars 0
```

That lists its sources and flags which have a PDF. Then read the actual
PDFs embedded in those source notes — and for sources flagged `-` for
PDF, work from the abstract and **say on the page that it is
abstract-only**.

Write `## What the literature says` organised **by claim, not by paper**:
a bolded lead-in per theme, then what the sources say about it. One
paragraph per paper is a reading list, not synthesis.

While reading, actively look for:
- **disagreement between sources** — surface it and attribute each side;
  never average two numbers into one,
- **a source contradicting itself** — an abstract whose headline figure
  does not match its own results table is a real finding; record it,
- **what is missing** — put it in `## Open questions / gaps`, and
  distinguish "no one has studied this" from "I have not read it closely
  yet",
- **anything you cannot support** — write "needs a closer read" and name
  the source. Never fill a gap by inference (rule 5).

Then set `status: drafted`, bump `last_updated`, and move to the next
page. Re-run the lint every few pages to catch a broken link early.

---

## Phase 4 — Multi-home and cross-link

Only once pages are `drafted` — before that you do not yet know enough
about what each page says to link them honestly.

```bash
python3 scripts/wiki_lint.py            # multi-homed count
python3 scripts/wiki_digest.py --chars 0 | grep '«in:'
```

### Multi-homing

For each source that a deep read showed is relevant to a topic beyond the
one it was filed under: add it to that page's `## Sources` and cite it in
the body **for the part that is relevant there**. A paper on method and
application appears on both pages, saying something different on each.
Never paste the same paragraph twice. This is normal — the lint reports
the count as information, never as an error.

### Cross-linking

On each topic page, fill `## Cross-links` with prose, not a bare list:
`overlaps with [[sibling]], which covers the X side of the same
question`. Only real relationships; padding here is worse than an empty
section.

Also:
- make the boundary sentence between neighbouring **domains** explicit on
  both domain pages, each linking the other,
- where a cluster has outgrown one page, propose promoting it to a `hub`
  with child topics — **propose, do not do it** (rule 3),
- lift genuinely cross-cutting gaps up to the domain page's
  `## Open questions / gaps`.

Set `status: linked` and bump `last_updated`.

---

## Finishing

```bash
python3 scripts/wiki_lint.py
```

Then report, per `AGENTS.md`:
- the agreed domains, and the topics created under each,
- how many pages are at `stub` / `drafted` / `linked`, so the user knows
  exactly what is left,
- sources still orphaned, and why each one is,
- sources deliberately multi-homed,
- anything you flagged as "needs a closer read", listed explicitly —
  these are the honest gaps and must not be buried.

Never report the lint as clean without having run it.
