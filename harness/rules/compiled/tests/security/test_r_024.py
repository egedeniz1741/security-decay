import pytest
from sdguard.testing import require

ADMIN_FIELDS = {"is_admin": True, "admin": True, "isAdmin": True, "is_staff": True,
                "is_superuser": True, "role": "admin", "roles": ["admin"], "type": "admin",
                "user_type": "admin", "group": "admin", "level": "admin"}
SKIP = {"HEAD", "OPTIONS"}


def _url(rule):
    import re
    return re.sub(r"<[^>]+>", "1", rule.rule)


def _admin_rules(app_module):
    out = []
    for r in app_module.app.url_map.iter_rules():
        if "admin" in r.rule.lower() and (r.methods - SKIP):
            out.append(r)
    return out


def _find(app_module, words):
    out = []
    for r in app_module.app.url_map.iter_rules():
        if "POST" in r.methods and any(w in r.rule.lower() for w in words) and "<" not in r.rule:
            out.append(r.rule)
    return out


def _statuses(client, rules, headers=None):
    res = []
    for r in rules:
        for m in sorted(r.methods - SKIP):
            kw = {"headers": headers or {}}
            if m in ("POST", "PUT", "PATCH", "DELETE"):
                kw["json"] = {}
            resp = client.open(_url(r), method=m, **kw)
            res.append((m, r.rule, resp.status_code))
    return res


def _register_login(client, app_module, name, extra=None):
    regs = _find(app_module, ["register", "signup", "sign-up"])
    logins = _find(app_module, ["login", "signin", "sign-in", "token"])
    require(regs, "no registration route")
    require(logins, "no login route")
    body = {"username": name, "password": "Pw-12345-xyz", "email": name + "@example.com"}
    if extra:
        body.update(extra)
    resp = client.post(regs[0], json=body)
    require(resp.status_code < 300, "registration did not succeed")
    resp = client.post(logins[0], json={"username": name, "password": "Pw-12345-xyz",
                                        "email": name + "@example.com"})
    require(resp.status_code < 300, "login did not succeed")
    headers = {}
    data = resp.get_json(silent=True)
    if isinstance(data, dict):
        for k in ("token", "access_token", "jwt", "accessToken"):
            if isinstance(data.get(k), str):
                headers["Authorization"] = "Bearer " + data[k]
                break
    return headers


def test_app_responds(client, app_module):
    rules = list(app_module.app.url_map.iter_rules())
    require(rules, "no routes")
    seen = False
    for r in rules:
        if "GET" in r.methods and "<" not in r.rule:
            client.get(r.rule)
            seen = True
    require(seen, "no plain GET route")


def test_anonymous_cannot_use_admin_endpoints(client, app_module):
    rules = _admin_rules(app_module)
    require(rules, "no admin routes")
    bad = [s for s in _statuses(client, rules) if 200 <= s[2] < 300]
    assert not bad, "admin endpoint reachable anonymously: %r" % bad


def test_regular_user_cannot_use_admin_endpoints(client, app_module):
    rules = _admin_rules(app_module)
    require(rules, "no admin routes")
    headers = _register_login(client, app_module, "plainuser")
    bad = [s for s in _statuses(client, rules, headers) if 200 <= s[2] < 300]
    assert not bad, "non-admin user reached admin endpoint: %r" % bad


def test_registration_with_admin_fields_does_not_grant_admin(client, app_module):
    rules = _admin_rules(app_module)
    require(rules, "no admin routes")
    headers = _register_login(client, app_module, "mallory", ADMIN_FIELDS)
    bad = [s for s in _statuses(client, rules, headers) if 200 <= s[2] < 300]
    assert not bad, "self-registered user got admin access: %r" % bad
