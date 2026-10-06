#!/usr/bin/env python3
"""
wiki_digest.py -- compact, skimmable digest of sources/.

Purpose-built for the *skim* phase of a wiki build: it lets an agent
survey hundreds of sources in one tool call instead of opening each
file, and it deliberately refuses to print whole PDFs, so a skim stays
a skim.

  # every source, short abstracts -- the clustering pass
  python3 scripts/wiki_digest.py

  # only the unprocessed ones -- the incremental update pass
  python3 scripts/wiki_digest.py --orphaned

  # more abstract per source, when clustering is genuinely ambiguous
  python3 scripts/wiki_digest.py --chars 600

  # the sources behind one topic page, before a deep read
  python3 scripts/wiki_digest.py --topic thermal-management --chars 0

`--chars 0` prints metadata only. `--json` emits records instead of
text. Read-only; never writes to the vault.

Stdlib only. No pip install required.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_config import SOURCES_DIR, TOPICS_DIR, parse_frontmatter  # noqa: E402

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def abstract_of(text):
    """Pull the ## Abstract section, collapsed to a single line."""
    m = re.search(r"^##\s+Abstract\s*$(.*?)(?=^##\s|\Z)", text,
                  re.MULTILINE | re.DOTALL)
    if not m:
        return ""
    body = m.group(1).strip()
    if body.startswith("_No abstract"):
        return ""
    return re.sub(r"\s+", " ", body)


def cited_citekeys():
    """Every citekey any topic page cites, and by which pages."""
    out = {}
    for md in TOPICS_DIR.glob("*.md"):
        if md.stem.startswith("_"):
            continue
        for t in WIKILINK_RE.findall(md.read_text(encoding="utf-8", errors="replace")):
            out.setdefault(t.strip(), set()).add(md.stem)
    return out


def collect(args):
    cited = cited_citekeys()

    wanted = None
    if args.topic:
        page = TOPICS_DIR / f"{args.topic}.md"
        if not page.exists():
            raise SystemExit(f"No such topic page: {page}")
        text = page.read_text(encoding="utf-8", errors="replace")
        wanted = {t.strip() for t in WIKILINK_RE.findall(text)}

    records = []
    for md in sorted(SOURCES_DIR.glob("*.md")):
        if md.stem.startswith("_"):
            continue
        if wanted is not None and md.stem not in wanted:
            continue
        where = sorted(cited.get(md.stem, ()))
        if args.orphaned and where:
            continue

        text = md.read_text(encoding="utf-8", errors="replace")
        fm, _ = parse_frontmatter(text)
        abstract = abstract_of(text)
        records.append({
            "citekey": md.stem,
            "title": fm.get("title") or "",
            "authors": fm.get("authors") or "",
            "year": fm.get("year"),
            "pub_type": fm.get("pub_type") or "",
            "journal": fm.get("journal") or "",
            "tags": fm.get("tags") or [],
            "has_pdf": bool(fm.get("has_pdf")),
            "has_abstract": bool(abstract),
            "in_topics": where,
            "abstract": abstract,
        })
    return records


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--orphaned", action="store_true",
                    help="only sources no topic page cites yet")
    ap.add_argument("--topic", metavar="SLUG",
                    help="only the sources cited by this topic page")
    ap.add_argument("--chars", type=int, default=300,
                    help="abstract characters per source (0 = metadata only)")
    ap.add_argument("--json", action="store_true", help="emit JSON records")
    args = ap.parse_args()

    if not SOURCES_DIR.exists():
        raise SystemExit(f"No sources/ directory under {SOURCES_DIR.parent}")

    records = collect(args)

    if args.json:
        for r in records:
            r["abstract"] = r["abstract"][:args.chars] if args.chars else ""
        print(json.dumps(records, indent=2))
        return 0

    no_abstract, no_pdf = [], []
    for r in records:
        year = r["year"] if r["year"] is not None else "n.d."
        flags = "".join(("P" if r["has_pdf"] else "-",
                         "A" if r["has_abstract"] else "-"))
        head = f"[{flags}] {r['citekey']} ({year}) — {r['title']}"
        if r["in_topics"]:
            head += f"   «in: {', '.join(r['in_topics'])}»"
        print(head)
        if args.chars and r["abstract"]:
            print(f"      {r['abstract'][:args.chars]}")
        if not r["has_abstract"]:
            no_abstract.append(r["citekey"])
        if not r["has_pdf"]:
            no_pdf.append(r["citekey"])

    print(f"\n{len(records)} source(s). Flags: P=has PDF, A=has abstract.")
    if no_abstract:
        print(f"  {len(no_abstract)} with NO abstract — cannot be clustered from "
              f"metadata alone; needs a closer read or a human decision.")
    if no_pdf:
        print(f"  {len(no_pdf)} with NO PDF — a deep read is impossible; say so "
              f"on the page rather than inferring from the abstract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
