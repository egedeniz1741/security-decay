"""pytest plugin for compiled behavior tests (load with ``-p sdguard.testing``).

A behavior rule ("a user only sees their own orders") compiles to a pytest file that
does not know which application it tests. This plugin provides the application:

- ``SDGUARD_APP_DIR``: folder with an ``app.py`` that defines a Flask ``app``. The
  ``client`` fixture loads a fresh copy of it, and of every module next to it, for each
  test and returns its test client.
- ``SDGUARD_RESULT_FILE``: if set, every test outcome is written there as JSON, so the
  validator can tell a detection from a crash.

Outcomes:

- ``assertion``: an ``assert`` (or ``pytest.fail`` / ``pytest.raises``) in the test file
  itself failed. This is the only outcome that counts as detecting a weakness.
- ``error``: anything else, including an ``AssertionError`` raised inside the application
  or a library, and a failed ``require`` in a setup step.
- ``passed``.

Compiled tests use ``require(condition, message)`` for setup steps ("the order was
created") and ``assert`` only for the security property itself, so a broken setup is not
mistaken for a detected weakness.

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

from sdguard.compiler.pytest_validation import APP_DIR_ENV, RESULT_FILE_ENV

_outcomes: dict[str, str] = {}
_collect_errors: list[str] = []


class PreconditionError(Exception):
    """A setup step of a compiled test failed; not a security finding."""


def require(condition: object, message: str = "precondition failed") -> None:
    """Check a setup step. Unlike ``assert``, a failure here never counts as detection."""
    if not condition:
        raise PreconditionError(message)


def _modules_under(folder: Path) -> list[str]:
    names = []
    for name, module in list(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if file and Path(file).resolve().is_relative_to(folder):
            names.append(name)
    return names


@pytest.fixture
def app_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    """Import ``$SDGUARD_APP_DIR/app.py`` as a fresh module, run from a temporary folder.

    Modules of a multi-file app (``store.py`` next to ``app.py``) are removed from
    ``sys.modules`` before and after each test, so no state leaks between tests.
    """
    app_dir = os.environ.get(APP_DIR_ENV)
    if not app_dir:
        raise RuntimeError(f"{APP_DIR_ENV} is not set")
    folder = Path(app_dir).resolve()
    source = folder / "app.py"
    monkeypatch.chdir(tmp_path)  # files the app creates (SQLite, uploads) stay out of the repo
    monkeypatch.syspath_prepend(str(folder))
    for name in _modules_under(folder):
        del sys.modules[name]
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
        for leftover in _modules_under(folder):
            del sys.modules[leftover]


@pytest.fixture
def client(app_module: ModuleType) -> Any:
    """Test client of the Flask ``app`` defined in the application under test."""
    app = app_module.app
    app.config["TESTING"] = True
    return app.test_client()


def _raised_in_test_file(item: pytest.Item, excinfo: pytest.ExceptionInfo[BaseException]) -> bool:
    """True when the innermost visible frame of the failure is in the test file itself."""
    entries = excinfo.traceback.filter(excinfo)
    if not entries:
        return False
    return Path(str(entries[-1].path)).resolve() == Path(str(item.path)).resolve()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Generator[None]:
    yield
    excinfo = call.excinfo
    if call.when == "call":
        if excinfo is None:
            _outcomes[item.nodeid] = "passed"
        elif excinfo.errisinstance((AssertionError, pytest.fail.Exception)) and (
            _raised_in_test_file(item, excinfo)
        ):
            _outcomes[item.nodeid] = "assertion"
        else:
            _outcomes[item.nodeid] = "error"
    elif excinfo is not None:
        # Setup failed (no call result yet) or teardown failed after a pass: the test or
        # the app is broken. A teardown error does not replace a call-phase result.
        if _outcomes.get(item.nodeid) in (None, "passed"):
            _outcomes[item.nodeid] = "error"


def pytest_collectreport(report: pytest.CollectReport) -> None:
    if report.failed:
        _collect_errors.append(report.nodeid or "<collection>")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    target = os.environ.get(RESULT_FILE_ENV)
    if not target:
        return
    data = {"outcomes": _outcomes, "collect_errors": _collect_errors, "exit": int(exitstatus)}
    Path(target).write_text(json.dumps(data), encoding="utf-8")
