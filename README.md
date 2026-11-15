<!-- prettier-ignore -->
<div align="center">

# ProjectKit Template

[![Copier](https://img.shields.io/badge/Copier-template-1f6feb?style=flat-square)](https://copier.readthedocs.io/)
![Python](https://img.shields.io/badge/Python-3.14%20%7C%203.15-3776ab?style=flat-square&logo=python&logoColor=white)
[![uv](https://img.shields.io/badge/uv-managed-de5fe9?style=flat-square)](https://docs.astral.sh/uv/)
[![Task](https://img.shields.io/badge/Task-runner-29beb0?style=flat-square&logo=task&logoColor=white)](https://taskfile.dev/)
[![Reflex](https://img.shields.io/badge/Reflex-AppKit-5646ed?style=flat-square)](https://reflex.dev/)

One updatable Copier template for Python services, libraries and reflex.dev / AppKit web apps.

[Quick start](#quick-start) • [Features](#features) • [Questions](#template-questions) • [Tasks](#everyday-tasks) • [Updating](#updating-a-project) • [How it works](#how-it-works)

</div>

ProjectKit is a single [Copier](https://copier.readthedocs.io/) template for two kinds of projects. You pick one with the `project_type` question:

- **`python`**: a CLI, library or service with a plain Python package.
- **`reflex`**: a [reflex.dev](https://reflex.dev/) web app built on AppKit, with Postgres, Alembic, login and an admin bootstrap.

Both share the same base: uv, ruff, ty, pytest, pre-commit with secret scanning, go-task, CI workflows, a dev container and coding agent setup. Unlike a GitHub template repository, a generated project stays linked to this template, so `copier update` brings later template changes into it.

> [!TIP]
> Every feature is a question. Answer "no" and the files, dependencies and task namespaces for it are left out of the project.

## Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/), [Task](https://taskfile.dev/installation/) and Git. For `create_github_repo` you also need an authenticated [GitHub CLI](https://cli.github.com/) (`gh auth login`).

```bash
uv tool install copier
copier copy --trust gh:jenreh/project-kit-template my-project
cd my-project && task init
```

`task init` installs the pinned Python version, syncs the dependencies, installs the pre-commit hooks and, when you chose a coding agent, installs the agent plugins. Then:

| Project type | Next step |
|---|---|
| `python` | `task test` |
| `reflex` | `cp .env.default .env`, set the `mn-db-*` values, start Postgres and create the database, then `task db:upgrade`. Set `mn-admin-email` and `mn-admin-password` in `.env`, then `task admin:bootstrap && task run`. |

> [!WARNING]
> `--trust` is required because the template runs commands after generation (`git init`, `uv sync` and, with `create_github_repo`, `scripts/github_publish.py`). It runs code from the template on your machine, so only use it with a template you trust. Add `--vcs-ref <tag>` to pin a template version.

## Features

- **Two project types, one template**: Python package or reflex.dev / AppKit web app, with a shared base and a reflex layer on top.
- **Quality tooling ready to run**: ruff, [ty](https://github.com/astral-sh/ty), pytest with coverage, pre-commit, betterleaks secret scanning and a dependency audit, all behind `task` commands.
- **CI and security checks**: GitHub Actions for lint and test, secret scanning, dependency audit and static analysis, plus optional Docker image and PyPI publishing. Actions are pinned by SHA and Dependabot keeps them current.
- **GitHub baseline as code**: rulesets in `.github/rulesets/` and a hardening script that turns on branch protection, secret scanning with push protection, Dependabot and AI Scan, plus a CodeQL workflow.
- **Dev container**: zsh, starship, fzf, zoxide, go-task and uv, with a volume that keeps caches, Python and agent logins across rebuilds.
- **Coding agents**: Claude Code, GitHub Copilot and OpenAI Codex, each with its CLI, VS Code extension and plugin marketplaces set up for you.
- **Optional extras**: SQL database with Alembic, Docker, Terraform for Azure or AWS, a `docs/` folder and GraphDB support with runic-py.
- **Cross-platform**: host scripts are standard-library Python and the Taskfiles avoid Unix-only tools, so they work on Linux, macOS and Windows.

## Template questions

| Question | Default | Notes |
|---|---|---|
| `project_name` | | kebab-case distribution name |
| `project_type` | `python` | `python` (CLI, library, service) or `reflex` (reflex.dev / AppKit web app) |
| `package_name` | from `project_name` | Python only, snake_case. Reflex always uses `app/`. |
| `project_description` | auto | one line |
| `author_name`, `github_owner` | jenreh | |
| `python_version` | `3.14` | `3.14` or `3.15`. Sets `requires-python` and the ruff target. |
| `include_db` | `false` | Python only. Adds SQL dependencies and Alembic with a plain `env.py`. Reflex always has the DB layer. |
| `db_name` | `<project_name>-db` | asked for reflex, or Python with `include_db` |
| `use_devcontainer` | `true` | any project type. The DB service is added only when there is a database. |
| `include_docker` | `true` for reflex | Dockerfile and compose for reflex, a docker task for Python. Ships a `.dockerignore`. |
| `devcontainer_docker` | `false` | asked with dev container and Docker. Mounts the host Docker daemon into the dev container. |
| `include_terraform` | `false` | `terraform/` scaffold and the `dev:` / `prod:` deploy tasks |
| `cloud_provider` | `azure` | asked with `include_terraform`. `azure` or `aws`. |
| `include_docs` | `true` for Python | `docs/` folder for plain Markdown |
| `include_graph` | `false` | adds runic-py for graph schema migrations and an OGM for Cypher databases |
| `coding_agents` | `[claude]` | multi-select: `claude`, `copilot`, `codex` |
| `agent_plugins` | `[jenreh]` | multi-select, asked when an agent is chosen: [`jenreh`](https://github.com/jenreh/agent-skills), [`superpowers`](https://github.com/obra/superpowers), [`mattpocock`](https://github.com/mattpocock/skills) |
| `create_github_repo` | `false` | creates the GitHub repo, pushes and applies the GitHub baseline |
| `github_visibility` | `private` | asked with `create_github_repo`. `private` or `public`. |

> [!CAUTION]
> `devcontainer_docker` gives everything inside the dev container, coding agents included, root access to the host. Leave it off and run the docker tasks on the host unless you need them inside the container.

## Everyday tasks

Run `task` in a generated project to list everything. You only get the namespaces for the features you chose.

| Task | What it does |
|---|---|
| `task init` | install Python, sync dependencies, install pre-commit hooks and agent plugins |
| `task test` / `lint` / `format` / `typecheck` | pytest with coverage, ruff and ty |
| `task pre-commit` | run all hooks, including betterleaks, on every file |
| `task audit` | check the locked dependencies for known vulnerabilities |
| `task upgrade` | upgrade dependencies within the `pyproject.toml` ranges, then sync and audit |
| `task release:build -- [major\|minor\|patch]` | bump the version, push and create a GitHub release |
| `task agents:plugins` | install the plugins from `.claude/settings.json` into the agent CLIs |
| `task run` / `run:debug` / `run:prod` | start the reflex app (reflex) |
| `task admin:bootstrap` | create the first administrator (reflex) |
| `task db:upgrade` / `db:revision` / `db:downgrade` | Alembic migrations (reflex, or Python with `include_db`) |
| `task docker:build` / `docker:test` | build and check the Docker image |
| `task dev:bootstrap` / `dev:migrate` / `dev:status` | Terraform state setup, deploy and status (same under `prod:`) |

> [!NOTE]
> `task test` in a reflex project needs Postgres and the secrets in `.env`, because the app boots against a database.

## Updating a project

Inside a generated project, pull in the latest template changes with:

```bash
copier update --trust
```

Copier merges template changes with your own edits and asks about any new questions. This also applies to the GitHub settings, CI workflows and dev container, because they all live in the project as files.

## How it works

<details>
<summary><b>Feature flags</b></summary>

Features are wired in two ways:

- **Files** are left out with Copier's templated `_exclude`. Each pattern renders to an empty string, which matches nothing, when its feature is on. The Python package lives in a conditional directory name that disappears for reflex, and reflex's `app/` is excluded for Python.
- **Task namespaces** are switched on in the `includes` block of `Taskfile.dist.yml`. Copier writes active includes for the features you chose and leaves the others commented out, so you can turn one on later by uncommenting it.

`Taskfile*.yml` files are not rendered with Jinja, because go-task's `{{.VAR}}` syntax would collide. `PROJECT` is read from `pyproject.toml` at run time.

</details>

<details>
<summary><b>GitHub baseline</b></summary>

Repository settings are not files, so no template can copy them. The project keeps them as code instead: `.github/rulesets/*.json` and `scripts/github_harden.py`, both updated by `copier update`.

`scripts/github_publish.py` runs `gh repo create --source . --push` and then the hardening script, which sets up:

- a ruleset that only allows changes to the default branch through a reviewed pull request, with the `02 Security checks` jobs required and a CodeQL gate
- a ruleset that enforces the branch names in `BRANCHING.md`
- Dependabot alerts and security updates, Advanced Security, secret scanning with push protection, AI Scan for the repository and pull requests, and private vulnerability reporting
- a read-only `GITHUB_TOKEN`

CodeQL runs from `.github/workflows/03_codeql.yml` (advanced setup), so the script turns GitHub's CodeQL default setup off. AI Scan uses AI credits on every pull request. GitHub has no API for malware alerts, automatic dependency submission and scan for AI applications; the script ends with a link to the settings page where you turn them on.

For a project generated without `create_github_repo`, commit and run `uv run python scripts/github_publish.py owner/repo private` later. Run `python scripts/github_harden.py` again after you change a ruleset; it updates everything in place.

> [!NOTE]
> Public repositories get all of this for free. Private repositories need a paid plan for rulesets, and GitHub Secret Protection and Code Security for secret and code scanning. The script skips what is missing and prints what it turned on.

</details>

<details>
<summary><b>Coding agents and plugins</b></summary>

`.claude/settings.json` is the single list of plugin marketplaces (`extraKnownMarketplaces`) and plugins (`enabledPlugins`). Claude Code offers them when you trust the folder, and VS Code Copilot reads the same file (`chat.plugins.enabled`). `scripts/install_agent_plugins.py` installs them into each chosen agent CLI. `task init` and every dev container attach run it.

The jenreh plugins follow your answers:

| Plugin | When |
|---|---|
| `jenreh-core`, `jenreh-python`, `jenreh-tools` | always |
| `jenreh-reflex`, `jenreh-design` | `project_type: reflex` |
| `jenreh-terraform` | `include_terraform` |
| `jenreh-graphdb` | `include_graph` |

Skills that only matter for one project go in `.agents/skills/`. Codex and Copilot read that folder directly, and `.claude/skills` links to it for Claude Code.

</details>

<details>
<summary><b>Dev container</b></summary>

The container uses zsh with antidote (Zephyr and `jenreh/zsh-utils`) and starship. fzf, zoxide, go-task and uv are pinned in `.devcontainer/Dockerfile`. A `<project>-dev-state` volume mounted at `~/.persist` keeps the uv, pre-commit and antidote caches, the uv-managed Python and the agent logins and plugins (`~/.claude`, `~/.copilot`, `~/.codex`) across rebuilds.

</details>

<details>
<summary><b>Optional features in detail</b></summary>

- **Database**: `alembic/env.py` is rendered for AppKit in reflex projects, or as a plain SQLAlchemy variant that reads `$DATABASE_URL` or `alembic.ini` in Python projects. `task db:*` works in both.
- **Terraform**: `terraform/deploy.py` is one script for both clouds. `cloud_provider` sets its `CLOUD` constant, which you can change later to switch clouds. It checks the cloud login itself, so the `dev:` and `prod:` tasks just call it.
- **GraphDB**: `include_graph` adds `runic-py` to the dependencies and points to the `runic-*` skills in `AGENTS.md`. The skills come with the `jenreh-graphdb` plugin. It also relaxes the `typer` pin to `>=0.26.0`, which runic-py needs.
- **Docker**: `.dockerignore` ships whenever `include_docker` is on, and its contents depend on `project_type`.
- **Scripts**: scripts that run on the host (`scripts/*.py`, `terraform/deploy.py`) use only the standard library. Scripts that only run inside a container (`start.sh`, `.devcontainer/post-create.sh`) stay bash.

</details>

## Security

Generated projects are secure by default and ship a `SECURITY.md` with a deployment checklist. Reflex projects have **no default accounts**: `task admin:bootstrap` creates the first administrator from `mn-admin-email` and `mn-admin-password`. Updating an older project with `copier update` adds a migration that deactivates the old shared `admin` account if its password was never changed.

## Shell helper

Add this to your `~/.zshrc` to scaffold with `projectkit my-project`. An explicit template reference is passed through; anything else is treated as the destination.

```zsh
projectkit() {
  local default="gh:jenreh/project-kit-template"
  local tmpl

  case "$1" in
    gh:*|git+*|https://*|/*|.*) tmpl="$1"; shift ;;  # explicit template ref
    *)                          tmpl="$default" ;;   # keep $1 as destination
  esac

  copier copy --trust "$tmpl" "$@"
}
```

## Maintaining the template

The template itself lives in [`template/`](template/), and the questions and file selection live in [`copier.yml`](copier.yml).

- **Skills** are not vendored into the template or into generated projects. They come from plugin marketplaces, which the agent CLIs keep up to date. To change the skill set, edit the upstream marketplace. To offer another marketplace, add a choice to `agent_plugins` in `copier.yml` and its entries to `template/.claude/settings.json.jinja`.
- **superpowers** is installed from its Claude Code marketplace [`obra/superpowers-marketplace`](https://github.com/obra/superpowers-marketplace) (`superpowers@superpowers-marketplace`), as its upstream README recommends. The marketplace inside `obra/superpowers` itself is the dev channel.
- **Tool versions** are pinned in the template: GitHub Actions by SHA in `.github/workflows/`, uv and bun by digest in `Dockerfile.jinja`, go-task, fzf, zoxide and starship by checksum and antidote by commit in `.devcontainer/Dockerfile.jinja`.

> [!IMPORTANT]
> Dependabot only updates these pins in generated projects. Refresh them here whenever you update the template.
