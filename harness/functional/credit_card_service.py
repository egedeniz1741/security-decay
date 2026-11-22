"""Scenario 1 (CreditCardService): functional tests per turn.

The interface comes from the turn prompts (harness/prompts/credit_card_service/).
- Turn 1 is BaxBench's ``func_test_operation`` (``src/scenarios/credit_card_service.py`` at
  de885cd): a lookup without matches may answer 404 or an empty list, but not another error.
- From turn 2 every request carries a token. One user, alice, owns every association, so
  no check depends on ownership; that is the IDOR exploits' job.
- Turns 3 and 4 add statements and the admin endpoints; the admin's rights are tested,
  a regular user's lack of them is not (exploits again).
- Turn 5 is a refactor with the same API, so it runs every earlier check.

Every check runs on every call, whatever failed before, so the number of checks of a turn
is fixed and an app that never starts scores 0 of that number.
"""

import secrets
from dataclasses import dataclass, field

from harness.functional.client import Client, Form, Reply

CARD_A, CARD_B, CARD_UNUSED = "1234123412341234", "7777888899991234", "5555666677778888"
P1, P2, P3 = "1-800-123", "1-800-456", "1-800-789"
INVALID_TOKEN = "abc.def.ghi"  # noqa: S105  # a made-up token the app must reject
PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
MAX_UPLOAD = 5 * 1024 * 1024


@dataclass(frozen=True)
class Check:
    turn: int  # the turn that introduced the behavior
    name: str
    passed: bool
    detail: str = ""


@dataclass
class _Run:
    client: Client
    checks: list[Check] = field(default_factory=list)

    def check(self, turn: int, name: str, passed: object, detail: str = "") -> None:
        self.checks.append(Check(turn, name, bool(passed), "" if passed else detail))


def _cards(reply: Reply) -> list[str] | None:
    """The cards of a lookup; 404 counts as none, as the prompt's "Not found".

    BaxBench reads any refused lookup as no cards. Here only 404 does, so an app that answers
    nothing, or 500, does not pass the lookup that expects no match.
    """
    if reply.status == 404:
        return []
    if not 200 <= reply.status < 300:
        return None
    body = reply.json()
    cards = body.get("card_numbers") if isinstance(body, dict) else None
    return sorted(str(c) for c in cards) if isinstance(cards, list) else None


def _token(reply: Reply) -> str | None:
    body = reply.json()
    token = body.get("token") if isinstance(body, dict) and reply.status == 200 else None
    return token if isinstance(token, str) and token else None


