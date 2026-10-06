---
name: wiki-find-sources
description: Search external literature databases for papers relevant to existing topic pages that are not yet in the library, de-duplicate against sources/, and write them to candidate-sources.md for human review. Use when asked to find new sources, search the literature, or expand coverage for a topic. Never adds anything to the reference manager or writes into sources/.
---

# wiki-find-sources

Finds candidates. **Does not enrol them.** Literature selection is a
human decision (`AGENTS.md` rule 6). Read `AGENTS.md` first.

## Hard boundary

You may: search external databases, de-duplicate against the library,
write to `candidate-sources.md`.

You may **never**: add anything to the reference manager, write into
`sources/`, or cite a candidate from a topic page. A candidate is not a
source until the user has added it to their library and the sync adapter
has written it into `sources/`. Citing one produces a broken link and an
unsupported claim.

## 1. Derive search terms from the pages themselves

Work through every page in `topics/`, or just the one the user names.

Pull key terms from its `## Overview` and `## What the literature says` —
the methods, mechanisms, models, materials, populations or contexts it
actually covers — and from its `## Open questions / gaps`, which is the
best available statement of what is missing, written from a real read:

```bash
sed -n '/## Overview/,/## Open questions/p' topics/<slug>.md
grep -A 12 '## Open questions' topics/<slug>.md
```

Use the vocabulary on the page, not general knowledge of the field. The
point is to find what *this* wiki is missing.

## 2. Know what you already have

```bash
python3 scripts/wiki_digest.py --chars 0 > /tmp/have.txt; wc -l /tmp/have.txt
python3 scripts/wiki_digest.py --topic <slug> --chars 0
```

## 3. Search

Use whichever literature search tools this agent has — a research-database
tool, a scholarly index, or a database the user names. Prefer a scholarly
index over general web search.

- Run **several differently-phrased queries** rather than one. Recall
  matters more than precision here, because the user filters afterwards.
- Prioritise recent and highly-cited work. **A handful of strong
  candidates beats a long list of marginal ones.**
- Match the database to the subject, and say when you cannot. A
  biomedical index returns little for an engineering topic and vice
  versa; lean on the general scholarly index rather than forcing hits
  from the wrong corpus.
- Terms differ between adjacent fields. If a concept has another name
  elsewhere, search both and say which you tried.

Record per hit: title, authors, year, venue, DOI, and one line on what it
would add **beyond what the page already cites**.

## 4. De-duplicate — carefully

Check every hit against the library before proposing it. **DOI is the
most reliable test**; title comparison is the fallback, and citekeys
encode author/title/year so title words work well:

```bash
grep -ri '10.1016/j.example' sources/ | head          # by DOI
grep -ril 'distinctive title words' sources/ | head   # by title
```

Also check `candidate-sources.md` itself, **including its Rejected
section** — re-proposing something the user already turned down wastes
their time and is this skill's main failure mode.

Treat as already held: same DOI; same title bar trivial differences; a
preprint whose published version is present, and the reverse.

## 5. Write to candidate-sources.md

One section per topic, **appending without rewriting the file**:

```markdown
### <YYYY-MM-DD> — [[topic-slug]]

Searched: <tool/database>, queries: "<q1>", "<q2>"
Gap addressed: <which gap from that page>

- **<Title>** (Year) — Authors. *Venue*. DOI: <doi>
  Why: what it adds beyond what [[topic-slug]] already cites.
- **<Title>** (Year) — …

Checked against sources/ and the Rejected list; N hits dropped as
already held (<citekeys>).
```

Set the file's `last_updated`.

## 6. Report and stop

- candidate counts per topic,
- how many hits were dropped as duplicates, and of what,
- **any topic where results were thin either way** — nothing found, or
  nothing beyond what is already cited. Both are useful findings: the
  first may mean the search terms were wrong, the second that coverage is
  genuinely good.
- where the search was weak: a paywalled or unreachable index, a term
  that may be named differently in an adjacent field. Say it rather than
  implying the search was exhaustive.

Then **stop**. Do not sync, do not create topics, do not cite anything.
