# Branching Rules

This repository only allows a defined list of branch names.

## Allowed Branch Names

- `feature/<slug>`
- `release/<version>`
- `fix/<ticket-ref-and-slug>`
- `hotfix/<slug-or-version>`
- `docs/<slug>`

## Naming Rules

- Use lowercase only.
- Use `/` exactly as shown in the allowed patterns.
- Use kebab-case for descriptive suffixes.
- Use digits and dots for versions where applicable.
- Keep names short and specific.

Examples:

- `feature/add-task-runner-docs`
- `feature/123-update-readme`
- `release/1.2.0`
- `hotfix/fix-taskfile-typo`
- `hotfix/1.2.1`

Branches that do not match the allowed names should be renamed before they are pushed or used for a pull request.
The default branch and `develop` are allowed as well.

## GitHub Rulesets

The rulesets are kept as code in `.github/rulesets/`, and `scripts/github_harden.py`
applies them (with the security settings). `scripts/github_publish.py` runs it when it
creates the repository. GitHub shows them under Settings → Rules → Rulesets; run the
script again after you change a JSON file.

**Protect branch via PR** (default branch):

- Changes only through a pull request with one approving review. A new push dismisses
  earlier approvals.
- All review conversations must be resolved before merging.
- The `00 Security checks` jobs must pass, and once CodeQL runs, no new high or critical
  code scanning alert may be merged.
- No force pushes, no deletion, and no creation of the branch.
- Merge commits only.

**Enforce git-flow branch names**: GitHub refuses to create a branch whose name does not
match the allowed names above.

The repository owner (or, for an organization, its admins) can bypass both rulesets.