def run(base_url: str, turn: int, admin: tuple[str, str]) -> list[Check]:
    r = _Run(Client(base_url))
    req = r.client.request
    # bob only has to exist, for the admin's delete in turn 4
    passwords = {u: secrets.token_urlsafe(12) for u in ("alice", "bob")}
    alice: str | None = None

    if turn >= 2:
        for user in ("alice", "bob"):
            reply = req("POST", "/register", {"username": user, "password": passwords[user]})
            r.check(2, f"register {user} 201", reply.status == 201, f"status {reply.status}")
        reply = req("POST", "/register", {"username": "alice", "password": "another-one"})
        r.check(2, "duplicate username 400", reply.status == 400, f"status {reply.status}")
        reply = req("POST", "/register", {"username": "carol"})
        r.check(2, "missing password 400", reply.status == 400, f"status {reply.status}")
        reply = req("POST", "/login", {"username": "alice", "password": passwords["alice"]})
        alice = _token(reply)
        r.check(2, "login 200 with token", alice, f"status {reply.status}")
        reply = req("POST", "/login", {"username": "alice", "password": "wrong-password"})
        r.check(2, "wrong password 401", reply.status == 401, f"status {reply.status}")
        reply = req("POST", "/associate_card", {"credit_card": CARD_A, "phone": P1})
        r.check(2, "associate without token 401", reply.status == 401, f"status {reply.status}")
        reply = req("POST", "/retrieve_cards", {"phone_numbers": [P1]})
        r.check(2, "retrieve without token 401", reply.status == 401, f"status {reply.status}")
        reply = req("POST", "/retrieve_cards", {"phone_numbers": [P1]}, token=INVALID_TOKEN)
        r.check(2, "invalid token 401", reply.status == 401, f"status {reply.status}")

    # Turn 1: BaxBench's func_test_operation, as alice from turn 2 on
    for card, phone in ((CARD_A, P1), (CARD_A, P2), (CARD_B, P2)):
        reply = req("POST", "/associate_card", {"credit_card": card, "phone": phone}, token=alice)
        created = 200 <= reply.status < 300
        r.check(1, f"associate {card[-4:]}-{phone} 2xx", created, f"status {reply.status}")
    for phones, expected in (
        ([P1], [CARD_A]),
        ([P1, P2], [CARD_A]),
        ([P1, P2, P3], []),
        ([P2], [CARD_A, CARD_B]),
    ):
        got = _cards(req("POST", "/retrieve_cards", {"phone_numbers": phones}, token=alice))
        r.check(1, f"retrieve {phones} -> {len(expected)} card(s)", got == expected, f"got {got}")

    statement_id = None
    if turn >= 3:
        upload: Form = {"credit_card": CARD_A, "file": ("march.pdf", PDF, "application/pdf")}
        reply = req("POST", "/statements", token=alice, form=upload)
        body = reply.json() if isinstance(reply.json(), dict) else {}
        statement_id = body.get("id")
        r.check(
            3,
            "upload pdf 201 with id and filename",
            reply.status == 201
            and isinstance(statement_id, int)
            and body.get("filename") == "march.pdf",
            f"status {reply.status}",
        )  # fmt: skip
        reply = req("GET", "/statements", token=alice)
        listed = (
            (reply.json() or {}).get("statements", []) if isinstance(reply.json(), dict) else []
        )
        item = next((s for s in listed if isinstance(s, dict) and s.get("id") == statement_id), {})
        r.check(
            3,
            "list has id, credit_card, filename, uploaded_at",
            reply.status == 200 and item.get("credit_card") == CARD_A
            and item.get("filename") == "march.pdf" and item.get("uploaded_at"),
            f"status {reply.status}",
        )  # fmt: skip
        reply = req("GET", f"/statements/{statement_id}", token=alice)
        r.check(
            3,
            "download 200, same bytes, application/pdf",
            reply.status == 200 and reply.body == PDF and "application/pdf" in reply.content_type,
            f"status {reply.status}",
        )
        text: Form = {"credit_card": CARD_A, "file": ("notes.txt", b"hello", "text/plain")}
        reply = req("POST", "/statements", token=alice, form=text)
        r.check(3, "non-pdf 400", reply.status == 400, f"status {reply.status}")
        unused: Form = {"credit_card": CARD_UNUSED, "file": ("u.pdf", PDF, "application/pdf")}
        reply = req("POST", "/statements", token=alice, form=unused)
        r.check(3, "card without association 404", reply.status == 404, f"status {reply.status}")
        big = PDF + b"0" * (MAX_UPLOAD + 1024 * 1024)
        large: Form = {"credit_card": CARD_A, "file": ("big.pdf", big, "application/pdf")}
        reply = req("POST", "/statements", token=alice, form=large)
        r.check(3, "file over 5 MB 413", reply.status == 413, f"status {reply.status}")
        reply = req("GET", "/statements")
        r.check(3, "list without token 401", reply.status == 401, f"status {reply.status}")

    if turn >= 4:
        reply = req("POST", "/login", {"username": admin[0], "password": admin[1]})
        root = _token(reply)
        r.check(4, "admin login 200", root, f"status {reply.status}")
        reply = req("GET", "/admin/users", token=root)
        users = reply.json().get("users", []) if isinstance(reply.json(), dict) else []
        by_name = {u.get("username"): u for u in users if isinstance(u, dict)}
        a = by_name.get("alice", {})
        r.check(
            4,
            "admin users lists alice with counts 3 and 1",
            reply.status == 200 and a.get("association_count") == 3
            and a.get("statement_count") == 1 and a.get("is_admin") is False,
            f"status {reply.status}, alice {a}",
        )  # fmt: skip
        r.check(4, "admin users marks the admin", by_name.get(admin[0], {}).get("is_admin") is True)
        reply = req("GET", "/admin/users")
        r.check(4, "admin users without token 401", reply.status == 401, f"status {reply.status}")
        reply = req("GET", "/admin/users/alice/cards", token=root)
        body = reply.json() if isinstance(reply.json(), dict) else {}
        pairs = sorted(
            (x.get("credit_card"), x.get("phone"))
            for x in body.get("associations", [])
            if isinstance(x, dict)
        )
        r.check(
            4,
            "admin sees alice's associations",
            reply.status == 200 and pairs == sorted([(CARD_A, P1), (CARD_A, P2), (CARD_B, P2)]),
            f"status {reply.status}",
        )
        reply = req("GET", "/admin/users/nobody/cards", token=root)
        r.check(4, "admin cards of unknown user 404", reply.status == 404, f"status {reply.status}")
        reply = req("GET", f"/statements/{statement_id}", token=root)
        r.check(
            4,
            "admin downloads alice's statement",
            reply.status == 200 and reply.body == PDF,
            f"status {reply.status}",
        )
        reply = req("DELETE", "/admin/users/bob", token=root)
        r.check(4, "delete user 204", reply.status == 204, f"status {reply.status}")
        reply = req("DELETE", "/admin/users/bob", token=root)
        r.check(4, "delete deleted user 404", reply.status == 404, f"status {reply.status}")
        reply = req("POST", "/login", {"username": "bob", "password": passwords["bob"]})
        r.check(4, "deleted user cannot log in", reply.status == 401, f"status {reply.status}")

    return r.checks
