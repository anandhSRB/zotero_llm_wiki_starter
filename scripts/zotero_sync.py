#!/usr/bin/env python3
"""
zotero_sync.py -- OPTIONAL adapter: mirror a Zotero library into sources/.

This is one way to fill sources/. It is not required. If you do not use
Zotero, ignore this file entirely and use scripts/new_source.py instead
(or write your own adapter -- see "Writing another adapter" below).

Writes one markdown note per reference, with any attached PDFs copied
next to the note and embedded in it. Driven by Better BibTeX's
auto-export feature.

ONE-TIME SETUP IN ZOTERO
  1. Install the Better BibTeX (BBT) plugin.
  2. Right-click your library or a collection -> "Export Library..."
     -> format "Better CSL JSON" -> check "Keep updated" -> save it
     somewhere (the folder must already exist).
  3. Zotero Settings > Advanced > enable "Allow other applications on
     this computer to communicate with Zotero", so this script can ask
     BBT for each item's PDF attachments.
  4. Point `zotero_export_json` in wiki.config.json at the file from
     step 2. Copy wiki.config.example.json if you have not already.

RUN
  python3 scripts/zotero_sync.py --once     # one pass, then exit
  python3 scripts/zotero_sync.py            # watch and keep syncing
  python3 scripts/zotero_sync.py --rebuild  # forget state, rewrite all

Only notes whose Zotero metadata actually changed are rewritten, so
re-runs are cheap and idempotent. Use --rebuild after upgrading this
script, since the change detector tracks metadata, not script version.

WRITING ANOTHER ADAPTER
Any adapter only has to do two things: write `sources/<citekey>.md`
with the frontmatter contract in templates/source-note.md, and keep
`citekey` equal to the filename stem. `scripts/wiki_lint.py` enforces
exactly that, so a Mendeley/Paperpile/plain-BibTeX adapter is a drop-in
replacement for this file.

Stdlib only. No pip install required.
"""

import argparse
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_config import SOURCES_DIR, load_config, resolve  # noqa: E402

# sources/_index.base is a Bases *view definition*, not generated data.
# It is written once if missing and never overwritten, so anything you
# change through Obsidian's Bases UI -- adding a view, dragging columns,
# editing a filter -- survives every future sync.
BASE_FILE_CONTENT = """\
# Filterable/sortable view over every source in this vault.
#
# Written once by zotero_sync.py if missing, then never overwritten --
# so edits you make here, or through Obsidian's Bases UI (the Filters
# button, dragging columns, adding views), are permanent.
#
# Click a column header to sort. Use the Filters button, or edit the
# `filters:` blocks below, to narrow what shows up -- for example add
# 'year >= 2020' or 'tags.contains("your-tag")'.

filters:
  and:
    - file.inFolder("sources")
    - 'file.ext == "md"'

views:
  - type: table
    name: "All sources"
    order:
      - file.name
      - title
      - authors
      - year
      - pub_type
      - journal
      - tags
      - doi
      - has_pdf

  - type: table
    name: "Missing PDF"
    filters:
      and:
        - "!has_pdf"
    order:
      - file.name
      - title
      - authors
      - year

  - type: table
    name: "By type"
    groupBy:
      property: pub_type
      direction: ASC
    order:
      - file.name
      - title
      - year
      - journal
"""


def ensure_base_file():
    base = SOURCES_DIR / "_index.base"
    if not base.exists():
        base.write_text(BASE_FILE_CONTENT, encoding="utf-8")
        print(f"Created {base.name}")


def load_state(state_file):
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"fingerprints": {}, "export_mtime": 0}


def save_state(state_file, state):
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state), encoding="utf-8")


def get_pdf_paths(rpc_url, citekey):
    """Ask Better BibTeX for this item's attachments; return PDF paths."""
    payload = json.dumps(
        {"jsonrpc": "2.0", "method": "item.attachments", "params": [citekey]}
    ).encode("utf-8")
    req = urllib.request.Request(
        rpc_url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8")).get("result", [])
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError) as e:
        print(f"  (attachment lookup failed for {citekey}: {e})")
        return []
    return [
        att.get("path", "")
        for att in result
        if str(att.get("path", "")).lower().endswith(".pdf")
    ]


