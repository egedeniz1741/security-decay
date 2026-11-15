"""pytest plugin for compiled behavior tests (load with ``-p sdguard.testing``).

A behavior rule ("a user only sees their own orders") compiles to a pytest file that
does not know which application it tests. This plugin provides the application:

- ``SDGUARD_APP_DIR``: folder with an ``app.py`` that defines a Flask ``app``. The
  ``client`` fixture loads a fresh copy of it for every test and returns its test client.
- ``SDGUARD_RESULT_FILE``: if set, every test outcome is written there as JSON, so the
  validator can tell an assertion failure (the test detected the weakness) from a crash
  (the test is broken or the application did not start).

Only Flask is supported for now; FastAPI follows the same pattern with its TestClient.
"""

import importlib.util
import json
import os
import sys
from collections.abc import Generator, Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

APP_DIR_ENV = "SDGUARD_APP_DIR"
RESULT_FILE_ENV = "SDGUARD_RESULT_FILE"

_outcomes: dict[str, str] = {}
_collect_errors: list[str] = []


@pytest.fixture
def app_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    """Import ``$SDGUARD_APP_DIR/app.py`` as a fresh module, run from a temporary folder."""
    app_dir = os.environ.get(APP_DIR_ENV)
    if not app_dir:
        raise RuntimeError(f"{APP_DIR_ENV} is not set")
    source = Path(app_dir) / "app.py"
    monkeypatch.chdir(tmp_path)  # files the app creates (SQLite, uploads) stay out of the repo
    monkeypatch.syspath_prepend(str(source.parent))
    name = f"sdguard_app_under_test_{os.getpid()}_{id(tmp_path)}"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(name, None)


@pytest.fixture
def client(app_module: ModuleType) -> Any:
    """Test client of the Flask ``app`` defined in the application under test."""
    app = app_module.app
    app.config["TESTING"] = True
    return app.test_client()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Generator[None]:
    yield
    if call.when == "call" and call.excinfo is not None:
        kind = "assertion" if call.excinfo.errisinstance(AssertionError) else "error"
        _outcomes[item.nodeid] = kind
    elif call.excinfo is not None:  # setup or teardown failed: broken test or app
        _outcomes[item.nodeid] = "error"
    elif call.when == "call":
        _outcomes.setdefault(item.nodeid, "passed")


def pytest_collectreport(report: pytest.CollectReport) -> None:
    if report.failed:
        _collect_errors.append(report.nodeid or "<collection>")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    target = os.environ.get(RESULT_FILE_ENV)
    if not target:
        return
    data = {"outcomes": _outcomes, "collect_errors": _collect_errors, "exit": int(exitstatus)}
    Path(target).write_text(json.dumps(data), encoding="utf-8")
