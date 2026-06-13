ARG VARIANT=3.14-bookworm
FROM mcr.microsoft.com/devcontainers/python:${VARIANT} AS base

ENV PATH="/root/.local/bin/:$PATH" \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Install uv (Astral) — Python package/project manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Install go-task — task runner used via Taskfile.dist.yml
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin
