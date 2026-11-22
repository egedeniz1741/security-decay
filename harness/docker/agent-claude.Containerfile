# Claude Code agent image for experiment sessions (02_DENEY_ALTYAPISI.md §2-3).
#
# - Claude Code is pinned by version and sha256 and never updates itself.
# - HOME is empty: no plugins, skills, memory or settings of a developer. The runner passes the
#   condition's settings with --settings from outside /work (R22, spike 05).
# - No credentials are baked in; the runner hands the login token in at run time.
# - Python and the Flask packages are the same as in eval.Containerfile, so the agent develops
#   against the environment its app is evaluated in.
#
# Build: harness/docker/build.sh
FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

# The platform package of @anthropic-ai/claude-code holds the native binary; its sha256 was
# checked against the registry's sha512 integrity field. Bump both together.
ARG CLAUDE_CODE_VERSION=2.1.323
ARG CLAUDE_CODE_SHA256=d12423fbd90e7239c073e87179f6996aa69130359fa311022a49ae98f0ebcce2

# Tools the agent used in the scenario 1 feasibility run (spikes/senaryo-1-istemler)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git lsof procps sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN [ "$(dpkg --print-architecture)" = amd64 ] || { echo "only linux-x64 is pinned" >&2; exit 1; } \
    && curl -fsSL -o /tmp/claude-code.tgz \
       "https://registry.npmjs.org/@anthropic-ai/claude-code-linux-x64/-/claude-code-linux-x64-${CLAUDE_CODE_VERSION}.tgz" \
    && echo "${CLAUDE_CODE_SHA256}  /tmp/claude-code.tgz" | sha256sum -c - \
    && tar -xzf /tmp/claude-code.tgz -C /tmp package/claude \
    && install -m 0755 /tmp/package/claude /usr/local/bin/claude \
    && rm -rf /tmp/claude-code.tgz /tmp/package

COPY flask-requirements.txt /tmp/flask-requirements.txt
RUN pip install --no-cache-dir --require-hashes -r /tmp/flask-requirements.txt \
    && rm /tmp/flask-requirements.txt

RUN useradd --create-home --uid 1000 --shell /bin/bash agent \
    && mkdir /work && chown agent:agent /work

# No self-update, and no auto memory: within a session it would carry notes from turn to turn
# outside the conversation. Both hold in every condition; init's memory_paths shows the latter.
ENV DISABLE_AUTOUPDATER=1 \
    CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
LABEL org.sdguard.agent="claude-code" \
      org.sdguard.agent-version="${CLAUDE_CODE_VERSION}"

USER agent
WORKDIR /work
# Turns run through `exec`; the container only stays up between them.
CMD ["sleep", "infinity"]
