#!/usr/bin/env python3
"""
new_source.py -- add a source to sources/ by hand, no reference manager.

Use this when you do not run Zotero, or for the occasional source that
is not in your library (a web page, a dataset, an internal report).
It writes the same frontmatter contract as the Zotero adapter, so
scripts/wiki_lint.py and every skill treat both kinds identically.

  # minimal
  python3 scripts/new_source.py --title "Attention Is All You Need" \
      --authors "Ashish Vaswani, Noam Shazeer" --year 2017

  # with a PDF, copied into sources/ and embedded in the note
  python3 scripts/new_source.py --title "..." --year 2017 \
      --pdf ~/Downloads/paper.pdf

  # adopt PDFs already sitting in sources/ with no note beside them
  python3 scripts/new_source.py --adopt

The citekey (and so the filename, and so the [[wikilink]] a topic page
cites) is derived as firstauthorTitleWordsYear, matching Better BibTeX's
default style, unless you pass --citekey explicitly.

Stdlib only. No pip install required.
"""

import argparse
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_config import SOURCES_DIR, parse_frontmatter  # noqa: E402

STOPWORDS = {
    "a", "an", "the", "of", "for", "and", "or", "on", "in", "to", "with",
    "at", "by", "from", "as", "is", "are", "be", "its", "their",
}


def ascii_fold(text):
    """Strip accents so citekeys stay filename-safe across platforms."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def make_citekey(title, authors, year):
    surname = ""
    if authors:
        first = authors.split(",")[0].strip()
        if first:
            surname = re.sub(r"[^A-Za-z]", "", ascii_fold(first.split()[-1])).lower()
    words = [
        w.capitalize()
        for w in re.findall(r"[A-Za-z]+", ascii_fold(title))
        if w.lower() not in STOPWORDS
    ][:3]
    key = f"{surname}{''.join(words)}{year or ''}"
    return key or "untitledSource"


def unique_path(citekey):
    """Never silently overwrite an existing source note."""
    candidate = SOURCES_DIR / f"{citekey}.md"
    if not candidate.exists():
        return candidate, citekey
    for suffix in "abcdefghijklmnopqrstuvwxyz":
        alt = SOURCES_DIR / f"{citekey}{suffix}.md"
        if not alt.exists():
            return alt, citekey + suffix
    raise SystemExit(f"Too many sources already named {citekey}*; pass --citekey.")


def _q(val):
    return '"' + str(val or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def note_body(citekey, title, authors, year, tags, doi, pub_type, journal,
              url, abstract, pdf_names):
    lines = [
        "---",
        f"citekey: {_q(citekey)}",
        f"title: {_q(title)}",
        f"authors: {_q(authors or 'Unknown')}",
        f"year: {year if year else 'null'}",
        f"tags: [{', '.join(tags)}]",
        f"doi: {_q(doi)}",
        f"pub_type: {_q(pub_type)}",
        f"journal: {_q(journal)}",
        f"url: {_q(url)}",
        f"has_pdf: {'true' if pdf_names else 'false'}",
        "---",
        "",
        f"# {title}",
        "",
        f"**{authors or 'Unknown'}** ({year or 'n.d.'})",
        "",
        "## Abstract",
        abstract or "_No abstract._",
        "",
        "## Notes",
        "",
        "## PDF",
    ]
    lines += [f"![[{n}]]" for n in pdf_names] or ["_No PDF attached._"]
    return "\n".join(lines) + "\n"


def adopt_orphan_pdfs():
    """Create a stub note for every PDF in sources/ that has none."""
    have = set()
    for md in SOURCES_DIR.glob("*.md"):
        fm, _ = parse_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
        have.add(fm.get("citekey") or md.stem)

    made = 0
    for pdf in sorted(SOURCES_DIR.glob("*.pdf")):
        # foo-2.pdf is a second attachment of foo, not its own source.
        # Only a single digit 2-9, so a trailing year (foo-2024) survives.
        stem = re.sub(r"-[2-9]$", "", pdf.stem)
        if stem in have:
            continue
        path = SOURCES_DIR / f"{stem}.md"
        path.write_text(
            note_body(stem, pdf.stem.replace("-", " ").replace("_", " "),
                      None, None, [], "", "", "", "", None, [pdf.name]),
            encoding="utf-8",
        )
        have.add(stem)
        made += 1
        print(f"Adopted {pdf.name} -> {path.name}")

    if not made:
        print("No orphaned PDFs found in sources/.")
    else:
        print(f"\n{made} stub note(s) created. Fill in title/authors/year, "
              "then run:\n  python3 scripts/wiki_lint.py")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--adopt", action="store_true",
                    help="stub a note for every PDF in sources/ lacking one")
    ap.add_argument("--title")
    ap.add_argument("--authors", help='comma-separated, e.g. "Ada Lovelace, Alan Turing"')
    ap.add_argument("--year", type=int)
    ap.add_argument("--citekey", help="override the generated citekey")
    ap.add_argument("--pdf", help="PDF to copy into sources/ and embed")
    ap.add_argument("--doi", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--journal", default="")
    ap.add_argument("--pub-type", default="article-journal",
                    help="CSL type: article-journal, book, report, webpage, thesis, ...")
    ap.add_argument("--tags", default="", help="comma-separated")
    ap.add_argument("--abstract", default="")
    args = ap.parse_args()

    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    if args.adopt:
        return adopt_orphan_pdfs()
    if not args.title:
        ap.error("--title is required (or use --adopt)")

    citekey = args.citekey or make_citekey(args.title, args.authors, args.year)
    path, citekey = unique_path(citekey)

    pdf_names = []
    if args.pdf:
        src = Path(args.pdf).expanduser()
        if not src.exists():
            raise SystemExit(f"No such PDF: {src}")
        dest = SOURCES_DIR / f"{citekey}.pdf"
        shutil.copy2(src, dest)
        pdf_names.append(dest.name)
        print(f"Copied PDF -> {dest.name}")

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    path.write_text(
        note_body(citekey, args.title, args.authors, args.year, tags, args.doi,
                  args.pub_type, args.journal, args.url, args.abstract, pdf_names),
        encoding="utf-8",
    )
    print(f"Created {path.relative_to(SOURCES_DIR.parent)}")
    print(f"Cite it from a topic page as [[{citekey}]]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
