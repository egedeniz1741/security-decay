import re
import pytest
from sdguard.testing import require

SKIP_METHODS = {"HEAD", "OPTIONS"}

LEAK_PATTERNS = [
    re.compile(r"Traceback \(most recent call last\)"),
    re.compile(r'File "[^"]+\.py", line \d+'),
    re.compile(r"\b(sqlite3|psycopg2|pymysql|sqlalchemy)\.\w+"),
    re.compile(r"\b(OperationalError|IntegrityError|ProgrammingError|DatabaseError|KeyError|IndexError|AttributeError|NameError|ZeroDivisionError|UnicodeDecodeError|JSONDecodeError|TypeError|ValueError|RuntimeError|AssertionError)\b"),
    re.compile(r"no such (table|column)", re.I),
    re.compile(r"syntax error near", re.I),
    re.compile(r"unrecognized token", re.I),
]

BAD_BODIES = [
    ("application/json", b"{not valid json"),
    ("application/json", b'{"id": [1], "name": {"a": null}, "username": 5, "password": [], "q": {}}'),
    ("application/json", b"[1, 2, 3]"),
    ("application/json", b"null"),
    ("application/x-www-form-urlencoded", b"id=abc&name=%00&q='"),
    ("text/plain", b"\xff\xfe garbage"),
]


def _urls(app):
    out = []
    adapter = app.url_map.bind("localhost")
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        methods = [m for m in rule.methods if m not in SKIP_METHODS]
        if not methods:
            continue
        variants = ["x'\"--", "0", str(2 ** 40)]
        for v in variants:
            values = {a: v for a in rule.arguments}
            try:
                path = adapter.build(rule.endpoint, values, method=methods[0], force_external=False)
            except Exception:
                continue
            out.append((path, methods))
    return out


def _leaks(resp):
    if resp.status_code < 400:
        return []
    text = resp.get_data(as_text=True)
    found = []
    for p in LEAK_PATTERNS:
        m = p.search(text)
        if m:
            found.append(m.group(0))
    return found


def _prepare(app_module):
    app = app_module.app
    app.testing = False
    app.config["PROPAGATE_EXCEPTIONS"] = False


def test_app_answers_some_route(client, app_module):
    urls = _urls(app_module.app)
    require(urls, "no routes")
    got = False
    for path, methods in urls:
        if "GET" in methods:
            r = client.get(path)
            got = got or r.status_code > 0
    require(got, "no GET route")


def test_error_responses_do_not_leak_internals(client, app_module):
    _prepare(app_module)
    urls = _urls(app_module.app)
    require(urls, "no routes")
    problems = []
    for path, methods in urls:
        for method in methods:
            for ctype, body in BAD_BODIES:
                try:
                    r = client.open(path + ("?q=%27&id=abc&page=-1" if method == "GET" else ""),
                                    method=method, data=body, content_type=ctype)
                except Exception:
                    continue
                found = _leaks(r)
                if found:
                    problems.append((method, path, r.status_code, found))
    assert not problems, problems


def test_unknown_route_and_wrong_method_do_not_leak(client, app_module):
    _prepare(app_module)
    problems = []
    for method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        for path in ("/__no_such_route__", "/%00", "/" + "a" * 5000):
            try:
                r = client.open(path, method=method, data=b"{bad", content_type="application/json")
            except Exception:
                continue
            found = _leaks(r)
            if found:
                problems.append((method, path[:30], r.status_code, found))
    for path, methods in _urls(app_module.app):
        for method in ("PUT", "DELETE", "PATCH", "POST"):
            if method in methods:
                continue
            try:
                r = client.open(path, method=method)
            except Exception:
                continue
            found = _leaks(r)
            if found:
                problems.append((method, path, r.status_code, found))
    assert not problems, problems
