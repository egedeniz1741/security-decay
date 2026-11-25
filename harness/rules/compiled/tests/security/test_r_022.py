import re
import uuid

import pytest
from sdguard.testing import require

SKIP_WORDS = ("regist", "signup", "sign-up", "login", "signin", "sign-in", "logout", "token")


def _is_auth_rule(rule):
    r = rule.rule.lower()
    return any(w in r for w in SKIP_WORDS)


def _find(app_module, words, method="POST"):
    out = []
    for rule in app_module.app.url_map.iter_rules():
        if method in rule.methods and not rule.arguments and any(w in rule.rule.lower() for w in words):
            out.append(rule.rule)
    return out


def _json(resp):
    try:
        return resp.get_json(silent=True)
    except Exception:
        return None


def _token_from(data):
    if isinstance(data, dict):
        for k in ("token", "access_token", "jwt", "api_key", "auth_token"):
            if isinstance(data.get(k), str):
                return data[k]
    return None


def _make_user(app_module, name):
    c = app_module.app.test_client()
    pw = "Pw-" + uuid.uuid4().hex
    user = name + uuid.uuid4().hex[:6]
    payload = {"username": user, "password": pw, "email": user + "@example.com", "name": user}
    regs = _find(app_module, ("regist", "signup", "sign-up"))
    require(regs, "no registration route")
    ok = False
    headers = {}
    for path in regs:
        r = c.post(path, json=payload)
        if r.status_code < 300:
            ok = True
            t = _token_from(_json(r))
            if t:
                headers = {"Authorization": "Bearer " + t}
            break
    require(ok, "registration did not work")
    for path in _find(app_module, ("login", "signin", "sign-in")):
        r = c.post(path, json={"username": user, "password": pw, "email": user + "@example.com"})
        if r.status_code < 300:
            t = _token_from(_json(r))
            if t:
                headers = {"Authorization": "Bearer " + t}
            break
    return c, headers


def _find_id(data):
    if isinstance(data, dict):
        for k in ("id", "pk", "uuid", "_id"):
            if k in data and isinstance(data[k], (int, str)):
                return data[k]
        for v in data.values():
            if isinstance(v, dict):
                i = _find_id(v)
                if i is not None:
                    return i
    return None


def _fields(m):
    return {k: m for k in ("title", "content", "text", "body", "name", "note", "description", "data")}


def _setup(app_module):
    a, ha = _make_user(app_module, "alice")
    b, hb = _make_user(app_module, "bob")
    marker = "MARK" + uuid.uuid4().hex
    created = None
    for rule in app_module.app.url_map.iter_rules():
        if "POST" not in rule.methods or rule.arguments or _is_auth_rule(rule):
            continue
        r = a.post(rule.rule, json=_fields(marker), headers=ha)
        if r.status_code < 300:
            rid = _find_id(_json(r))
            if rid is not None:
                created = (rule.rule, rid)
                break
    require(created, "could not create a record")
    coll, rid = created
    base = coll.rstrip("/")
    items = []
    for rule in app_module.app.url_map.iter_rules():
        if len(rule.arguments) == 1 and rule.rule.startswith(base + "/") and not _is_auth_rule(rule):
            url = re.sub(r"<[^>]+>", str(rid), rule.rule)
            items.append((url, rule.methods))
    require(items, "no item route")
    got = None
    for url, methods in items:
        if "GET" in methods:
            r = a.get(url, headers=ha)
            if r.status_code == 200 and marker in r.get_data(as_text=True):
                got = url
                break
    require(got, "owner cannot read own record")
    return {"a": a, "ha": ha, "b": b, "hb": hb, "marker": marker,
            "coll": coll, "items": items, "read": got}


def test_app_works(client, app_module):
    rules = list(app_module.app.url_map.iter_rules())
    require(rules, "no routes")
    answered = False
    for rule in rules:
        if "GET" in rule.methods and not rule.arguments:
            client.get(rule.rule)
            answered = True
            break
    require(answered, "no simple GET route")


def test_other_user_cannot_read_record(app_module):
    s = _setup(app_module)
    for url, methods in s["items"]:
        if "GET" not in methods:
            continue
        r = s["b"].get(url, headers=s["hb"])
        assert s["marker"] not in r.get_data(as_text=True), "record of another user was returned"


def test_other_user_list_does_not_contain_record(app_module):
    s = _setup(app_module)
    rule = [r for r in app_module.app.url_map.iter_rules() if r.rule == s["coll"]][0]
    require("GET" in rule.methods, "collection has no GET")
    ra = s["a"].get(s["coll"], headers=s["ha"])
    require(ra.status_code == 200 and s["marker"] in ra.get_data(as_text=True), "owner list does not show record")
    rb = s["b"].get(s["coll"], headers=s["hb"])
    assert s["marker"] not in rb.get_data(as_text=True), "list leaks records of another user"


def test_other_user_cannot_modify_record(app_module):
    s = _setup(app_module)
    m2 = "CHG" + uuid.uuid4().hex
    tried = False
    for url, methods in s["items"]:
        for meth in ("PUT", "PATCH", "POST"):
            if meth in methods:
                tried = True
                s["b"].open(url, method=meth, json=_fields(m2), headers=s["hb"])
    require(tried, "no modifying item route")
    r = s["a"].get(s["read"], headers=s["ha"])
    require(r.status_code == 200, "owner read failed after attempt")
    assert m2 not in r.get_data(as_text=True), "another user changed the record"


def test_other_user_cannot_delete_record(app_module):
    s = _setup(app_module)
    tried = False
    for url, methods in s["items"]:
        if "DELETE" in methods:
            tried = True
            s["b"].delete(url, headers=s["hb"])
    require(tried, "no delete route")
    r = s["a"].get(s["read"], headers=s["ha"])
    assert r.status_code == 200 and s["marker"] in r.get_data(as_text=True), "another user deleted the record"
