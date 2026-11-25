# Image in which `sdguard compile` validates LLM-written behavior tests
# (sdguard/compiler/behavior_runner.py, DockerRunner).
#
# - The compiler runs it with --network none, --cap-drop ALL and a read-only root file
#   system; the sdguard package is mounted read-only, so the image does not contain it.
# - Python and the app libraries match the experiment's evaluation image
#   (harness/docker/eval.Containerfile, BaxBench's Flask environment).
#
# Build: docker build -t sdguard-validate:latest -f docker/sdguard-validate.Containerfile docker
FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
RUN pip install --no-cache-dir \
    "pydantic==2.14.2" "pytest==9.2.0" \
    "Flask==3.1.0" "Werkzeug==3.1.3" "pyjwt==2.10.1" "passlib==1.7.4"
ENV PYTHONDONTWRITEBYTECODE=1
USER nobody
