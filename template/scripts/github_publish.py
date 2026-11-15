#!/usr/bin/env python3
"""Publishes this project to a new GitHub repository and applies the GitHub baseline.

  1. gh repo create <owner/repo> --source . --push   (creates the repo and pushes HEAD)
  2. scripts/github_harden.py: rulesets with the security checks required,
     branch protection, security and Advanced Security

Copier runs it when you answer create_github_repo: yes. Run it yourself to publish
later. It needs at least one local commit.

Runs on Linux, macOS and Windows. Needs Python 3.10 or newer, git and gh
(authenticated, with rights to create the repository). No other dependencies.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
HARDEN = Path(__file__).resolve().parent / "github_harden.py"


class PublishError(Exception):
    """Stops the script; the message is printed as the error."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("repo", help="owner/repo of the new repository")
    parser.add_argument(
        "visibility", nargs="?", choices=("private", "public"), default="private"
    )
    return parser.parse_args()


def tool(name: str) -> str:
    # shutil.which also resolves Windows executables and .cmd shims.
    exe = shutil.which(name)
    if exe is None:
        raise PublishError(f"{name} is required.")
    return exe


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [tool("git"), *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


def check_ready() -> str:
    """Returns the current branch once the project can be published."""
    tool("gh")
    if git("rev-parse", "--verify", "-q", "HEAD").returncode != 0:
        raise PublishError("commit the project first.")
    origin = git("remote", "get-url", "origin")
    if origin.returncode == 0:
        raise PublishError(f"remote 'origin' already exists ({origin.stdout.strip()}).")
    return git("branch", "--show-current").stdout.strip()


def main() -> int:
    args = parse_args()
    publish = f"python scripts/github_publish.py {args.repo} {args.visibility}"
    try:
        branch = check_ready()
        print(
            f"==> Creating {args.visibility} repository {args.repo} and pushing {branch}",
            flush=True,
        )
        create = [tool("gh"), "repo", "create", args.repo, f"--{args.visibility}"]
        create += ["--source", ".", "--remote", "origin", "--push"]
        if subprocess.run(create, cwd=PROJECT_DIR, check=False).returncode != 0:
            raise PublishError(
                f"GitHub repository not created (is gh authenticated? does it already "
                f"exist?). Fix the cause, then run: {publish}"
            )
    except PublishError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    harden = [sys.executable, str(HARDEN), args.repo]
    if subprocess.run(harden, cwd=PROJECT_DIR, check=False).returncode != 0:
        print(
            "Error: the repository exists, but the GitHub baseline is not (fully) "
            f"applied. Finish it with: python scripts/github_harden.py {args.repo}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
