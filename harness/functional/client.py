"""A small HTTP client for the app under test on the evaluation container's loopback.

Stdlib only. Proxies are ignored (a proxy variable would send loopback requests away), and
a request that fails at the connection or protocol level comes back as status 0, so a
broken app fails its checks instead of crashing the evaluation.
"""

import http.client
import json
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

Form = dict[str, str | tuple[str, bytes, str]]  # field -> value or (filename, content, type)


@dataclass(frozen=True)
class Reply:
    status: int
    body: bytes
    content_type: str = ""

    def json(self) -> Any:
        try:
            return json.loads(self.body)
        except ValueError:
            return None


@dataclass(frozen=True)
class Client:
    base_url: str
    timeout: float = 10.0

    def request(
        self,
        method: str,
        path: str,
        body: Any = None,
        *,
        token: str | None = None,
        form: Form | None = None,
    ) -> Reply:
        headers: dict[str, str] = {}
        data = None
        if form is not None:
            boundary = uuid.uuid4().hex
            data = _multipart(form, boundary)
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(  # noqa: S310  # base_url is the loopback app
            self.base_url + path, data=data, method=method, headers=headers
        )
        try:
            with _OPENER.open(req, timeout=self.timeout) as resp:
                return Reply(resp.status, resp.read(), resp.headers.get("Content-Type", ""))
        except urllib.error.HTTPError as err:
            return Reply(err.code, err.read(), err.headers.get("Content-Type", ""))
        except (urllib.error.URLError, http.client.HTTPException, OSError):
            return Reply(0, b"")


def _multipart(form: Form, boundary: str) -> bytes:
    parts = []
    for name, value in form.items():
        if isinstance(value, tuple):
            filename, content, ctype = value
            head = (
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
                f'filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n'
            )
            parts.append(head.encode() + content + b"\r\n")
        else:
            head = f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            parts.append(head.encode() + value.encode() + b"\r\n")
    return b"".join(parts) + f"--{boundary}--\r\n".encode()
