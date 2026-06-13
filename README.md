# kit-template

A single [Copier](https://copier.readthedocs.io/) template for **both** project archetypes —
Python-only services/libraries **and** reflex.dev / AppKit web apps — chosen by a
`project_type` question. Replaces the separate `python-kit` / `projectkit` GitHub templates
with one **updateable** template (`copier update`).

```bash
uv tool install copier
copier copy --trust gh:jenreh/kit-template my-project
cd my-project && task init
```

`--trust` is required (post-gen tasks run `uv sync` and wire `.claude/skills`).

## Questions

| Question | Default | Notes |
|---|---|---|
| `project_name` | — | kebab-case distribution name |
| `project_type` | `python` | `python` (CLI/lib/service) or `reflex` (reflex.dev/AppKit web) |
| `package_name` | from `project_name` | python only; snake_case (reflex always uses `app/`) |
| `project_description` | auto | |
| `author_name` / `github_owner` | jenreh | |
| `python_version` | 3.14 | sets `requires-python` + ruff target |
| `include_db` | false | python: adds SQL deps. reflex: full DB layer (alembic) is always on |
| `db_name` | `{{ project_name }}-db` | asked for reflex / python+db |
| `use_devcontainer` | true | reflex only |
| `include_docker` | reflex→true | Dockerfile+compose (reflex) / docker task |
| `include_terraform` | false | `terraform/` + azure task |
| `include_docs` | python→true | VitePress `docs/` scaffold |
| `include_graph` | false | GraphDB / runic hooks (see note) |
| `include_skills` | true | vendor `jenreh/agent-skills` into `.agents/skills` |

## How it works

- **Shared base** is always generated (pyproject, ruff/mypy/pytest, pre-commit, gitleaks,
  AGENTS/CLAUDE, terraform, `qa`/`release` tasks, `.agents/skills`).
- **`project_type: reflex`** adds the reflex layer: `app/`, `alembic/`, `rxconfig.py`,
  `docker-compose.yml`, `configuration/`, `assets/`, `components/`, `.devcontainer/`,
  `Dockerfile`, reflex deps, `Taskfile.reflex.yml`.
- **Feature flags** are wired two ways:
  - **Files** via Copier's templated `_exclude` (a pattern renders to `""` — matches
    nothing — when its feature is on).
  - **Taskfile includes** are all marked `optional: true` in `Taskfile.dist.yml`, so go-task
    silently skips any `tasks/Taskfile.*.yml` the template didn't ship. You only get the task
    namespaces (`db:`, `docker:`, `dev:`/`prod:`, `reflex:`) for components you selected.
- The python package lives in a whole-segment conditional directory that vanishes for reflex;
  reflex's `app/` is excluded for python.

## Notes

- `Taskfile*.yml` are **not** Jinja-rendered (go-task `{{.VAR}}` would collide); `PROJECT` is
  derived from `pyproject.toml` at runtime.
- **`include_graph`**: the runic skills are vendored, but the PyPI package named `runic` is
  **unrelated** to the graph migration tool — add your graph `runic` from its own source/index
  and pin it in `pyproject.toml`.
- `task test` for **reflex** needs Postgres + `.env` secrets (the app boots against a DB).

## Maintainers

Refresh the bundled skills snapshot with `scripts/sync-skills.sh`, then commit + tag a new
version (generated projects pull it via `copier update`).
