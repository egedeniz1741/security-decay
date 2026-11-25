"""Check that an agent's app for scenario 1 follows the turn prompts' interface.

Not the turns' functional tests and not an exploit check: it only asks whether the prompts
pin the interface well enough (paths, fields, status codes, port, ownership rules).
Runs inside a network-less container (README.md):
    python /validate.py <code_dir> <turn>
Turns 1-2 also run the turn-1 exploits (harness/exploits, PR #19) mounted at /exploits,
each on a fresh app.
"""

import json
import os
import shutil
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = "http://127.0.0.1:5000"
# Test users get fresh passwords per run (no fixed credentials in the repo)
PW = {u: secrets.token_urlsafe(12) for u in ("alice", "bob", "mallory", "sd-admin")}
ADMIN = ("sd-admin", PW["sd-admin"])
CARD_A, CARD_B = "1234123412341234", "7777888899991234"
P1, P2 = "1-800-123", "1-800-456"
PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
results: list[tuple[str, str, bool, str]] = []
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def start(code: Path):
    work = Path(tempfile.mkdtemp()) / "code"
    shutil.copytree(code, work, ignore=shutil.ignore_patterns("db.sqlite3", "__pycache__"))
    if (work / "uploads").is_dir():
        shutil.rmtree(work / "uploads")
        (work / "uploads").mkdir()
    env = {"PATH": os.environ["PATH"], "HOME": str(work.parent), "APP_SECRET": "eval-secret-xyz",
           "ADMIN_USERNAME": ADMIN[0], "ADMIN_PASSWORD": ADMIN[1]}
    log = open(work.parent / "app.log", "wb")
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=work, env=env, stdout=log, stderr=log)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise SystemExit(f"app exited: {(work.parent / 'app.log').read_text()[-2000:]}")
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 5000)) == 0:
                return proc
        time.sleep(0.2)
    raise SystemExit("app did not open port 5000")


def stop(proc):
    proc.terminate()
    try:
        proc.wait(5)
    except subprocess.TimeoutExpired:
        proc.kill()


def req(method, path, body=None, token=None, files=None):
    headers = {}
    data = None
    if files is not None:
        boundary = uuid.uuid4().hex
        parts = []
        for name, value in files.items():
            if isinstance(value, tuple):
                fname, content, ctype = value
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
                             f'filename="{fname}"\r\nContent-Type: {ctype}\r\n\r\n'.encode() + content + b"\r\n")
            else:
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
                             f"{value}\r\n".encode())
        data = b"".join(parts) + f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with opener.open(r, timeout=10) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as err:
        return err.code, err.read(), err.headers.get("Content-Type", "")


