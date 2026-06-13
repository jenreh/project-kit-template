# Changelog

All notable changes to this repo are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions are git tags.

## [Unreleased]

## [0.1.0] - 2026-06-13

### Added

- Initial canonical, portable agent-skills repo: single source of truth for skills
  shared across Claude Code, Codex, and GitHub Copilot.
- 27 skills migrated from `jenreh/project-kit` (a strict superset of `python-kit`),
  all verified portable-core (no Claude-only / Codex-only frontmatter).
- `scripts/add-skills.sh` — one-command vendor + cross-agent wiring (`git subtree`
  into `.agents/agent-skills` + `.agents/skills` / `.claude/skills` symlinks).
- `scripts/validate_skills.py` + `task validate` + GitHub Actions `validate` workflow.
- `docs/cross-agent-skills.md` documenting the D3/D4 conventions.
- Optional Claude Code marketplace layer (`.claude-plugin/marketplace.json`,
  `plugins/jenreh-{core,python,reflex,terraform}`) with skills symlinked back to
  `skills/` (no duplication).
