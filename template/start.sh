#!/bin/bash
# Stop on the first failure: the app must not start on a half-migrated database.
set -euo pipefail

cd /reflexapp/

uv run --no-sync alembic upgrade head
uv run --no-sync python -m app.bootstrap_admin
exec uv run --no-sync reflex run --env prod --single-port
