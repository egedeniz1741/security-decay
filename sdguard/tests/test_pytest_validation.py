import shutil
from pathlib import Path

import pytest

from sdguard.compiler.pytest_validation import run_against, validate_pytest
from sdguard.contracts.rules import Rule, ValidationStatus

FIXTURE = Path(__file__).parent / "fixtures" / "compiler" / "pytest" / "R-003"
TEST = FIXTURE / "R-003.py"
SECURE = FIXTURE / "secure"
INSECURE = FIXTURE / "insecure"

# Checks only that the owner can read the order: passes on both apps.
WEAK_TEST = """
def test_owner_can_read_own_order(client):
    r = client.post("/orders", json={"item": "book"}, headers={"X-User": "alice"})
    order_id = r.get_json()["id"]
    assert client.get(f"/orders/{order_id}", headers={"X-User": "alice"}).status_code == 200
"""

# Expects the insecure behaviour: fails on the secure app.
WRONG_TEST = """
def test_bob_reads_alices_order(client):
    r = client.post("/orders", json={"item": "book"}, headers={"X-User": "alice"})
    order_id = r.get_json()["id"]
    assert client.get(f"/orders/{order_id}", headers={"X-User": "bob"}).status_code == 200
"""

# Crashes on both apps (no order exists, get_json() is None): not a detection.
CRASHING_TEST = """
def test_reads_owner_field(client):
    owner = client.get("/orders/1", headers={"X-User": "bob"}).get_json()["owner"]
    assert owner == "bob"
"""


def write(tmp_path: Path, text: str, name: str = "R-003.py") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_correct_test_is_verified() -> None:
    validation = validate_pytest(TEST, [SECURE], [INSECURE])
    assert validation.status is ValidationStatus.VERIFIED, validation.message
    assert (validation.good_examples, validation.bad_examples) == (1, 1)


def test_outcomes_tell_assertions_from_passes() -> None:
    run = run_against(TEST, INSECURE)
    assert run.detected
    assert run.tests_with("assertion") == [
        "test_order_list_contains_only_own_orders",
        "test_other_user_cannot_read_the_order",
    ]
    assert run.tests_with("passed") == ["test_owner_can_read_own_order"]


def test_verified_result_goes_into_a_behavior_rule() -> None:
    validation = validate_pytest(TEST, [SECURE], [INSECURE])
    rule = Rule.model_validate(
        {
            "id": "R-003",
            "source": {"file": "AGENTS.md", "line": 18, "text": "A user must only see own orders."},
            "category": "behavior",
            "cwe": ["CWE-639"],
            "targets": {"pytest": {"test_path": "tests/security/R-003.py"}},
            "validation": validation.model_dump(),
            "enforcement": "warn",
            "coverage": "partial",
            "known_gaps": [
                "Only reading orders is tested; updating and deleting another user's order is not.",
                "The test logs in with a header; apps with other login methods need an adapter.",
            ],
        }
    )
    assert rule.is_enforced


def test_test_that_passes_the_insecure_app_fails(tmp_path: Path) -> None:
    validation = validate_pytest(write(tmp_path, WEAK_TEST), [SECURE], [INSECURE])
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "weakness not detected" in validation.message


def test_test_that_fails_the_secure_app_fails(tmp_path: Path) -> None:
    validation = validate_pytest(write(tmp_path, WRONG_TEST), [SECURE], [INSECURE])
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "false alarm in test_bob_reads_alices_order" in validation.message


def test_crash_is_not_counted_as_detection(tmp_path: Path) -> None:
    validation = validate_pytest(write(tmp_path, CRASHING_TEST), [SECURE], [INSECURE])
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "crashed instead: test_reads_owner_field" in validation.message


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("def test_broken(client):\n    return (\n", "could not be collected"),
        ("x = 1\n", "contains no tests"),
    ],
)
def test_unusable_test_file_fails(tmp_path: Path, text: str, message: str) -> None:
    validation = validate_pytest(write(tmp_path, text), [SECURE], [INSECURE])
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert message in validation.message


def test_app_folder_without_app_py_fails(tmp_path: Path) -> None:
    validation = validate_pytest(TEST, [SECURE], [tmp_path])
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "has no app.py" in validation.message


def test_missing_reference_apps_fail() -> None:
    validation = validate_pytest(TEST, [SECURE], [])
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "insecure reference application" in validation.message


def test_missing_test_file_fails(tmp_path: Path) -> None:
    validation = validate_pytest(tmp_path / "nope.py", [SECURE], [INSECURE])
    assert validation.status is ValidationStatus.FAILED


def test_slow_test_times_out(tmp_path: Path) -> None:
    slow = write(tmp_path, "import time\n\ndef test_slow(client):\n    time.sleep(10)\n")
    validation = validate_pytest(slow, [SECURE], [INSECURE], timeout=2)
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "timed out" in validation.message


def make_app(tmp_path: Path, name: str, old: str, new: str) -> Path:
    folder = tmp_path / name
    folder.mkdir()
    source = (SECURE / "app.py").read_text()
    assert old in source
    (folder / "app.py").write_text(source.replace(old, new))
    return folder


def test_broken_app_is_not_a_detection(tmp_path: Path) -> None:
    # Secure app whose POST /orders fails: no IDOR, so the test must not verify against it.
    broken = make_app(
        tmp_path,
        "broken",
        'return jsonify({"id": order_id}), 201',
        'return jsonify({"error": "db down"}), 500',
    )
    validation = validate_pytest(TEST, [SECURE], [broken])
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "weakness not detected" in validation.message


def test_broken_app_is_caught_even_when_setup_uses_assert(tmp_path: Path) -> None:
    broken = make_app(
        tmp_path,
        "broken",
        'return jsonify({"id": order_id}), 201',
        'return jsonify({"error": "db down"}), 500',
    )
    old_style = TEST.read_text().replace(
        'require(response.status_code == 201, "order could not be created")',
        "assert response.status_code == 201",
    )
    validation = validate_pytest(write(tmp_path, old_style), [SECURE], [broken])
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "no test passed" in validation.message


def test_assert_inside_the_app_is_not_a_detection(tmp_path: Path) -> None:
    asserting = make_app(
        tmp_path,
        "asserting",
        "    own = [",
        "    assert ORDERS is None\n    own = [",
    )
    run = run_against(TEST, asserting)
    assert run.outcomes[next(k for k in run.outcomes if k.endswith("only_own_orders"))] == "error"


def test_pytest_fail_in_the_test_file_counts_as_assertion(tmp_path: Path) -> None:
    text = "import pytest\n\ndef test_fails(client):\n    pytest.fail('weakness found')\n"
    run = run_against(write(tmp_path, text), SECURE)
    assert run.tests_with("assertion") == ["test_fails"]


def test_state_does_not_leak_between_tests_of_a_multi_file_app(tmp_path: Path) -> None:
    split = tmp_path / "split"
    split.mkdir()
    (split / "store.py").write_text("ORDERS: dict[int, dict[str, str]] = {}\n")
    source = (SECURE / "app.py").read_text()
    (split / "app.py").write_text(
        source.replace("ORDERS: dict[int, dict[str, str]] = {}\n", "from store import ORDERS\n")
    )
    one_order = (
        "def _one(client):\n"
        "    client.post('/orders', json={'item': 'x'}, headers={'X-User': 'alice'})\n"
        "    assert len(client.get('/orders', headers={'X-User': 'alice'}).get_json()) == 1\n\n"
        "def test_first(client):\n    _one(client)\n\n"
        "def test_second(client):\n    _one(client)\n"
    )
    run = run_against(write(tmp_path, one_order, "iso.py"), split)
    assert run.tests_with("passed") == ["test_first", "test_second"]


def test_parent_environment_does_not_reach_the_test(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SDGUARD_FAKE_TOKEN", "not-a-real-token")
    text = "import os\n\ndef test_env(client):\n    assert 'SDGUARD_FAKE_TOKEN' not in os.environ\n"
    run = run_against(write(tmp_path, text), SECURE)
    assert run.tests_with("passed") == ["test_env"]


def test_reference_apps_are_left_unchanged(tmp_path: Path) -> None:
    copy = tmp_path / "secure"
    shutil.copytree(SECURE, copy)
    before = sorted(p.name for p in copy.iterdir())
    run_against(TEST, copy)
    assert sorted(p.name for p in copy.iterdir()) == before
