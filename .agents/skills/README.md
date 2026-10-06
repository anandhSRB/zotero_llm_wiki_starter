# Skills

Four workflows, agent-agnostic. Canonical copies live here; everything
else points at them.

| Skill | Use when |
|---|---|
| `wiki-bootstrap` | `topics/` is empty and `sources/` has content — the gated first build |
| `wiki-update` | new sources appeared; fold them into an existing structure |
| `wiki-lint` | check integrity and act on what the lint reports |
| `wiki-find-sources` | look for literature not yet in the library |

Each is a plain Markdown file with YAML frontmatter (`name`,
`description`) and instructions in the body. No tool-specific syntax, so
any agent that can read a Markdown file can follow one.

## Wiring up your agent

**Claude Code** — already wired. `.claude/skills/<name>/SKILL.md` carries
the same frontmatter and points here, so `/wiki-bootstrap` and friends
work out of the box.

**Cursor, Codex, Copilot, Gemini CLI, Aider, and others that read
`AGENTS.md`** — already wired. `AGENTS.md` sits at the vault root and
names all four skills with their paths; the agent reads the one it needs.

**An agent with no skill mechanism at all** — paste the file. The skills
are self-contained prose:

> Read `AGENTS.md` and `.agents/skills/wiki-bootstrap/SKILL.md` in this
> vault, then follow the bootstrap workflow.

**A tool that wants its own directory** (`.cursor/rules/`,
`.github/copilot-instructions.md`, `.gemini/`) — add a pointer like the
ones in `.claude/skills/`, naming the canonical path. Keep one source of
truth; duplicated instructions drift.

## Regenerating the pointers

After editing a canonical skill's frontmatter, refresh the Claude Code
pointers so the descriptions stay in sync:

```bash
python3 scripts/sync_skill_pointers.py
```

## Adding a skill

Create `.agents/skills/<name>/SKILL.md` with `name` and `description`
frontmatter, add a row to the table above and to the table in
`AGENTS.md`, then run the command above.

Write the `description` to say **when to use it**, not just what it does —
that is what an agent matches against when deciding whether to reach for
it.
