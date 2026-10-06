# Templates

These record the **frontmatter contract** that `scripts/wiki_lint.py`
enforces. They are reference, not something Obsidian inserts for you.

| Template | Contract for | Written by |
|---|---|---|
| `source-note.md` | `sources/*.md` | the sync adapter or `new_source.py` — **never by hand or by an agent** |
| `domain-page.md` | `topics/*.md` with `tags: [domain]` | an agent, with your approval |
| `topic-page.md` | `topics/*.md` with `tags: [topic]` or `[hub]` | an agent |

## Why sources/ is off-limits to agents

`sources/` is a projection of your reference manager. Anything written
there by hand is overwritten the next time the adapter runs. If a source
note looks wrong, that is an adapter bug to fix in `scripts/`, not a file
to patch.

The one exception is the `## Notes` section, which the adapter leaves
alone — but prefer putting your thinking in a topic page, where it is
linked and discoverable, over burying it in a single source note.

## The three tiers

- **`domain`** — a top-level area of your field. The map, not the
  territory: an overview plus links to its sub-topics. 3–8 of these.
- **`hub`** — optional middle tier, created only when one topic grows
  big enough to split. Same shape as a domain page, but has a `parent`.
- **`topic`** — a leaf. This is where synthesis actually lives, and the
  only tier that carries a `## Sources` list.

Every non-`domain` page needs a `parent` that exists, so the tree stays
walkable from the domain pages down.
