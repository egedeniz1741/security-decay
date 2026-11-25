import re
import uuid
import pytest
from sdguard.testing import require

EXTRA = {
    "is_admin": True, "isAdmin": True, "admin": True, "is_superuser": True,
    "is_staff": True, "role": "admin", "roles": ["admin"], "user_type": "admin",
    "type": "admin", "group": "admin", "privilege": "admin", "level": "admin",
}


def _routes(app_module, keys, method):
    out = []
    for rule in app_module.app.url_map.iter_rules():
        if method in rule.methods and any(k in rule.rule.lower() for k in keys):
            out.append(re.sub(r"<[^>]+>", "1", rule.rule))
    return out


def _flatten(obj, acc=None):
    acc = [] if acc is None else acc
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.append((str(k).lower(), v))
            _flatten(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _flatten(v, acc)
    return acc


def _shows_admin(resp):
    data = resp.get_json(silent=True)
    for k, v in _flatten(data):
        if ("admin" in k or "superuser" in k) and v is True:
            return True
        if k in ("role", "user_type", "type", "group", "privilege", "level") and \
                isinstance(v, str) and v.lower() in ("admin", "administrator", "superuser"):
            return True
        if k == "roles" and isinstance(v, list) and any(
                isinstance(x, str) and x.lower() in ("admin", "administrator") for x in v):
            return True
    return False


def _register(c, path, extra):
    name = "u" + uuid.uuid4().hex[:10]
    body = {"username": name, "password": "Pw-" + uuid.uuid4().hex,
            "email": name + "@example.com"}
    body.update(extra)
    r = c.post(path, json=body)
    return name, body, r


def _login(c, app_module, name, body):
    headers = {}
    for p in _routes(app_module, ("login", "signin", "sign-in", "token"), "POST"):
        r = c.post(p, json={"username": name, "password": body["password"],
                            "email": body["email"]})
        if 200 <= r.status_code < 300:
            data = r.get_json(silent=True)
            if isinstance(data, dict):
                for k in ("token", "access_token", "jwt", "id_token"):
                    if isinstance(data.get(k), str):
                        headers["Authorization"] = "Bearer " + data[k]
            return True, headers
    return False, headers


def test_app_has_routes(client, app_module):
    require(len(list(app_module.app.url_map.iter_rules())) > 0, "no routes")
    regs = _routes(app_module, ("regist", "signup", "sign-up", "sign_up"), "POST")
    require(regs, "no registration route")
    name, body, r = _register(client, regs[0], {})
    require(r.status_code < 500, "registration errors out")


def test_registration_response_never_shows_admin(client, app_module):
    regs = _routes(app_module, ("regist", "signup", "sign-up", "sign_up"), "POST")
    require(regs, "no registration route")
    for path in regs:
        name, body, r = _register(client, path, EXTRA)
        require(200 <= r.status_code < 300, "registration not accepted")
        assert not _shows_admin(r), "registration created an administrator"


def test_registered_user_cannot_use_admin_endpoints(app_module):
    regs = _routes(app_module, ("regist", "signup", "sign-up", "sign_up"), "POST")
    require(regs, "no registration route")
    admin_paths = _routes(app_module, ("admin",), "GET")
    require(admin_paths, "no admin GET route")
    path = regs[0]
    plain = app_module.app.test_client()
    evil = app_module.app.test_client()
    pn, pb, pr = _register(plain, path, {})
    require(200 <= pr.status_code < 300, "plain registration failed")
    en, eb, er = _register(evil, path, EXTRA)
    require(200 <= er.status_code < 300, "registration with extra fields failed")
    ok1, h1 = _login(plain, app_module, pn, pb)
    ok2, h2 = _login(evil, app_module, en, eb)
    require(ok2, "cannot log in as registered user")
    for ap in admin_paths:
        rp = plain.get(ap, headers=h1) if ok1 else plain.get(ap)
        require(not (200 <= rp.status_code < 300),
                "admin route open to ordinary users; not applicable")
        re_ = evil.get(ap, headers=h2)
        assert not (200 <= re_.status_code < 300), \
            "user registered with admin fields reached an admin endpoint"
