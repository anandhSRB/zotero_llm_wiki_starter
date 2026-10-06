#!/usr/bin/env python3
"""
wiki_lint.py -- read-only integrity check for the vault.

This script is ground truth for "what needs attention". It never writes
to the vault. Run it before and after any session that touches topics/.

  python3 scripts/wiki_lint.py            # human-readable report
  python3 scripts/wiki_lint.py --json     # same data, machine-readable
  python3 scripts/wiki_lint.py --quiet    # problems only, no progress

Exit code 0 means no problems. Exit code 1 means it found something.
Progress information (stub counts, orphan counts) is reported but does
not on its own make the run fail -- an unfinished wiki is not a broken
one. Orphaned sources DO fail, because they are the definition of
unprocessed material.

Stdlib only. No pip install required.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_config import (  # noqa: E402
    SOURCES_DIR,
    STAGING_FILES,
    TOPIC_STATUSES,
    TOPIC_TAGS,
    TOPICS_DIR,
    VAULT_ROOT,
    parse_frontmatter,
)

# [[target]], [[target#heading]], [[target|alias]], ![[embed.pdf]]
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")

# Topic slugs should stay short enough to read in a graph view and in a
# wikilink mid-sentence. This is a style warning, not a hard error.
MAX_SLUG_WORDS = 5


def build_indices():
    """How links resolve in Obsidian.

    notes:     .md stem -> paths      ([[note]] matches the stem)
    all_files: exact filename -> paths ([[file.pdf]] matches the filename)
    """
    notes, all_files = defaultdict(list), defaultdict(list)
    for f in VAULT_ROOT.rglob("*"):
        if not f.is_file() or any(part.startswith(".") for part in f.parts):
            continue
        all_files[f.name].append(f)
        if f.suffix == ".md":
            notes[f.stem].append(f)
    return notes, all_files


def check_base_files(problems):
    """Validate Obsidian .base view definitions, if PyYAML is available."""
    bases = list(VAULT_ROOT.rglob("*.base"))
    if not bases:
        return
    try:
        import yaml
    except ImportError:
        return  # optional check; absence of PyYAML is not a problem
    for base in bases:
        try:
            yaml.safe_load(base.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            problems.append(f"BAD .base YAML: {base.relative_to(VAULT_ROOT)} -- {e}")


def lint():
    problems, warnings = [], []
    # PDF issues are collected apart from the rest: when a vault is copied
    # between machines without its PDFs, every source reports the same two
    # problems and buries everything else. See summarise_pdf_issues().
    pdf_issues = []
    notes, all_files = build_indices()

    # Obsidian resolves [[x]] ambiguously when two notes share a stem.
    # Only collisions among vault content matter -- a topic page named
    # after a citekey makes every citation of it ambiguous. Two docs
    # outside sources/ and topics/ (say README.md and templates/README.md)
    # are never link targets, so they are not a problem.
    layered = {d.name for d in (SOURCES_DIR, TOPICS_DIR)}
    for stem, paths in sorted(notes.items()):
        inside = [p for p in paths
                  if p.relative_to(VAULT_ROOT).parts[0] in layered]
        if len(inside) > 1 or (inside and len(paths) > 1):
            rels = ", ".join(str(p.relative_to(VAULT_ROOT)) for p in sorted(paths))
            problems.append(f"DUPLICATE NAME: '{stem}' used by {rels}")

    source_citekeys = {p.stem for p in SOURCES_DIR.glob("*.md") if not p.stem.startswith("_")}
    topic_pages = [p for p in sorted(TOPICS_DIR.glob("*.md"))
                   if not p.stem.startswith("_") and p.name not in STAGING_FILES]
    topic_stems = {p.stem for p in topic_pages}

    # citekey -> set of topic slugs citing it. A source appearing in
    # several topics is correct and expected, not a problem.
    cited_by = defaultdict(set)
    status_counts = defaultdict(int)
    tag_counts = defaultdict(int)

    # Only sources/ and topics/ are vault content. Root-level docs
    # (README, AGENTS.md) legitimately write [[citekey]] as prose
    # placeholders, so linting their links would be noise.
    content = sorted(SOURCES_DIR.glob("*.md")) + sorted(TOPICS_DIR.glob("*.md"))
    for md in content:
        if md.stem.startswith("_"):
            continue
        rel = md.relative_to(VAULT_ROOT)
        text = md.read_text(encoding="utf-8", errors="replace")
        fm, fm_err = parse_frontmatter(text)
        if fm_err:
            problems.append(f"BAD FRONTMATTER: {rel} -- {fm_err}")

        in_topics = rel.parts[0] == TOPICS_DIR.name
        in_sources = rel.parts[0] == SOURCES_DIR.name

        for target in {t.strip() for t in WIKILINK_RE.findall(text)}:
            if not target:
                continue
            if target not in notes and target not in all_files:
                if target.lower().endswith(".pdf"):
                    pdf_issues.append(f"BROKEN EMBED: {rel} -> [[{target}]]")
                else:
                    problems.append(f"BROKEN LINK: {rel} -> [[{target}]]")
            elif (in_topics and target in source_citekeys
                  and md.name not in STAGING_FILES):
                # A citation from a staging file is not processing: parking
                # a source in uncategorized.md records why it is waiting,
                # it does not synthesise it. So those sources stay in the
                # ORPHANED list, which makes the lint alone the queue of
                # unprocessed material rather than something to be
                # manually combined with the staging file by hand.
                cited_by[target].add(md.stem)

        if in_sources:
            _check_source(rel, md, fm, problems, pdf_issues)
        elif in_topics and md.name not in STAGING_FILES:
            _check_topic(rel, md, fm, topic_stems, problems, warnings,
                         status_counts, tag_counts)

    check_base_files(problems)
    problems.extend(summarise_pdf_issues(pdf_issues, len(source_citekeys)))

    orphaned = sorted(source_citekeys - set(cited_by))
    if orphaned:
        problems.append(
            f"ORPHANED (not cited by any topic page): {len(orphaned)}"
        )

    multi_homed = {k: sorted(v) for k, v in cited_by.items() if len(v) > 1}

    return {
        "problems": problems,
        "warnings": warnings,
        "orphaned": orphaned,
        "counts": {
            "sources": len(source_citekeys),
            "sources_cited": len(cited_by),
            "topic_pages": len(topic_pages),
            "multi_homed_sources": len(multi_homed),
            "by_tag": dict(tag_counts),
            "by_status": dict(status_counts),
        },
        "multi_homed": multi_homed,
    }


def summarise_pdf_issues(pdf_issues, n_sources):
    """Collapse PDF issues when the whole vault is simply missing its PDFs.

    A vault synced between machines (or cloned from git, where PDFs are
    gitignored) has every source declaring has_pdf: true with no file
    beside it. That is one fact about the machine, not N problems with
    the notes, and reporting it N times hides everything else. When even
    one PDF is present the situation is a genuine per-note mismatch, so
    each is reported individually.
    """
    if not pdf_issues:
        return []
    if list(SOURCES_DIR.glob("*.pdf")):
        return pdf_issues

    declared = sum(1 for i in pdf_issues if i.startswith("has_pdf=true"))
    return [
        f"PDFs ABSENT ON THIS MACHINE: {declared} of {n_sources} source(s) "
        f"declare has_pdf: true, and sources/ holds no PDF at all. Expected "
        f"if the vault was copied or cloned without them (they are "
        f"gitignored). Run the sync adapter here to fetch them, or ignore "
        f"this if you read PDFs elsewhere -- but note a deep read is "
        f"impossible on this machine. ({len(pdf_issues) - declared} dead "
        f"embed(s) folded into this line.)"
    ]


def _check_source(rel, md, fm, problems, pdf_issues):
    """sources/ is machine-maintained; flag anything the adapter got wrong."""
    citekey = fm.get("citekey")
    if not citekey:
        problems.append(f"MISSING citekey: {rel}")
    elif citekey != md.stem:
        problems.append(f"citekey/filename MISMATCH: {rel} has citekey '{citekey}'")
    if not fm.get("title"):
        problems.append(f"MISSING title: {rel}")

    # has_pdf must agree with what is actually on disk, otherwise the
    # embed in the note body is either dead or missing.
    if "has_pdf" in fm:
        actual = list(SOURCES_DIR.glob(f"{md.stem}*.pdf"))
        if fm["has_pdf"] and not actual:
            pdf_issues.append(f"has_pdf=true but no PDF on disk: {rel}")
        if not fm["has_pdf"] and actual:
            pdf_issues.append(
                f"has_pdf=false but PDF(s) exist: {rel} ({[p.name for p in actual]})"
            )


def _check_topic(rel, md, fm, topic_stems, problems, warnings,
                 status_counts, tag_counts):
    """topics/ is agent-maintained; enforce the vocabulary and the tree."""
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    own = [t for t in tags if t in TOPIC_TAGS]
    if not own:
        problems.append(
            f"MISSING topic tag: {rel} -- needs exactly one of {list(TOPIC_TAGS)}"
        )
    elif len(own) > 1:
        problems.append(f"AMBIGUOUS topic tag: {rel} has {own}")
    else:
        tag_counts[own[0]] += 1

    # Non-domain pages must hang off a parent that actually exists, so
    # the tree stays navigable from the domain hubs down.
    parent = fm.get("parent")
    if own and own[0] != "domain":
        if not parent:
            problems.append(f"MISSING parent: {rel} (tag '{own[0]}' requires one)")
        elif parent not in topic_stems:
            problems.append(f"PARENT NOT FOUND: {rel} -> parent '{parent}'")
    elif parent:
        warnings.append(f"domain page with a parent: {rel} -> '{parent}'")

    status = fm.get("status")
    if status is None:
        warnings.append(f"no status field: {rel} (expected one of {list(TOPIC_STATUSES)})")
    elif status not in TOPIC_STATUSES:
        problems.append(f"UNKNOWN status '{status}': {rel}")
    else:
        status_counts[status] += 1

    if len(md.stem.split("-")) > MAX_SLUG_WORDS:
        warnings.append(
            f"long slug ({len(md.stem.split('-'))} words, prefer <={MAX_SLUG_WORDS}): {rel}"
        )


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    ap.add_argument("--quiet", action="store_true", help="problems only, no progress block")
    args = ap.parse_args()

    if not SOURCES_DIR.exists() or not TOPICS_DIR.exists():
        print(f"Not a wiki vault (no sources/ and topics/ under {VAULT_ROOT}).")
        return 1

    r = lint()
    if args.json:
        print(json.dumps(r, indent=2))
        return 1 if r["problems"] else 0

    c = r["counts"]
    if not args.quiet:
        print(f"Vault: {VAULT_ROOT}")
        print(f"  sources:     {c['sources']} ({c['sources_cited']} cited by a topic)")
        print(f"  topic pages: {c['topic_pages']}  "
              f"by tag {dict(sorted(c['by_tag'].items()))}  "
              f"by status {dict(sorted(c['by_status'].items()))}")
        print(f"  sources placed in >1 topic: {c['multi_homed_sources']}")
        if r["orphaned"]:
            shown = ", ".join(r["orphaned"][:15])
            more = f" ... (+{len(r['orphaned']) - 15} more)" if len(r["orphaned"]) > 15 else ""
            print(f"\nUNPROCESSED -- {len(r['orphaned'])} orphaned source(s):\n  {shown}{more}")
        print()

    if r["warnings"] and not args.quiet:
        print(f"{len(r['warnings'])} warning(s) (style, not failures):")
        for w in r["warnings"][:25]:
            print(f"  - {w}")
        if len(r["warnings"]) > 25:
            print(f"  ... (+{len(r['warnings']) - 25} more)")
        print()

    if not r["problems"]:
        print("No problems found.")
        return 0

    print(f"{len(r['problems'])} problem(s):")
    for p in r["problems"]:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
