import re
import uuid

from sdguard.testing import require

AUTH_WORDS = ("login", "signin", "token", "register", "signup", "logout", "auth")


def _routes(app_module, method):
    out = []
    for r in app_module.app.url_map.iter_rules():
        if method in r.methods and r.endpoint != "static":
            out.append(r)
    return out


def _is_auth(rule):
    return any(w in rule.rule.lower() for w in AUTH_WORDS)


def _find(app_module, words):
    for r in _routes(app_module, "POST"):
        if not r.arguments and any(w in r.rule.lower() for w in words):
            return r.rule
    return None


def _token(resp):
    j = resp.get_json(silent=True)
    if isinstance(j, dict):
        for k in ("token", "access_token", "jwt"):
            if isinstance(j.get(k), str):
                return j[k]
    return None


def _make_user(app_module, name):
    c = app_module.app.test_client()
    pw = "Pw-" + uuid.uuid4().hex
    uname = name + uuid.uuid4().hex[:6]
    creds = {"username": uname, "password": pw, "email": uname + "@example.com", "name": uname}
    reg = _find(app_module, ("register", "signup"))
    require(reg, "no registration route")
    r = c.post(reg, json=creds)
    require(r.status_code < 300, "registration failed")
    tok = _token(r)
    login = _find(app_module, ("login", "signin", "token"))
    if login:
        r2 = c.post(login, json=creds)
        require(r2.status_code < 300, "login failed")
        tok = _token(r2) or tok
    headers = {"Authorization": "Bearer " + tok} if tok else {}
    return c, headers


def _find_id(j):
    if isinstance(j, dict):
        if "id" in j and isinstance(j["id"], (int, str)):
            return j["id"]
        for v in j.values():
            i = _find_id(v)
            if i is not None:
                return i
    return None


def _fill(rule, value):
    return re.sub(r"<[^>]+>", str(value), rule.rule)


def _setup(app_module):
    a, ha = _make_user(app_module, "alice")
    b, hb = _make_user(app_module, "bob")
    marker = "SECRETMARKER" + uuid.uuid4().hex
    payload = {k: marker for k in ("title", "content", "text", "body", "note", "name",
                                   "description", "data", "message", "value", "secret")}
    rid = None
    created = False
    for r in _routes(app_module, "POST"):
        if r.arguments or _is_auth(r):
            continue
        resp = a.post(r.rule, json=payload, headers=ha)
        if resp.status_code < 300:
            created = True
            rid = _find_id(resp.get_json(silent=True))
            break
    require(created, "cannot create a record")
    gets = [r for r in _routes(app_module, "GET") if not _is_auth(r)]
    ids = [i for i in (rid, 1) if i is not None]
    urls = []
    for r in gets:
        if not r.arguments:
            urls.append(r.rule)
        elif len(r.arguments) == 1:
            for i in ids:
                urls.append(_fill(r, i))
    seen = []
    for u in urls:
        if u not in seen:
            seen.append(u)
    owner_sees = [u for u in seen if marker in a.get(u, headers=ha).get_data(as_text=True)]
    require(owner_sees, "owner cannot read the record back")
    return a, ha, b, hb, marker, seen


def test_app_has_routes(app_module):
    require(len(list(app_module.app.url_map.iter_rules())) > 1, "no routes")


def test_other_user_cannot_read_record(app_module):
    a, ha, b, hb, marker, urls = _setup(app_module)
    for u in urls:
        resp = b.get(u, headers=hb)
        assert marker not in resp.get_data(as_text=True), "record of another user returned by " + u


def test_anonymous_cannot_read_record(app_module):
    a, ha, b, hb, marker, urls = _setup(app_module)
    anon = app_module.app.test_client()
    for u in urls:
        resp = anon.get(u)
        assert marker not in resp.get_data(as_text=True), "record of a user returned to anonymous by " + u
