#!/usr/bin/env python3
"""
wiki_config.py -- single source of truth for where things live.

Nothing in this repo hardcodes a machine-specific path. The vault root
is derived from this file's own location (scripts/ sits directly inside
the vault), so a fresh clone works with no editing at all.

Anything that genuinely varies per machine -- principally where your
reference manager drops its export -- goes in `wiki.config.json` at the
vault root. That file is gitignored. Copy `wiki.config.example.json`
to `wiki.config.json` and edit it only if you use the Zotero adapter.

Stdlib only, by design: a colleague should be able to run the scripts
on a stock Python 3.9+ with nothing installed.
"""

import json
import os
from pathlib import Path

# scripts/ lives directly inside the vault, so the vault is its parent.
# Override with the LLM_WIKI_ROOT environment variable if you relocate
# the scripts (e.g. sharing one copy across several vaults).
VAULT_ROOT = Path(os.environ.get("LLM_WIKI_ROOT", Path(__file__).resolve().parent.parent))

SOURCES_DIR = VAULT_ROOT / "sources"
TOPICS_DIR = VAULT_ROOT / "topics"
TEMPLATES_DIR = VAULT_ROOT / "templates"
CANDIDATES_FILE = VAULT_ROOT / "candidate-sources.md"
CONFIG_FILE = VAULT_ROOT / "wiki.config.json"

# --- vocabulary ------------------------------------------------------
# The three-tier topic scheme. `domain` pages are the top-level map of
# the field, `topic` pages are the leaves that actually hold synthesis,
# and `hub` is an optional middle tier for when one topic grows big
# enough to split into several.
TOPIC_TAGS = ("domain", "hub", "topic")

# Staging files live in topics/ but are not part of the hierarchy, so
# they carry no topic tag, parent or status. `uncategorized.md` holds
# sources that have not clustered yet plus clusters awaiting approval,
# so a proposal survives between sessions.
STAGING_FILES = ("uncategorized.md", "candidate-sources.md")

# Lifecycle of a topic page, so an agent resuming work knows what is
# left to do. See .agents/skills/wiki-bootstrap/SKILL.md.
#   stub    -- created from a quick skim; overview + source list only
#   drafted -- filled in from a deep read of its sources
#   linked  -- cross-linked to sibling topics, multi-homing resolved
TOPIC_STATUSES = ("stub", "drafted", "linked")

DEFAULTS = {
    # Only used by scripts/zotero_sync.py. Leave null if you add
    # sources by hand (see scripts/new_source.py).
    "zotero_export_json": None,
    "zotero_bbt_rpc": "http://localhost:23119/better-bibtex/json-rpc",
    "poll_seconds": 5,
    # Where the sync adapter remembers what it already wrote.
    "state_file": "~/.llm_wiki_sync_state.json",
}


def load_config():
    """Merge wiki.config.json over DEFAULTS. Missing file is fine."""
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            raise SystemExit(f"{CONFIG_FILE.name} is not valid JSON: {e}")
    return cfg


def resolve(value):
    """Expand ~ and make relative paths vault-relative. None stays None."""
    if not value:
        return None
    p = Path(str(value)).expanduser()
    return p if p.is_absolute() else (VAULT_ROOT / p)


# --- frontmatter -----------------------------------------------------
# A deliberately small parser for the flat frontmatter this vault uses
# (`key: value` and `tags: [a, b]`). Using it instead of PyYAML keeps
# the scripts dependency-free. Where real YAML is needed -- validating
# an Obsidian .base file -- we use PyYAML if it happens to be installed
# and skip the check with a note if it is not.

def parse_frontmatter(text):
    """Return (dict, error_or_None). Absent frontmatter -> ({}, None)."""
    if not text.startswith("---"):
        return {}, None
    end = text.find("\n---", 3)
    if end == -1:
        return {}, "frontmatter opened with --- but never closed"
    block = text[text.find("\n", 3) + 1:end]

    fm = {}
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t", "-")):
            continue  # nested/list-item syntax: out of scope, ignored
        if ":" not in line:
            return fm, f"cannot parse frontmatter line: {line!r}"
        key, _, val = line.partition(":")
        fm[key.strip()] = _coerce(val.strip())
    return fm, None


def _coerce(val):
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [_scalar(p.strip()) for p in inner.split(",") if p.strip()]
    return _scalar(val)


def _scalar(val):
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        return val[1:-1]
    low = val.lower()
    if low in ("null", "~", ""):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(val)
    except ValueError:
        return val
