#!/usr/bin/env bash
# Refresh the committed skills snapshot in template/.agents/skills from jenreh/agent-skills.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="${AGENT_SKILLS_REPO:-https://github.com/jenreh/agent-skills.git}"
BRANCH="${AGENT_SKILLS_BRANCH:-main}"
DEST="template/.agents/{% if include_skills %}skills{% endif %}"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
git clone --depth 1 --branch "$BRANCH" "$REPO" "$tmp/agent-skills"
rm -rf "$DEST"; mkdir -p "$DEST"
cp -R "$tmp/agent-skills/skills/." "$DEST/"
find "$DEST" -name '.DS_Store' -delete; find "$DEST" -maxdepth 2 -type l -delete
echo "Synced $(find "$DEST" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ') skills. Commit + tag a new version."
