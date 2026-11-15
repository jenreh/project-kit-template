#!/usr/bin/env python3
"""Applies the project's GitHub baseline to a repository.

Rulesets and security settings are repository settings, not files, so they have
to be set through the API once the repository exists. This script does that, and
running it again is safe. scripts/github_publish.py runs it after the first push.

  Repository   delete head branches after merge, merge commits only,
               read-only GITHUB_TOKEN by default, Actions cannot approve PRs
  Security     dependency graph, Dependabot alerts and security updates,
               GitHub Advanced Security (Code Security + Secret Protection),
               secret scanning with push protection, non-provider patterns,
               AI detection, private vulnerability reporting,
               CodeQL code scanning (default setup)
  Rulesets     every .github/rulesets/*.json. The one on the default branch also
               gets the required status checks (--require-check, by default the
               jobs of .github/workflows/00_security_checks.yml, accepted only
               from GitHub Actions) and, once CodeQL is configured, a code
               scanning merge gate (high or higher). It replaces classic branch
               protection, which is removed only after the ruleset is in place.

Not every feature exists on every plan. Public repositories get the security
features for free; private ones need GitHub Secret Protection / Code Security
(organizations) for secret and code scanning. The script tries each feature,
then reads the settings back and prints what is actually on.

The repository owner (personal repo) or the organization admins bypass the rulesets.

Runs on Linux, macOS and Windows. Needs Python 3.10 or newer and gh,
authenticated with admin rights on the repository. No other dependencies.
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

RULES_DIR = Path(__file__).resolve().parent.parent / ".github" / "rulesets"
DEFAULT_BRANCH_MARKER = "~DEFAULT_BRANCH"
# Job names from .github/workflows/00_security_checks.yml. Rename them together.
DEFAULT_CHECKS = (
    "Scan for committed secrets",
    "Audit locked dependencies",
    "Static security analysis",
)
# Required checks must come from GitHub Actions, so no other app (or a token with
# statuses:write) can satisfy them by posting a status with the same name.
GITHUB_ACTIONS_APP_ID = 15368

# Advanced Security / Code Security come first, because they unlock the rest on
# private repositories.
SECURITY_FEATURES = (
    "advanced_security",
    "code_security",
    "secret_scanning",
    "secret_scanning_push_protection",
    "secret_scanning_non_provider_patterns",
    "secret_scanning_ai_detection",
)


class GhError(Exception):
    """A gh call failed. The message is the last line gh printed to stderr."""


class Gh:
    """Thin wrapper around the gh CLI, which also handles authentication."""

    def __init__(self, executable: str) -> None:
        self._exe = executable

    def run(self, *args: str, body: Any = None) -> str:
        cmd = [self._exe, *args]
        if body is not None:
            cmd += ["--input", "-"]
        proc = subprocess.run(
            cmd,
            input=None if body is None else json.dumps(body),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            lines = [line for line in proc.stderr.splitlines() if line.strip()]
            raise GhError(
                lines[-1] if lines else f"gh exited with code {proc.returncode}"
            )
        return proc.stdout

    def api(self, path: str, method: str = "GET", body: Any = None) -> Any:
        out = self.run("api", "--method", method, path, body=body)
        return json.loads(out) if out.strip() else None


class Reporter:
    """Runs calls that may not exist on the current plan and remembers what failed."""

    def __init__(self) -> None:
        self.unavailable: list[str] = []

    def attempt(self, label: str, call: Any) -> bool:
        try:
            call()
        except GhError as err:
            print(f"  - {label}: not available ({err})")
            self.unavailable.append(label)
            return False
        print(f"  ✓ {label}")
        return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--require-check",
        dest="checks",
        action="append",
        metavar="NAME",
        help=(
            "GitHub Actions job the default branch must pass (repeatable; "
            f"default: {', '.join(DEFAULT_CHECKS)})"
        ),
    )
    parser.add_argument(
        "repo",
        nargs="?",
        help="owner/repo (default: the repository of the current folder)",
    )
    args = parser.parse_args()
    args.checks = args.checks or list(DEFAULT_CHECKS)
    return args


def bypass_actors(repo_info: dict[str, Any]) -> list[dict[str, Any]]:
    if repo_info["owner"]["type"] == "Organization":
        return [
            {"actor_id": 1, "actor_type": "OrganizationAdmin", "bypass_mode": "always"}
        ]
    return [
        {
            "actor_id": repo_info["owner"]["id"],
            "actor_type": "User",
            "bypass_mode": "always",
        }
    ]


def protects_default_branch(template: dict[str, Any]) -> bool:
    include = template.get("conditions", {}).get("ref_name", {}).get("include", [])
    return DEFAULT_BRANCH_MARKER in include


def build_ruleset(
    template: dict[str, Any],
    branch: str,
    bypass: list[dict[str, Any]],
    checks: list[str],
    codeql_configured: bool,
) -> dict[str, Any]:
    ruleset: dict[str, Any] = {**template, "bypass_actors": bypass}
    ref_name = ruleset.get("conditions", {}).get("ref_name", {})
    # ~DEFAULT_BRANCH is only documented for `include`, so `exclude` gets the real name.
    ref_name["exclude"] = [
        f"refs/heads/{branch}" if ref == DEFAULT_BRANCH_MARKER else ref
        for ref in ref_name.get("exclude", [])
    ]
    if not protects_default_branch(ruleset):
        return ruleset

    rules = [
        rule
        for rule in ruleset.get("rules", [])
        if rule.get("type") not in ("required_status_checks", "code_scanning")
    ]
    if checks:
        rules.append(
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": False,
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [
                        {"context": check, "integration_id": GITHUB_ACTIONS_APP_ID}
                        for check in checks
                    ],
                },
            }
        )
    if codeql_configured:
        rules.append(
            {
                "type": "code_scanning",
                "parameters": {
                    "code_scanning_tools": [
                        {
                            "tool": "CodeQL",
                            "security_alerts_threshold": "high_or_higher",
                            "alerts_threshold": "errors",
                        }
                    ]
                },
            }
        )
    ruleset["rules"] = rules
    return ruleset


def list_rulesets(gh: Gh, repo: str) -> list[dict[str, Any]]:
    try:
        return gh.api(f"repos/{repo}/rulesets?includes_parents=false") or []
    except GhError:
        return []  # Rulesets are not available; the create calls report it.


def codeql_state(gh: Gh, repo: str) -> str:
    try:
        return (gh.api(f"repos/{repo}/code-scanning/default-setup") or {}).get(
            "state", "unavailable"
        )
    except GhError:
        return "unavailable"


def apply_repository_settings(gh: Gh, repo: str, report: Reporter) -> None:
    print("--> Repository settings")
    merge_settings = {
        "delete_branch_on_merge": True,
        "allow_merge_commit": True,
        "allow_squash_merge": False,
        "allow_rebase_merge": False,
        "allow_update_branch": True,
    }
    report.attempt(
        "merge settings", lambda: gh.api(f"repos/{repo}", "PATCH", merge_settings)
    )
    workflow_permissions = {
        "default_workflow_permissions": "read",
        "can_approve_pull_request_reviews": False,
    }
    report.attempt(
        "read-only GITHUB_TOKEN",
        lambda: gh.api(
            f"repos/{repo}/actions/permissions/workflow", "PUT", workflow_permissions
        ),
    )


def apply_security(gh: Gh, repo: str, report: Reporter) -> None:
    print("--> Security")
    report.attempt(
        "Dependabot alerts", lambda: gh.api(f"repos/{repo}/vulnerability-alerts", "PUT")
    )
    report.attempt(
        "Dependabot security updates",
        lambda: gh.api(f"repos/{repo}/automated-security-fixes", "PUT"),
    )
    # One feature per call: a feature the plan lacks must not block the others.
    for feature in SECURITY_FEATURES:
        body = {"security_and_analysis": {feature: {"status": "enabled"}}}
        report.attempt(
            feature, lambda body=body: gh.api(f"repos/{repo}", "PATCH", body)
        )
    report.attempt(
        "private vulnerability reporting",
        lambda: gh.api(f"repos/{repo}/private-vulnerability-reporting", "PUT"),
    )
    report.attempt(
        "CodeQL default setup",
        lambda: gh.api(
            f"repos/{repo}/code-scanning/default-setup",
            "PATCH",
            {"state": "configured", "query_suite": "default"},
        ),
    )


def apply_rulesets(
    gh: Gh,
    repo: str,
    repo_info: dict[str, Any],
    *,
    checks: list[str],
    codeql: str,
    report: Reporter,
) -> None:
    print("--> Rulesets")
    branch = repo_info["default_branch"]
    bypass = bypass_actors(repo_info)
    existing = {
        ruleset["name"]: ruleset["id"]
        for ruleset in list_rulesets(gh, repo)
        if ruleset.get("target") == "branch"
    }
    default_branch_ruleset = False
    for file in sorted(RULES_DIR.glob("*.json")):
        template = json.loads(file.read_text(encoding="utf-8"))
        payload = build_ruleset(
            template, branch, bypass, checks, codeql == "configured"
        )
        name = payload["name"]
        ruleset_id = existing.get(name)
        if ruleset_id is not None:
            applied = report.attempt(
                f"update '{name}'",
                lambda p=payload, i=ruleset_id: gh.api(
                    f"repos/{repo}/rulesets/{i}", "PUT", p
                ),
            )
        else:
            applied = report.attempt(
                f"create '{name}'",
                lambda p=payload: gh.api(f"repos/{repo}/rulesets", "POST", p),
            )
        default_branch_ruleset |= applied and protects_default_branch(payload)

    # Rulesets replace classic branch protection; keeping both makes the rules hard to
    # follow. Only drop it once a ruleset protects the branch instead.
    if not default_branch_ruleset:
        print(f"  - kept classic branch protection on '{branch}' (no ruleset applied)")
        return
    try:
        gh.api(f"repos/{repo}/branches/{branch}/protection", "DELETE")
    except GhError:
        pass
    else:
        print(f"  ✓ removed classic branch protection from '{branch}'")


def print_result(
    gh: Gh, repo: str, checks: list[str], codeql: str, report: Reporter
) -> None:
    print("==> Result")
    security = gh.api(f"repos/{repo}").get("security_and_analysis") or {}
    for key, value in security.items():
        status = value.get("status", value) if isinstance(value, dict) else value
        print(f"  {key}: {status}")
    print(f"  codeql_default_setup: {codeql}")
    names = [ruleset["name"] for ruleset in list_rulesets(gh, repo)]
    print(f"  rulesets: {', '.join(names)}")
    if checks:
        print(f"  required checks: {','.join(checks)}")
    if report.unavailable:
        print(
            f"Not applied on this plan or repository: {','.join(report.unavailable)}."
        )
        print(
            "Run this script again after upgrading the plan or making the repository public."
        )


def main() -> int:
    # Windows consoles and redirected output may not use UTF-8; never crash on "✓".
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(errors="replace")

    args = parse_args()
    gh_exe = shutil.which("gh")
    if gh_exe is None:
        print("Error: gh is required (https://cli.github.com).", file=sys.stderr)
        return 1
    if not RULES_DIR.is_dir():
        print(f"Error: {RULES_DIR} not found.", file=sys.stderr)
        return 1

    gh = Gh(gh_exe)
    try:
        repo = (
            args.repo
            or gh.run(
                "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"
            ).strip()
        )
        repo_info = gh.api(f"repos/{repo}")
        if not repo_info.get("permissions", {}).get("admin", False):
            print(f"Error: you need admin rights on {repo}.", file=sys.stderr)
            return 1
        print(
            f"==> Hardening {repo} ({repo_info['visibility']}, "
            f"default branch '{repo_info['default_branch']}')"
        )

        report = Reporter()
        apply_repository_settings(gh, repo, report)
        apply_security(gh, repo, report)
        codeql = codeql_state(gh, repo)
        apply_rulesets(
            gh, repo, repo_info, checks=args.checks, codeql=codeql, report=report
        )
        print_result(gh, repo, args.checks, codeql, report)
    except GhError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
