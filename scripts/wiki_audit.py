#!/usr/bin/env python3
"""
wiki_audit.py -- rank existing claims by how likely they are to be wrong.

For retrofitting claim-fidelity discipline (AGENTS.md -> Claim fidelity)
to a wiki whose pages were written before it. Re-verifying every claim
costs as much as the original deep read, so this orders the work instead:
it scores each claim block on signals that correlate with context error,
and hands you a shortlist for `wiki-verify`.

  python3 scripts/wiki_audit.py                 # top 20 across the vault
  python3 scripts/wiki_audit.py --top 50
  python3 scripts/wiki_audit.py --min-score 5
  python3 scripts/wiki_audit.py --topic <slug>  # one page, every block
  python3 scripts/wiki_audit.py --json

A score is a PRIORITY, not a verdict. A high score means "check this
first"; it is not evidence the claim is wrong, and a zero score is not
evidence it is right. Only reading the source settles either.

Read-only. Stdlib only.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_config import SOURCES_DIR, STAGING_FILES, TOPICS_DIR, parse_frontmatter  # noqa: E402

CLAIM_SECTIONS = ("What the literature says", "Open questions / gaps")

NUM = re.compile(r"\d[\d.,]*\s*(%|°C|\bK\b|W/|kW\b|MW\b|vol%|wt%|bar\b|Pa\b|mm\b|μm\b)")
# A qualifier near a figure is what pins it to an operating point.
COND = re.compile(r"\b(at|under|for|when|with|per|across|above|below|between|using|during)\b", re.I)
STRONG = re.compile(r"\b(shows?|proves?|demonstrates?|confirms?|establishes?)\b", re.I)
HEDGE = re.compile(r"\b(suggests?|indicates?|may|might|could|appears?|likely|reported|"
                   r"estimated|modell?ed|simulat)\w*", re.I)
QUOTE = re.compile(r'"[^"]{8,}"|“[^”]{8,}”')
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")

# Each signal, why it correlates with a context error, and its weight.
SIGNALS = [
    ("abstract-only", 3,
     "every source lacks a PDF, so conditions were never available to copy"),
    ("has figures", 2,
     "carries a number -- the claim type that is both checkable and load-bearing"),
    ("figure w/o conditions", 2,
     "a number with no nearby qualifier: the signature of condition stripping"),
    ("unhedged", 1,
     "asserts without any hedge, where the source may have hedged"),
    ("no anchor", 1,
     "no verbatim quote, so checking it means re-reading the paper"),
    ("long, 1 source", 1,
     "many sentences resting on one citation"),
]


def source_pdf_map():
    out = {}
    for f in SOURCES_DIR.glob("*.md"):
        if f.stem.startswith("_"):
            continue
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        out[f.stem] = bool(fm.get("has_pdf"))
    return out


def score_block(text, cites, has_pdf):
    score, why = 0, []

    def add(name):
        nonlocal score
        w = next(w for n, w, _ in SIGNALS if n == name)
        score += w
        why.append(name)

    if cites and not any(has_pdf.get(c) for c in cites):
        add("abstract-only")
    if NUM.search(text):
        add("has figures")
        if not COND.search(text):
            add("figure w/o conditions")
    if STRONG.search(text) and not HEDGE.search(text):
        add("unhedged")
    if not QUOTE.search(text):
        add("no anchor")
    if len(text.split()) > 120 and len(cites) == 1:
        add("long, 1 source")
    return score, why


def collect(only_topic=None):
    has_pdf = source_pdf_map()
    srcs = set(has_pdf)
    rows = []
    pages = ([TOPICS_DIR / f"{only_topic}.md"] if only_topic
             else sorted(TOPICS_DIR.glob("*.md")))
    for f in pages:
        if not f.exists():
            raise SystemExit(f"No such topic page: {f}")
        if f.name in STAGING_FILES or f.stem.startswith("_"):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        fm, _ = parse_frontmatter(text)
        tags = fm.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if "topic" not in tags:
            continue
        for sect in CLAIM_SECTIONS:
            if f"## {sect}" not in text:
                continue
            body = text.split(f"## {sect}", 1)[1].split("\n## ", 1)[0]
            for blk in body.split("\n\n"):
                if len(blk.split()) < 10:
                    continue
                cites = {c.strip() for c in WIKILINK.findall(blk)} & srcs
                if not cites:
                    continue  # uncited blocks are wiki_lint's business
                sc, why = score_block(blk, cites, has_pdf)
                rows.append({
                    "score": sc, "page": f.stem, "section": sect,
                    "signals": why, "words": len(blk.split()),
                    "citekeys": sorted(cites),
                    "excerpt": " ".join(blk.split())[:110],
                })
    rows.sort(key=lambda r: (-r["score"], r["page"]))
    return rows


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=20, help="how many to show (default 20)")
    ap.add_argument("--min-score", type=int, default=0)
    ap.add_argument("--topic", metavar="SLUG", help="restrict to one page")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = [r for r in collect(args.topic) if r["score"] >= args.min_score]
    if args.json:
        print(json.dumps(rows[:args.top], indent=2))
        return 0

    if not rows:
        print("No cited claim blocks found.")
        return 0

    shown = rows[:args.top]
    print(f"{len(rows)} cited claim block(s); showing {len(shown)}, highest risk first.\n")
    for r in shown:
        print(f"[{r['score']}] {r['page']} [{r['section']}] ({r['words']}w)")
        print(f"     signals: {', '.join(r['signals']) or 'none'}")
        print(f"     sources: {', '.join(r['citekeys'][:4])}"
              f"{' ...' if len(r['citekeys']) > 4 else ''}")
        print(f"     {r['excerpt']}...\n")

    buckets = {}
    for r in rows:
        buckets[r["score"]] = buckets.get(r["score"], 0) + 1
    print("score distribution:", dict(sorted(buckets.items(), reverse=True)))
    print("\nA score is a PRIORITY, not a verdict -- it says what to check first,")
    print("not that anything is wrong. Audit with the wiki-verify skill.")
    print("Signals:")
    for name, w, meaning in SIGNALS:
        print(f"  +{w}  {name:<22} {meaning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
