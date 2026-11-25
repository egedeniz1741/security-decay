# Evaluation image: runs the agent's app and the evaluators side by side, with no network
# (02_DENEY_ALTYAPISI.md §2 step d, R18).
#
# - The app gets exactly BaxBench's Flask environment (system site-packages).
# - The evaluators (functional tests, exploits) run from /opt/harness, a separate venv, so their
#   packages are invisible to the app.
# - Run it with the flags in harness/docker/README.md: no network, no capabilities, read-only
#   root file system.
#
# Build: harness/docker/build.sh
FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

COPY flask-requirements.txt harness-requirements.txt /tmp/
RUN pip install --no-cache-dir --require-hashes -r /tmp/flask-requirements.txt \
    && python -m venv /opt/harness \
    && /opt/harness/bin/pip install --no-cache-dir --require-hashes -r /tmp/harness-requirements.txt \
    && rm /tmp/flask-requirements.txt /tmp/harness-requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1
USER nobody
