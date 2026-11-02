ARG VARIANT=3.14-trixie
FROM mcr.microsoft.com/devcontainers/python:${VARIANT} AS base

ENV PATH="/root/.local/bin/:$PATH" \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# The base image can ship a stale Yarn apt repo whose GPG key has expired, which
# makes `apt-get update` fail (exit 100) and breaks devcontainer feature installs
# (e.g. common-utils). We don't use this repo, so remove it.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# Install uv (Astral) — Python package/project manager
COPY --from=ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 /uv /uvx /usr/local/bin/

# Install go-task — task runner used via Taskfile.dist.yml. The release archive is
# verified against a pinned checksum instead of piping an installer into a shell.
ARG TASK_VERSION=3.54.0
RUN set -eu; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
        amd64) sha256=680859dbb4d881a9c72d4d9a8f510825450849af8567deacd7302c01124416fb ;; \
        arm64) sha256=d7189d439d4a6058e39e1b2acd7c8b27acd4856691b408f23b242e4294e1df5b ;; \
        *) echo "Unsupported architecture: $arch" >&2; exit 1 ;; \
    esac; \
    curl --fail --silent --show-error --location --output /tmp/task.tar.gz \
        "https://github.com/go-task/task/releases/download/v${TASK_VERSION}/task_linux_${arch}.tar.gz"; \
    echo "$sha256  /tmp/task.tar.gz" | sha256sum --check --strict -; \
    tar -xzf /tmp/task.tar.gz -C /usr/local/bin task; \
    rm /tmp/task.tar.gz
