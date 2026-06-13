# agent-skills

Canonical, portable [agent skills](https://agentskills.io) shared across **Claude Code**,
**Codex**, and **GitHub Copilot** — a single source of truth, vendored into projects via
`git subtree` and wired so every agent resolves the same physical files.

Each skill is a `skills/<name>/SKILL.md` folder using only the portable core (name +
description + markdown, with optional `scripts/`, `references/`, `assets/`). No Claude-only
or Codex-only frontmatter, so the bytes are identical for every agent.

## What's here

```
skills/<name>/SKILL.md   # 27 portable skills
scripts/
  add-skills.sh          # vendor + wire into any repo (one command)
  validate_skills.py      # portable-core validator (run in CI)
Taskfile.yml             # task validate | task list
docs/cross-agent-skills.md
.claude-plugin/, plugins/  # optional Claude Code marketplace layer
```

Run `task list` to see every skill and its trigger description, or `task validate` to check
portability.

## Consume it

### Any repo (all three agents) — recommended

```bash
curl -fsSL https://raw.githubusercontent.com/jenreh/agent-skills/main/scripts/add-skills.sh | bash
# or, if you've already cloned this repo:
bash scripts/add-skills.sh
```

This vendors the repo via `git subtree` into `.agents/agent-skills/` and creates two
symlinks so each agent finds the skills from one copy:

```
.agents/skills  -> agent-skills/skills              # Codex + Copilot
.claude/skills  -> ../.agents/agent-skills/skills   # Claude Code
```

Update later:

```bash
git subtree pull --prefix .agents/agent-skills https://github.com/jenreh/agent-skills.git main --squash
```

See [docs/cross-agent-skills.md](docs/cross-agent-skills.md) for the full convention.

### Per-agent native paths

- **Claude Code** — `/plugin marketplace add gh:jenreh/agent-skills` then `/plugin install`
  (see the [marketplace layer](#claude-code-marketplace-optional)), or just run
  `add-skills.sh`.
- **Codex** — run `add-skills.sh`; Codex scans `.agents/skills` and follows the symlink.
- **GitHub Copilot** — run `add-skills.sh`, or drop skills into `.github/skills`.

### Copier templates

The [python-kit-template](https://github.com/jenreh/python-kit-template) and
[project-kit-template](https://github.com/jenreh/project-kit-template) Copier templates
wire these skills automatically when you answer `include_skills: true`.

## Claude Code marketplace (optional)

For ad-hoc Claude-only projects, skills are also grouped into installable plugins:

```text
/plugin marketplace add gh:jenreh/agent-skills
/plugin install jenreh-core@jenreh        # boost, commit-msg, create-readme, …
/plugin install jenreh-python@jenreh      # python-coding, runic, docker, …
/plugin install jenreh-reflex@jenreh      # appkit + reflex skills
/plugin install jenreh-terraform@jenreh   # terraform-*
```

Plugin updates are refresh + reinstall (`/plugin marketplace update`, then reinstall);
plugin skills are namespaced, e.g. `jenreh-core:boost`. The plugins **symlink** back to the
canonical `skills/` folders, so nothing is duplicated.

## Develop

```bash
task validate   # enforce portable core (also runs in CI on every PR)
task list       # list skills + descriptions
```

The bundled validator is self-contained. The hosted validators at
[agentskills.io](https://agentskills.io) / skills.sh are stricter on some optional fields —
run `npx skills validate` if you want the full check.

## License

MIT — see [LICENSE](LICENSE). Individual skills may carry their own license file
(e.g. `frontend-design/LICENSE.txt`); those take precedence for that skill.
