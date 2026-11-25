import os
import io
import re
import uuid

from sdguard.testing import require

FIELDS = ["file", "upload", "image", "document", "files", "attachment", "avatar"]
SKIP_EXT = (".py", ".pyc")
BIG = 6 * 1024 * 1024


def _routes(app_module):
    out = []
    for rule in app_module.app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        methods = set(rule.methods or []) & {"POST", "PUT"}
        if not methods:
            continue
        path = re.sub(r"<[^>]+>", "1", rule.rule)
        out.append((path, sorted(methods)[0]))
    return out


def _roots(app_module):
    roots = {os.getcwd()}
    rp = getattr(app_module.app, "root_path", None)
    if rp:
        roots.add(rp)
    return [r for r in roots if os.path.isdir(r)]


def _contains(path, marker):
    try:
        with open(path, "rb") as f:
            prev = b""
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    return False
                if marker in prev + chunk:
                    return True
                prev = chunk[-len(marker):]
    except OSError:
        return False


def _stored(app_module, marker, min_size=0):
    for root in _roots(app_module):
        for d, _dirs, files in os.walk(root):
            for n in files:
                if n.endswith(SKIP_EXT):
                    continue
                p = os.path.join(d, n)
                try:
                    if os.path.getsize(p) < max(min_size, len(marker)):
                        continue
                except OSError:
                    continue
                if _contains(p, marker):
                    return p
    return None


def _upload(client, path, method, field, filename, content, mimetype):
    data = {field: (io.BytesIO(content), filename, mimetype)}
    try:
        return client.open(path, method=method, data=data,
                           content_type="multipart/form-data")
    except Exception:
        return None


def test_app_has_routes(client, app_module):
    rules = list(app_module.app.url_map.iter_rules())
    require(rules, "app has no routes")
    answered = False
    for rule in rules:
        if "GET" in rule.methods and "<" not in rule.rule:
            r = client.get(rule.rule)
            answered = answered or r.status_code > 0
    require(answered, "no simple GET route")


def test_disallowed_type_not_stored(client, app_module):
    routes = _routes(app_module)
    require(routes, "no POST/PUT routes")
    for path, method in routes:
        for field in FIELDS:
            marker = ("MARK" + uuid.uuid4().hex).encode()
            content = b"<?php system($_GET['c']); ?>" + marker
            r = _upload(client, path, method, field,
                        "evil_%s.php" % uuid.uuid4().hex[:6],
                        content, "application/x-php")
            if r is None:
                continue
            found = _stored(app_module, marker)
            assert found is None, (
                "executable/script upload (.php) was stored at %s via %s" % (found, path))


def test_oversized_file_not_stored(client, app_module):
    routes = _routes(app_module)
    require(routes, "no POST/PUT routes")
    for path, method in routes:
        for field in FIELDS:
            marker = ("BIG" + uuid.uuid4().hex).encode()
            content = marker + b"A" * BIG
            r = _upload(client, path, method, field,
                        "big_%s.txt" % uuid.uuid4().hex[:6],
                        content, "text/plain")
            if r is None:
                continue
            found = _stored(app_module, marker, min_size=BIG)
            assert found is None, (
                "%d byte upload was stored at %s via %s" % (BIG, found, path))