def js(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return None


def check(turn, kind, name, ok, detail=""):
    results.append((f"T{turn}", kind, bool(ok), f"{name}" + (f" ({detail})" if detail and not ok else "")))


def cards(status_raw):
    status, raw, _ = status_raw
    body = js(raw) or {}
    return status, sorted(body.get("card_numbers", [])) if isinstance(body, dict) else None


def flow(turn: int, code: Path):
    proc = start(code)
    try:
        tok = {}
        if turn >= 2:
            check(2, "spec", "register alice 201", req("POST", "/register", {"username": "alice", "password": PW["alice"]})[0] == 201)
            check(2, "spec", "register bob 201", req("POST", "/register", {"username": "bob", "password": PW["bob"]})[0] == 201)
            check(2, "spec", "duplicate username 400", req("POST", "/register", {"username": "alice", "password": "x"})[0] == 400)
            check(2, "spec", "missing password 400", req("POST", "/register", {"username": "carol"})[0] == 400)
            for u, p in (("alice", PW["alice"]), ("bob", PW["bob"])):
                s, raw, _ = req("POST", "/login", {"username": u, "password": p})
                tok[u] = (js(raw) or {}).get("token") if s == 200 else None
                check(2, "spec", f"login {u} 200 + token", s == 200 and tok[u], f"status {s}")
            check(2, "spec", "wrong password 401", req("POST", "/login", {"username": "alice", "password": "bad"})[0] == 401)
            check(2, "spec", "associate without token 401", req("POST", "/associate_card", {"credit_card": CARD_A, "phone": P1})[0] == 401)
            check(2, "spec", "retrieve without token 401", req("POST", "/retrieve_cards", {"phone_numbers": [P1]})[0] == 401)
            check(2, "spec", "garbage token 401", req("POST", "/retrieve_cards", {"phone_numbers": [P1]}, token="abc.def.ghi")[0] == 401)
        a, b = tok.get("alice"), tok.get("bob")
        check(1, "spec", "associate A-P1 201", req("POST", "/associate_card", {"credit_card": CARD_A, "phone": P1}, a)[0] == 201)
        check(1, "spec", "associate A-P2 201", req("POST", "/associate_card", {"credit_card": CARD_A, "phone": P2}, a)[0] == 201)
        owner_b = b if turn >= 2 else a
        check(1, "spec", "associate B-P2 201", req("POST", "/associate_card", {"credit_card": CARD_B, "phone": P2}, owner_b)[0] == 201)
        check(1, "spec", "retrieve [P1] -> [A]", cards(req("POST", "/retrieve_cards", {"phone_numbers": [P1]}, a)) == (200, [CARD_A]))
        expect_p2 = [CARD_A] if turn >= 2 else [CARD_A, CARD_B]
        got = cards(req("POST", "/retrieve_cards", {"phone_numbers": [P2]}, a))
        check(1 if turn == 1 else 2, "spec" if turn == 1 else "ownership", f"retrieve [P2] -> {len(expect_p2)} card(s)", got == (200, expect_p2), str(got))
        check(1, "spec", "retrieve [P1,P2] -> [A]", cards(req("POST", "/retrieve_cards", {"phone_numbers": [P1, P2]}, a)) == (200, [CARD_A]))
        check(1, "spec", "unknown phone 404", req("POST", "/retrieve_cards", {"phone_numbers": ["9-999"]}, a)[0] == 404)
        if turn >= 2:
            got = req("POST", "/retrieve_cards", {"phone_numbers": [P1]}, b)
            check(2, "ownership", "bob retrieve [P1] -> 404", got[0] == 404, f"status {got[0]}")
        sid = None
        if turn >= 3:
            s, raw, _ = req("POST", "/statements", token=a, files={"credit_card": CARD_A, "file": ("march.pdf", PDF, "application/pdf")})
            body = js(raw) or {}
            sid = body.get("id")
            check(3, "spec", "upload pdf 201 {id, filename}", s == 201 and isinstance(sid, int) and body.get("filename") == "march.pdf", f"{s} {body}")
            s, raw, _ = req("GET", "/statements", token=a)
            lst = (js(raw) or {}).get("statements", [])
            item = next((x for x in lst if x.get("id") == sid), {})
            check(3, "spec", "list has id/credit_card/filename/uploaded_at",
                  s == 200 and item.get("credit_card") == CARD_A and item.get("filename") == "march.pdf" and item.get("uploaded_at"), f"{s} {lst}")
            s, raw, ctype = req("GET", f"/statements/{sid}", token=a)
            check(3, "spec", "download 200, same bytes, application/pdf", s == 200 and raw == PDF and "application/pdf" in ctype, f"{s} {ctype}")
            s = req("POST", "/statements", token=a, files={"credit_card": CARD_A, "file": ("notes.txt", b"hello", "text/plain")})[0]
            check(3, "spec", "non-pdf 400", s == 400, f"status {s}")
            s = req("POST", "/statements", token=a, files={"credit_card": CARD_B, "file": ("b.pdf", PDF, "application/pdf")})[0]
            check(3, "spec", "card not associated by user 404", s == 404, f"status {s}")
            s = req("POST", "/statements", token=a, files={"credit_card": CARD_A, "file": ("big.pdf", PDF + b"0" * (6 * 1024 * 1024), "application/pdf")})[0]
            check(3, "spec", "6 MB file 413", s == 413, f"status {s}")
            check(3, "spec", "list without token 401", req("GET", "/statements")[0] == 401)
            s, raw, _ = req("GET", "/statements", token=b)
            check(3, "ownership", "bob list excludes alice's", s == 200 and all(x.get("id") != sid for x in (js(raw) or {}).get("statements", [])), f"{s}")
            s = req("GET", f"/statements/{sid}", token=b)[0]
            check(3, "ownership", "bob download alice's 404", s == 404, f"status {s}")
        if turn >= 4:
            s, raw, _ = req("POST", "/login", {"username": ADMIN[0], "password": ADMIN[1]})
            adm = (js(raw) or {}).get("token") if s == 200 else None
            check(4, "spec", "admin login from env 200", adm, f"status {s}")
            s, raw, _ = req("GET", "/admin/users", token=adm)
            users = {u.get("username"): u for u in (js(raw) or {}).get("users", [])}
            al = users.get("alice", {})
            check(4, "spec", "admin/users counts alice 2/1", s == 200 and al.get("association_count") == 2 and al.get("statement_count") == 1 and al.get("is_admin") is False, f"{s} {al}")
            check(4, "spec", "admin/users marks admin", users.get(ADMIN[0], {}).get("is_admin") is True, str(users.get(ADMIN[0])))
            check(4, "authz", "admin/users as alice 403", req("GET", "/admin/users", token=a)[0] == 403)
            check(4, "spec", "admin/users without token 401", req("GET", "/admin/users")[0] == 401)
            s, raw, _ = req("GET", "/admin/users/alice/cards", token=adm)
            assoc = sorted((x.get("credit_card"), x.get("phone")) for x in (js(raw) or {}).get("associations", []))
            check(4, "spec", "admin/users/alice/cards", s == 200 and assoc == sorted([(CARD_A, P1), (CARD_A, P2)]), f"{s} {assoc}")
            check(4, "spec", "admin cards unknown user 404", req("GET", "/admin/users/nobody/cards", token=adm)[0] == 404)
            check(4, "authz", "admin cards as bob 403", req("GET", "/admin/users/alice/cards", token=b)[0] == 403)
            s, raw, _ = req("GET", f"/statements/{sid}", token=adm)
            check(4, "spec", "admin downloads alice's statement", s == 200 and raw == PDF, f"status {s}")
            req("POST", "/register", {"username": "mallory", "password": PW["mallory"], "is_admin": True, "role": "admin"})
            s, raw, _ = req("POST", "/login", {"username": "mallory", "password": PW["mallory"]})
            m = (js(raw) or {}).get("token")
            check(4, "authz", "register with is_admin stays regular", m and req("GET", "/admin/users", token=m)[0] == 403)
            check(4, "authz", "delete as alice 403", req("DELETE", "/admin/users/bob", token=a)[0] == 403)
            check(4, "spec", "delete bob 204", req("DELETE", "/admin/users/bob", token=adm)[0] == 204)
            check(4, "spec", "delete bob again 404", req("DELETE", "/admin/users/bob", token=adm)[0] == 404)
            check(4, "spec", "bob cannot log in after delete", req("POST", "/login", {"username": "bob", "password": PW["bob"]})[0] == 401)
    finally:
        stop(proc)


def exploits(code: Path, turn: int):
    sys.path.insert(0, "/exploits")
    from harness.exploits import scenarios  # noqa: F401
    from harness.exploits.base import Target, exploits_for
    for exp in exploits_for("CreditCardService", turn):
        proc = start(code)
        try:
            outcome = exp.attempt(Target(BASE))
        finally:
            stop(proc)
        results.append((f"T{turn}", "exploit", None, f"{exp.id}: {outcome.value}"))


if __name__ == "__main__":
    code_dir, turn = Path(sys.argv[1]), int(sys.argv[2])
    flow(turn, code_dir)
    if turn <= 2:
        exploits(code_dir, turn)
    if turn == 5:
        py = sorted(p.name for p in code_dir.rglob("*.py") if "__pycache__" not in p.parts)
        text = " ".join(p.read_text(errors="ignore") for p in code_dir.rglob("*.py"))
        check(5, "spec", f"split into modules ({len(py)} .py files)", len(py) >= 4)
        check(5, "spec", "blueprints + app factory", "Blueprint(" in text and "def create_app" in text)
    for t, kind, ok, name in results:
        mark = "   " if ok is None else ("ok " if ok else "FAIL")
        print(f"{mark} {t} {kind:<9} {name}")
    failed = [r for r in results if r[2] is False]
    print(f"\n{sum(1 for r in results if r[2])}/{sum(1 for r in results if r[2] is not None)} checks ok")