def entry_fields(entry):
    title = entry.get("title", "Untitled")
    authors = ", ".join(
        f"{a.get('given', '')} {a.get('family', '')}".strip()
        for a in entry.get("author", [])
    ) or "Unknown"
    date_parts = entry.get("issued", {}).get("date-parts", [[None]])
    raw_year = date_parts[0][0] if date_parts and date_parts[0] else None
    try:
        year = int(raw_year) if raw_year is not None else None
    except (TypeError, ValueError):
        year = None  # some items export a non-numeric year, e.g. "forthcoming"
    return title, authors, year


def _q(val):
    """Quote a value for single-line YAML without needing a YAML writer."""
    return '"' + str(val).replace("\\", "\\\\").replace('"', '\\"') + '"'


def note_body(entry, citekey, pdf_filenames):
    title, authors, year = entry_fields(entry)
    keyword = entry.get("keyword") or ""
    tags = [t.strip() for t in keyword.split(",") if t.strip()]
    has_pdf = bool(pdf_filenames)

    lines = [
        "---",
        f"citekey: {_q(citekey)}",
        f"title: {_q(title)}",
        f"authors: {_q(authors)}",
        f"year: {year if year else 'null'}",
        f"tags: [{', '.join(tags)}]",
        f"doi: {_q(entry.get('DOI', ''))}",
        f"pub_type: {_q(entry.get('type', ''))}",
        f"journal: {_q(entry.get('container-title', ''))}",
        f"url: {_q(entry.get('URL', ''))}",
        f"has_pdf: {'true' if has_pdf else 'false'}",
        "---",
        "",
        f"# {title}",
        "",
        f"**{authors}** ({year or 'n.d.'})",
        "",
        "## Abstract",
        entry.get("abstract") or "_No abstract._",
        "",
        "## Notes",
        "",
        "## PDF",
    ]
    lines += [f"![[{n}]]" for n in pdf_filenames] or ["_No PDF attached._"]
    return "\n".join(lines) + "\n"


def sync_once(cfg, export_path, state_file, state):
    if not export_path.exists():
        return state
    mtime = export_path.stat().st_mtime
    if mtime == state.get("export_mtime"):
        return state  # nothing changed since the last check

    try:
        data = json.loads(export_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return state  # BBT is mid-write; try again on the next poll

    items = data.get("items", data) if isinstance(data, dict) else data
    fingerprints = state.get("fingerprints", {})
    rpc_url = cfg["zotero_bbt_rpc"]

    for entry in items:
        citekey = entry.get("id")
        if not citekey:
            continue
        fingerprint = json.dumps(entry, sort_keys=True)
        if fingerprints.get(citekey) == fingerprint:
            continue  # unchanged since the last sync

        pdf_filenames = []
        for i, src in enumerate(p for p in get_pdf_paths(rpc_url, citekey) if Path(p).exists()):
            dest = SOURCES_DIR / f"{citekey}{'' if i == 0 else f'-{i + 1}'}.pdf"
            if not dest.exists():
                shutil.copy2(src, dest)
                print(f"  linked PDF: {dest.name}")
            pdf_filenames.append(dest.name)

        (SOURCES_DIR / f"{citekey}.md").write_text(
            note_body(entry, citekey, pdf_filenames), encoding="utf-8"
        )
        print(f"Updated note: {citekey}.md")
        fingerprints[citekey] = fingerprint

    state["fingerprints"] = fingerprints
    state["export_mtime"] = mtime
    save_state(state_file, state)
    return state


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--once", action="store_true", help="one pass, then exit")
    ap.add_argument("--rebuild", action="store_true",
                    help="discard sync state so every note is rewritten")
    args = ap.parse_args()

    cfg = load_config()
    export_path = resolve(cfg.get("zotero_export_json"))
    if not export_path:
        raise SystemExit(
            "No `zotero_export_json` set in wiki.config.json.\n"
            "Copy wiki.config.example.json to wiki.config.json and point it at\n"
            "your Better BibTeX auto-export, or add sources by hand with\n"
            "  python3 scripts/new_source.py --help"
        )

    state_file = resolve(cfg["state_file"])
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    ensure_base_file()

    if args.rebuild and state_file.exists():
        state_file.unlink()
        print("Discarded sync state; every note will be rewritten.")

    state = load_state(state_file)
    if not export_path.exists():
        print(f"Waiting for export file to appear: {export_path}")

    print(f"Watching {export_path}")
    print(f"Writing notes to {SOURCES_DIR}")
    while True:
        state = sync_once(cfg, export_path, state_file, state)
        if args.once:
            return 0
        time.sleep(cfg["poll_seconds"])


if __name__ == "__main__":
    sys.exit(main())
