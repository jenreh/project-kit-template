# Cross-agent skills wiring convention

This repo is the single source of truth for portable [agent skills](https://agentskills.io)
shared across **Claude Code**, **Codex**, and **GitHub Copilot**. The same physical
`SKILL.md` folder is discovered by all three agents — no duplication, no per-agent forks.

## The convention (decisions D3 + D4)

- **Canonical files** live in `skills/<name>/SKILL.md` in this repo.
- **Vendored** into a consuming project under `.agents/agent-skills/` via `git subtree`.
- **Two symlinks** expose them to each agent from one copy:

```
.agents/agent-skills/   # git subtree of jenreh/agent-skills (the whole repo)
.agents/skills          -> agent-skills/skills              # Codex + Copilot read here
.claude/skills          -> ../.agents/agent-skills/skills   # Claude Code reads here
```

Both symlinks are **single-hop** and resolve directly to the real
`.agents/agent-skills/skills` directory — there are no symlink chains, which keeps
discovery reliable across agents and survives a fresh `git clone`.

### Why a wrapper dir + symlinks?

Skills live under `skills/` in this repo (leaving room for a top-level
`.claude-plugin/` marketplace). `git subtree add --prefix <p>` maps the **whole repo**
to `<p>`, so subtreeing straight into `.agents/skills` would nest skills at
`.agents/skills/skills/<name>`. Vendoring into `.agents/agent-skills` and pointing
`.agents/skills` at `agent-skills/skills` gives the flat `.agents/skills/<name>` layout
every agent expects.

## Portable core (D4)

Shared skills use only the portable `SKILL.md` core so the bytes are identical for every
agent:

- Frontmatter: `name` + `description` (write the description as activation triggers,
  "Use when …" — all three agents match on it). Optional `metadata`, `license`,
  `allowed-tools`, `argument-hint` degrade gracefully on agents that don't read them.
- Body: markdown instructions (keep under ~500 lines; push detail into `references/`).
- Optional `scripts/`, `references/`, `assets/` subfolders.

**Not allowed in shared skills:** Claude-only `context: fork` frontmatter, Codex-only
`openai.yaml`. Those break byte-identical reuse. If a skill genuinely needs a Claude-only
feature, keep that variant out of this repo and only in the project's `.claude/skills`.

`task validate` (or `python3 scripts/validate_skills.py`) enforces these rules.

## Verifying discovery per agent

After running `scripts/add-skills.sh` (or the Copier template's `include_skills` task):

- **Claude Code** — open the project, run `/skills` (or ask "list your skills"). The
  skills appear by name.
- **Codex** — run Codex in the project dir; it scans `.agents/skills` and follows the
  symlink.
- **Copilot** — in VS Code agent mode run `/skills`, or `gh copilot`; it resolves
  `.agents/skills`.

Re-verify after a fresh `git clone` to confirm the symlinks survive checkout.
