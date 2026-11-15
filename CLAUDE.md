# ProjectKit Template

This repo is a Copier template, not a project. It generates Python projects and reflex.dev / AppKit web apps. [README.md](README.md) is the user guide; read its "How it works" and "Maintaining the template" sections before larger changes.

## Layout

- `copier.yml`: the questions, `_exclude` (file selection), `_message_after_copy` and `_tasks`.
- `template/`: everything that ends up in a generated project (`_subdirectory: template`).
- `.agents/agent-skills/`: an old vendored copy of the skills (this repo's `.claude/skills` links to it). Generated projects get skills from plugin marketplaces instead; do not add new skills here or to `template/`.
- `template/AGENTS.md.jinja`: the agent instructions of generated projects. `template/CLAUDE.md` is a symlink to `AGENTS.md`, and `_preserve_symlinks: true` keeps it (and `.claude/skills -> ../.agents/skills`) a symlink. Edit the `.jinja` file; never replace a symlink with a copy.

## How a change becomes visible

- Only files ending in `.jinja` are rendered. Everything else is copied as is.
- Copier uses the newest git tag by default, so generated projects see a change only after a new `vX.Y.Z` tag. To render the working tree, pass `--vcs-ref HEAD`.
- `copier update` merges template changes into existing projects. Renaming or moving a template file shows up there as a delete plus a new file, so avoid it unless needed and say so in the commit message.

## Rules that are easy to break

- **Every question is a feature switch.** Leaving a feature off must remove its files, dependencies and task namespace. When you add a question, wire it into `_exclude`, `pyproject.toml.jinja`, `Taskfile.dist.yml.jinja` and the README question table. Exception: every `taskfiles/*.yml` always ships. A feature switches its taskfile on or off through a commented or uncommented `includes:` entry in `Taskfile.dist.yml.jinja`.
- **`_exclude` patterns are root anchored** (start with `/`) and render to `""` when the feature is on. Copier's default excludes are listed again at the top because `_exclude` replaces them.
- **The Python package dir** is a conditional dir name: `{% if project_type == 'python' %}{{ package_name }}{% endif %}`. It disappears for reflex, so it is not in `_exclude`.
- **go-task syntax collides with Jinja.** Plain `Taskfile*.yml` files are not `.jinja`. In the ones that are (`Taskfile.dist.yml.jinja`, `taskfiles/Taskfile.terraform.yaml.jinja`) and in workflow `.jinja` files, wrap `{{.VAR}}` and `${{ }}` in `{% raw %}...{% endraw %}`.
- **JSON templates** (`.claude/settings.json.jinja`, `devcontainer.json.jinja`) build lists in loops. Watch the commas: use `{{ "," if not loop.last }}` and the `{%- if %},` pattern already in those files.
- **Everything must run on Windows.** `_tasks` are argument lists, not shell strings. Host scripts (`scripts/*.py`, `terraform/deploy.py`) use only the standard library. Taskfiles avoid Unix-only tools. Only container scripts (`start.sh`, `.devcontainer/post-create.sh`) may be bash.
- **User answers end up in shell commands and TOML/YAML**, so every free text question needs a `validator`.
- **Pins:** GitHub Actions and pre-commit hooks are pinned by commit SHA with a `# frozen: vX.Y.Z` or `# vX.Y.Z` comment. Docker base images are pinned by digest, tools in `.devcontainer/Dockerfile.jinja` by checksum, MCP servers in `.vscode/mcp.json` by exact version. Keep the betterleaks version the same in `.pre-commit-config.yaml` and `02_security_checks.yml`. Dependabot only updates generated projects, so refresh pins here by hand.
- **Secrets:** generated projects must stay secure by default. No default accounts, no real secrets in `.env.default`, and keep the `deny` list in `template/.claude/settings.json.jinja`.

## Checking a change

A PostToolUse hook (`.claude/hooks/render_check.py`, set up in `.claude/settings.json`) runs after every edit to `template/**` or `copier.yml`. It renders three answer sets from the working tree with tasks skipped, parses every rendered JSON, TOML, YAML and Python file, and checks that feature files are present or excluded as expected. If it reports a problem, fix it before you go on. When you add a question or a conditional file, add it to the variants and the expected file lists in that script.

Run it by hand:

```bash
uv run --script .claude/hooks/render_check.py --all
```

For a full check, generate a project and run its own tasks:

```bash
copier copy --trust --vcs-ref HEAD --defaults --data project_name=demo . "$TMPDIR/demo"
cd "$TMPDIR/demo" && task init && task lint && task test
```

A reflex project needs Postgres and a `.env` before `task test` works.

## Writing and commits

- README and other prose use plain, simple English: short complete sentences, no filler.
- Conventional commits with a scope, for example `feat(template): ...`, `fix(taskfile): ...`, `docs(readme): ...`, `chore(template): bump ...`.
