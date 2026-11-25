"""Behavior test used as a scripted model answer in test_compile.py."""

from sdguard.testing import require


def _routes(app_module):
    return [r for r in app_module.app.url_map.iter_rules() if r.endpoint != "static"]


def test_app_has_routes(app_module):
    assert _routes(app_module)


def test_errors_do_not_show_tracebacks(client, app_module):
    routes = _routes(app_module)
    require(routes, "the app has no routes")
    for rule in routes:
        for method in sorted((rule.methods or set()) - {"HEAD", "OPTIONS"}):
            response = client.open(
                rule.rule, method=method, data="{not json", content_type="application/json"
            )
            assert b"Traceback (most recent call last)" not in response.data
