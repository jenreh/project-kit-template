#!/usr/bin/env bash
# (Re)build the Claude Code marketplace plugin layer:
#   * write each plugin's .claude-plugin/plugin.json
#   * symlink plugins/<plugin>/skills/<name> -> ../../../skills/<name>
# Skills are NEVER duplicated — the marketplace points back at the canonical skills/.
set -euo pipefail
cd "$(dirname "$0")/.."

# plugin : space-separated skill names
declare -a PLUGINS=(jenreh-core jenreh-python jenreh-reflex jenreh-terraform)

core="boost code-cleanup commit-msg create-readme frontend-design release skills-creator skills-find"
python="python-coding python-clean-code docker-multi-stage github-actions-cicd runic runic-migrate runic-ogm"
reflex="appkit-commons appkit-mantine-reference reflex-docs reflex-state-and-architecture reflex-testing-state"
terraform="terraform-azure-verified-modules terraform-refactor-module terraform-run-acceptance-tests terraform-search-import terraform-stacks terraform-style-guide terraform-test"

desc_jenreh_core="Cross-cutting agent skills (boost, commit-msg, create-readme, release, …)."
desc_jenreh_python="Python archetype skills (python-coding, runic, docker-multi-stage, …)."
desc_jenreh_reflex="reflex.dev / AppKit web skills (appkit-*, reflex-*)."
desc_jenreh_terraform="Terraform / infra skills (terraform-*)."

skills_for() {
  case "$1" in
    jenreh-core) echo "$core" ;;
    jenreh-python) echo "$python" ;;
    jenreh-reflex) echo "$reflex" ;;
    jenreh-terraform) echo "$terraform" ;;
  esac
}

for plugin in "${PLUGINS[@]}"; do
  pdir="plugins/$plugin"
  mkdir -p "$pdir/.claude-plugin" "$pdir/skills"
  descvar="desc_${plugin//-/_}"
  cat > "$pdir/.claude-plugin/plugin.json" <<EOF
{
  "name": "$plugin",
  "description": "${!descvar}",
  "version": "0.1.0",
  "author": { "name": "Jens Rehpöhler" },
  "license": "MIT"
}
EOF
  # Reset skill symlinks for this plugin.
  find "$pdir/skills" -maxdepth 1 -type l -delete
  for skill in $(skills_for "$plugin"); do
    ln -sfn "../../../skills/$skill" "$pdir/skills/$skill"
  done
  echo "linked $plugin: $(skills_for "$plugin" | wc -w | tr -d ' ') skills"
done
