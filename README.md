# ProjectKit Template

A single [Copier](https://copier.readthedocs.io/) template for **both** project archetypes —
Python-only services/libraries **and** reflex.dev / AppKit web apps — chosen by a
`project_type` question. Replaces GitHub templates
with one **updateable** template (`copier update`).

```bash
uv tool install copier
copier copy --trust gh:jenreh/kit-template my-project
cd my-project && task init
```

`--trust` is required (post-gen tasks run `uv sync`, and with `create_github_repo` also
`scripts/github_publish.py`). `--trust` runs code from the template, so only use it with a template you trust. Add
`--vcs-ref <tag>` to pin the version.

## `projectkit` shell helper (optional)

Drop this in your `~/.zshrc` so `projectkit my-project` scaffolds from this template
(an explicit template ref is passed through; anything else is treated as the destination):

```zsh
projectkit() {
  local default="gh:jenreh/kit-template"
  local tmpl

  case "$1" in
#    py)  tmpl="gh:jenreh/kit-template"; shift ;;
#    web) tmpl="gh:jenreh/web-template"; shift ;;
    gh:*|git+*|https://*|/*|.*)         # explicit ref → consume it
         tmpl="$1"; shift ;;
    *)   tmpl="$default" ;;             # anything else → default, keep $1 as dest
  esac

  copier copy --trust "$tmpl" "$@"
}
```

## Questions

| Question | Default | Notes |
|---|---|---|
| `project_name` | — | kebab-case distribution name |
| `project_type` | `python` | `python` (CLI/lib/service) or `reflex` (reflex.dev/AppKit web) |
| `package_name` | from `project_name` | python only; snake_case (reflex always uses `app/`) |
| `project_description` | auto | |
| `author_name` / `github_owner` | jenreh | |
| `python_version` | 3.14 | sets `requires-python` + ruff target |
| `include_db` | false | adds SQL deps **+ Alembic** (pure `env.py`). reflex always includes the DB layer (appkit `env.py`) |
| `db_name` | `{{ project_name }}-db` | asked for reflex / python+db |
| `use_devcontainer` | true | any project type (db service included only when there's a DB) |
| `include_docker` | reflex→true | Dockerfile+compose (reflex) / docker task; ships `.dockerignore` |
| `devcontainer_docker` | false | asked with devcontainer + docker: mounts the host Docker daemon into the dev container (docker-outside-of-docker). That is root on the host for everything in the container, agents included |
| `include_terraform` | false | `terraform/` scaffold + cloud deploy task |
| `cloud_provider` | `azure` | asked when `include_terraform`; `azure` or `aws` (renders `terraform/deploy.py` for it) |
| `include_docs` | python→true | `docs/` folder for plain Markdown (templated `index.md`) |
| `include_graph` | false | GraphDB / runic hooks (see note) |
| `coding_agents` | `[claude]` | multi-select: `claude` (Claude Code), `copilot` (GitHub Copilot), `codex` (OpenAI Codex). Adds each CLI and VS Code extension to the dev container, persists its login, and installs the plugins into it |
| `agent_plugins` | `[jenreh]` | multi-select, asked when an agent is chosen: `jenreh` ([jenreh/agent-skills](https://github.com/jenreh/agent-skills)), `superpowers` ([obra/superpowers](https://github.com/obra/superpowers)), `mattpocock` ([mattpocock/skills](https://github.com/mattpocock/skills)) |
| `create_github_repo` | false | post-gen `scripts/github_publish.py`: creates the GitHub repo, pushes, and applies rulesets + security (needs an authenticated `gh`) |
| `github_visibility` | `private` | asked when `create_github_repo`; `private` or `public` |

## How it works

- **Shared base** is always generated (pyproject, ruff/mypy/pytest, pre-commit, betterleaks,
  AGENTS/CLAUDE, `qa`/`release` tasks, `.agents/skills/` for project skills with
  `.claude/skills` linked to it). When `create_github_repo` is on, the last post-gen tasks
  commit and run `scripts/github_publish.py`.
- **GitHub baseline**: repository settings are not files, so no template (Copier or a
  GitHub template repo) can copy them. The project keeps them as code instead:
  `.github/rulesets/*.json` and `scripts/github_harden.py`, both updated by
  `copier update` like every other file. `scripts/github_publish.py` runs
  `gh repo create --source . --push` and then the harden script. That sets up two
  rulesets (the default branch only changes through a reviewed pull request with the
  `00 Security checks` jobs required and a CodeQL gate; new branches must follow
  `BRANCHING.md`), Dependabot alerts and security updates, Advanced Security, secret
  scanning with push protection, CodeQL default setup, private vulnerability reporting,
  and a read-only `GITHUB_TOKEN`. For a project generated without `create_github_repo`,
  commit and run `python scripts/github_publish.py owner/repo private` later. Public repos get
  all of it for free; private repos need a paid plan for rulesets and GitHub Secret
  Protection / Code Security for secret and code scanning. The script skips what is
  missing and prints what is on. Run `python scripts/github_harden.py` again after
  changing a ruleset JSON; it updates everything in place.
- **Agent plugins**: `.claude/settings.json` is the single list of plugin marketplaces
  (`extraKnownMarketplaces`) and plugins (`enabledPlugins`). Claude Code offers them when
  the folder is trusted, and VS Code Copilot reads the same file (`chat.plugins.enabled`).
  `scripts/install_agent_plugins.py` (`task agents:plugins`) installs them into the chosen
  agent CLIs; `task init` and every dev container attach run it. The jenreh plugins follow
  the answers: `jenreh-core`, `-python`, `-tools` always, `-reflex` + `-design` for reflex,
  `-terraform` with `include_terraform`, `-graphdb` with `include_graph`.
- **Dev container**: zsh with antidote (Zephyr + `jenreh/zsh-utils`) and starship; fzf,
  zoxide, go-task and uv pinned in `.devcontainer/Dockerfile`. A `<project>-dev-state`
  volume at `~/.persist` keeps the uv/pre-commit/antidote caches, uv-managed Python and the
  agent logins and plugins (`~/.claude`, `~/.copilot`, `~/.codex`) across rebuilds.
- **`project_type: reflex`** adds the reflex layer: `app/`, `alembic/`, `rxconfig.py`,
  `docker-compose.yml`, `configuration/`, `assets/`, `components/`, `.devcontainer/`,
  `Dockerfile`, reflex deps, `Taskfile.reflex.yml`.
- **Feature flags** are wired two ways:
  - **Files** via Copier's templated `_exclude` (a pattern renders to `""` — matches
    nothing — when its feature is on).
  - **Taskfile includes** are all marked `optional: true` in `Taskfile.dist.yml`, so go-task
    silently skips any `taskfiles/Taskfile.*.yml` the template didn't ship. You only get the task
    namespaces (`db:`, `docker:`, `dev:`/`prod:`, `reflex:`) for components you selected.
- The python package lives in a whole-segment conditional directory that vanishes for reflex;
  reflex's `app/` is excluded for python.

## Notes

- `Taskfile*.yml` are **not** Jinja-rendered (go-task `{{.VAR}}` would collide); `PROJECT` is
  derived from `pyproject.toml` at runtime.
- **`include_graph`**: adds `runic-py` (graph schema migrations + OGM for Cypher DBs) to
  dependencies and surfaces the `runic-*` skills in AGENTS.md (the skills themselves come
  with the `jenreh-graphdb` plugin when `jenreh` is in `agent_plugins`). (Note: `include_graph` relaxes the
  `typer` pin to `>=0.26.0`, which `runic-py` requires.)
- **Alembic** works for both archetypes: `alembic/env.py` is rendered as the appkit-coupled
  variant for reflex, or a pure SQLAlchemy variant (reads `$DATABASE_URL` / `alembic.ini`) for
  Python — so `task db:*` is usable in both.
- `task test` for **reflex** needs Postgres + `.env` secrets (the app boots against a DB).
- **`include_terraform`**: ships the `terraform/` scaffold. `terraform/deploy.py` is one
  script for both clouds; `cloud_provider` sets its `CLOUD` constant (change it to switch
  clouds later). It checks the cloud login itself, so the `dev:`/`prod:` tasks just call it.
- **Scripts**: scripts that run on the host (`scripts/*.py`, `terraform/deploy.py`) are
  standard-library Python, so they run the same on Linux, macOS and Windows. Scripts that
  only run inside a container (`start.sh`, `.devcontainer/post-create.sh`) stay bash.
- **`.dockerignore`** ships whenever `include_docker` is on; its contents branch on
  `project_type` (reflex `.web`/build artifacts vs. plain Python).
- **Security**: generated projects are secure by default and ship a `SECURITY.md` with a
  deployment checklist. Reflex projects have **no default accounts**: `task admin:bootstrap`
  creates the first admin from `mn-admin-email` / `mn-admin-password`. Updating an older
  project with `copier update` adds a migration that deactivates the old shared `admin`
  account if its password was never changed.

## Maintainers

Skills are not vendored into this template or into generated projects. They come from
plugin marketplaces, which the agent CLIs keep up to date. To change the skill set, edit
the upstream marketplace. To offer another marketplace, add a choice to `agent_plugins` in
`copier.yml` and its entries to `template/.claude/settings.json.jinja`.

`obra/superpowers` is installed from its Claude Code marketplace
[`obra/superpowers-marketplace`](https://github.com/obra/superpowers-marketplace)
(`superpowers@superpowers-marketplace`), which the upstream README recommends for Claude
Code and Copilot CLI. The marketplace inside `obra/superpowers` itself is the dev channel.

Versions of tools live in the templates: GitHub Actions by SHA in `.github/workflows/`, uv and
bun by digest in `Dockerfile.jinja`, go-task, fzf, zoxide and starship by checksum and
antidote by commit in `.devcontainer/Dockerfile.jinja`.
Dependabot only updates them in generated projects, so refresh them here when you update the
template.
