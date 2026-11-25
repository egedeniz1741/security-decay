import re
import pytest
from sdguard.testing import require

AUTH_WORDS = ("register", "signup", "sign-up", "sign_up", "login", "signin", "sign-in", "sign_in", "token")
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def _is_auth(rule):
    text = (rule.rule + " " + rule.endpoint).lower()
    return any(w in text for w in AUTH_WORDS)


def _fill(path):
    return re.sub(r"<[^>]+>", "1", path)


def _routes(app_module):
    has_accounts = False
    protected = []
    for rule in app_module.app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        if _is_auth(rule):
            has_accounts = True
            continue
        for m in METHODS:
            if m in rule.methods:
                protected.append((m, _fill(rule.rule)))
    return has_accounts, protected


def _call(client, method, path, headers=None):
    kwargs = {"headers": headers or {}}
    if method in ("POST", "PUT", "PATCH"):
        kwargs["json"] = {}
    return client.open(path, method=method, **kwargs)


def test_app_responds(client, app_module):
    rules = [r for r in app_module.app.url_map.iter_rules() if r.endpoint != "static"]
    require(rules, "app has no routes")
    answered = False
    for r in rules:
        if "GET" in r.methods:
            resp = client.get(_fill(r.rule))
            if resp.status_code:
                answered = True
    require(answered, "no GET route to exercise")


def test_no_token_rejected_with_401(client, app_module):
    has_accounts, protected = _routes(app_module)
    require(has_accounts, "app has no registration/login routes")
    require(protected, "no non-auth routes")
    for method, path in protected:
        resp = _call(client, method, path)
        assert resp.status_code == 401, (
            f"{method} {path} answered {resp.status_code} without a token, expected 401"
        )


def test_invalid_token_rejected_with_401(client, app_module):
    has_accounts, protected = _routes(app_module)
    require(has_accounts, "app has no registration/login routes")
    require(protected, "no non-auth routes")
    headers = {"Authorization": "Bearer not.a.validtoken"}
    for method, path in protected:
        resp = _call(client, method, path, headers)
        assert resp.status_code == 401, (
            f"{method} {path} answered {resp.status_code} with an invalid token, expected 401"
        )
