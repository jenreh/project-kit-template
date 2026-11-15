# /// script
# requires-python = ">=3.12"
# dependencies = ["copier>=9.10", "pyyaml>=6"]
# ///
"""Render the template after an edit and check that the output still parses.

Claude Code runs this as a PostToolUse hook (see .claude/settings.json). It reads
the hook payload from stdin and does nothing unless the edited file is part of the
template (template/** or copier.yml). Otherwise it renders a few answer sets from
the working tree (dirty changes included) into temp folders, with tasks skipped,
and parses every rendered JSON, TOML, YAML and Python file.

On failure it prints the problems to stderr and exits with code 2, which Claude
Code feeds back to Claude. Run it by hand with --all to check without a payload:

    uv run --script .claude/hooks/render_check.py --all
"""

from __future__ import annotations

import ast
import json
import re
import sys
import tempfile
import tomllib
import warnings
from pathlib import Path
from typing import Any

import yaml
from copier import run_copy

ROOT = Path(__file__).resolve().parents[2]

# Few renders that together switch every question on and off at least once.
VARIANTS: dict[str, dict[str, Any]] = {
    "python-minimal": {
        "project_type": "python",
        "include_db": False,
        "use_devcontainer": False,
        "include_docker": False,
        "include_terraform": False,
        "include_docs": False,
        "include_graph": False,
        "coding_agents": [],
    },
    "python-db-docker": {
        "project_type": "python",
        "include_db": True,
        "use_devcontainer": True,
        "include_docker": True,
        "devcontainer_docker": False,
        "include_terraform": True,
        "cloud_provider": "azure",
        "include_docs": True,
        "coding_agents": ["claude"],
        "agent_plugins": ["jenreh"],
    },
    "reflex-full": {
        "project_type": "reflex",
        "use_devcontainer": True,
        "include_docker": True,
        "devcontainer_docker": True,
        "include_terraform": True,
        "cloud_provider": "aws",
        "include_docs": True,
        "include_graph": True,
        "coding_agents": ["claude", "copilot", "codex"],
        "agent_plugins": ["jenreh", "superpowers", "mattpocock"],
    },
}

# Files every render must (not) contain, relative to the output root.
EXPECT_PRESENT = {
    "python-minimal": [
        "pyproject.toml",
        "render_check/__init__.py",
        "tests/test_smoke.py",
    ],
    "python-db-docker": [
        "alembic.ini",
        ".devcontainer/devcontainer.json",
        ".claude/settings.json",
    ],
    "reflex-full": ["app/app.py", "Dockerfile", "terraform/deploy.py", "alembic.ini"],
}
EXPECT_ABSENT = {
    "python-minimal": [
        "app",
        "alembic",
        ".devcontainer",
        "Dockerfile",
        "docs",
        "terraform",
    ],
    "python-db-docker": ["app", "Dockerfile", "rxconfig.py"],
    "reflex-full": ["render_check", "tests/test_smoke.py"],
}


def edited_path() -> Path | None:
    """The file the tool call touched, or None when there is no usable payload."""
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return None
    file_path = (payload.get("tool_input") or {}).get("file_path")
    return Path(file_path).resolve() if file_path else None


def touches_template(path: Path | None) -> bool:
    if path is None:
        return False
    return path == ROOT / "copier.yml" or path.is_relative_to(ROOT / "template")


def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments and trailing commas, leaving strings alone."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            end = i + 1
            while end < n and text[end] != '"':
                end += 2 if text[end] == "\\" else 1
            out.append(text[i : end + 1])
            i = end + 1
        elif text.startswith("//", i):
            i = text.find("\n", i) if "\n" in text[i:] else n
        elif text.startswith("/*", i):
            i = text.index("*/", i) + 2
        else:
            out.append(ch)
            i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_json(text: str) -> None:
    try:
        json.loads(text)
    except json.JSONDecodeError:
        json.loads(strip_jsonc(text))  # VS Code and dev container files are JSONC


def check_file(path: Path) -> None:
    if path.suffix not in {".json", ".toml", ".yml", ".yaml", ".py"}:
        return
    text = path.read_text(encoding="utf-8")
    match path.suffix:
        case ".json":
            load_json(text)
        case ".toml":
            tomllib.loads(text)
        case ".yml" | ".yaml":
            list(yaml.safe_load_all(text))
        case ".py":
            ast.parse(text, filename=str(path))


def check_variant(name: str, data: dict[str, Any], workdir: Path) -> list[str]:
    dst = workdir / name
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # DirtyLocalWarning is expected here
            run_copy(
                str(ROOT),
                dst,
                data={"project_name": "render-check", **data},
                defaults=True,
                unsafe=True,
                skip_tasks=True,
                vcs_ref="HEAD",
                quiet=True,
            )
    except Exception as exc:  # noqa: BLE001 - every render error is a finding
        return [f"[{name}] render failed: {type(exc).__name__}: {exc}"]

    problems = []
    for path in sorted(dst.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            check_file(path)
        except Exception as exc:  # noqa: BLE001
            rel = path.relative_to(dst)
            problems.append(f"[{name}] {rel}: {type(exc).__name__}: {exc}")
        if path.suffix == ".jinja":
            problems.append(
                f"[{name}] {path.relative_to(dst)}: .jinja suffix left over"
            )
    problems += [
        f"[{name}] expected file missing: {rel}"
        for rel in EXPECT_PRESENT.get(name, [])
        if not (dst / rel).exists()
    ]
    problems += [
        f"[{name}] should have been excluded: {rel}"
        for rel in EXPECT_ABSENT.get(name, [])
        if (dst / rel).exists()
    ]
    return problems


def main() -> int:
    if "--all" not in sys.argv and not touches_template(edited_path()):
        return 0
    with tempfile.TemporaryDirectory(prefix="render-check-") as tmp:
        problems = [
            problem
            for name, data in VARIANTS.items()
            for problem in check_variant(name, data, Path(tmp))
        ]
    if problems:
        print("Template render check failed:", *problems, sep="\n  ", file=sys.stderr)
        return 2
    if "--all" in sys.argv:
        print(f"Render check passed for {', '.join(VARIANTS)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
