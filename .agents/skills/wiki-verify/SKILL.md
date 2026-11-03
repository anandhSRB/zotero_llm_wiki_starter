---
name: wiki-verify
description: Audit the claims on a topic page against the sources they cite — checking that each source actually produced the finding, under the conditions stated, with the hedge intact. Use when asked to verify, audit, fact-check or spot-check a page, before relying on one in a paper or talk, or after noticing a claim that a source does not support. Checks meaning, not citation presence.
---

# wiki-verify

The audit pass. Read `AGENTS.md` first — in particular **Claim fidelity**,
which this skill enforces after the fact.

`wiki_lint.py` can only check that a claim *has* a citation. This skill
checks whether the cited source actually supports it. That cannot be
automated, which is why it is a skill and not a script.

## When to run it

- Before relying on a page in a paper, thesis, talk or decision.
- After finding one bad claim — errors cluster, because they come from a
  single reading session. Audit that whole page, not just the sentence.
- On the pages `wiki_lint.py` flags as **resting only on abstract-only
  sources**, which is where context errors concentrate.

Never run it across the whole vault at once. It is as expensive as the
original deep read.

## Retrofitting a wiki written before these rules existed

Pages written earlier carry no quote anchors and often no conditions.
**Do not try to re-verify everything** — that costs as much as the
original deep read and will not be finished.

Order the work instead:

```bash
python3 scripts/wiki_audit.py --top 25
```

That ranks every cited claim block by signals correlated with context
error — sources with no PDF, bare figures, figures with no qualifier
nearby, unhedged assertions, no verbatim anchor. Work down the list.

A realistic sequence:

1. **Stop the bleeding first.** The fidelity rules apply to all *new*
   writing the moment the skills are in place; that costs nothing extra
   and is most of the long-run benefit.
2. **Audit the top of the ranking** — on a real vault this is tens of
   blocks, not hundreds.
3. **Verify opportunistically.** Whenever `wiki-update` touches a page
   for another reason, verify the claims already on it. Retrofitting then
   rides along with work you were doing anyway.
4. **Verify on demand.** Before a page is used in a paper or a talk,
   audit that page in full regardless of score.

Add anchors as you go. Each one you add makes the next audit of that
claim a grep instead of a re-read, so the cost falls over time.

A score is a priority, not a verdict: a high score is not evidence a
claim is wrong, and a zero score is not evidence it is right.

## Pick the target

```bash
python3 scripts/wiki_lint.py                  # counts, and abstract-only claims
python3 scripts/wiki_audit.py --topic <slug>  # every block on one page, ranked
python3 scripts/wiki_digest.py --topic <slug> --chars 0   # which have a PDF
```

The digest shows which sources have a PDF. A claim citing a source with
no PDF can only ever be checked against its abstract — note that limit
rather than pretending to have verified it.

## The loop, one claim at a time

This is a deep read, so `AGENTS.md` → **Checkpointing** applies: fix or
annotate each claim on the page **before** moving to the next. An audit
held in context and lost is worse than no audit, because nothing records
which claims were already checked.

For each claim block in `## What the literature says` and
`## Open questions / gaps`, open the cited source and ask, in this order:

1. **Does the source make this claim at all?** If not, the claim is
   unsupported — delete it, or demote it to "needs a closer read".
2. **Did this source produce it, or relay it?** Check whether the
   sentence sits in the paper's own results or in its introduction citing
   prior work. This is the most common failure. Fix by citing the
   original, or by writing "as reported in `[[x]]`".
3. **Are the conditions right?** Compare every number against the body —
   the results table, not the abstract. Check concentration, temperature,
   scale, population, load case. A figure whose operating point is
   missing or wrong is a defect even when the number matches.
4. **Is the scope honest?** If the study's setting differs from the
   page's subject, the page must say so.
5. **Is the hedge intact?** Modelled is not measured. "Suggests" is not
   "shows". One study is not a literature.
6. **Do abstract and body agree?** Where they do not, record the
   disagreement on the page and prefer the body.

## Recording the result

Edit the claim in place — **never rewrite the page** (rule 2). Then mark
the source in `## Sources`:

```markdown
- [[citekeyA]] — deep read 2026-10-07, verified 2026-11-03
- [[citekeyB]] — abstract only (no PDF), verified 2026-11-03 (abstract only)
```

Add a verbatim anchor to any figure you had to go back to the paper to
confirm. That is the whole point: the next audit should be a grep, not a
re-read.

Where a claim cannot be checked — no PDF, paywalled, a scanned file with
no text layer — **say so on the page** rather than leaving it looking
verified.

## Reporting

State plainly, per claim changed:

- what the page said, what the source actually says, and which of the
  five failure modes it was,
- claims you could not check, and why,
- claims you deleted, and whether anything else on the page depended on
  them,
- whether the errors share a cause — all from one source, one session, or
  one abstract-only paper. **Say so if they do**: that tells the user
  which other pages to audit next, which is more valuable than the fixes
  themselves.

Never report a page as verified when you checked only part of it.
