#!/usr/bin/env python3
"""Self-tests for ``rehost_image``.

Network-free: ``urllib.request.urlopen`` is patched with a sequenced fake
that returns whatever the next test step expects, so CI never reaches
GitHub or any external host.

Run with: ``python scripts/test_rehost_image.py``
"""
from __future__ import annotations

import datetime as dt
import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rehost_image  # noqa: E402
from rehost_image import RehostError, _slug_safe, rehost  # noqa: E402


# ---------------------------------------------------------------------------
# Test fixtures: fake urlopen responses
# ---------------------------------------------------------------------------

class _FakeResponse(io.BytesIO):
    """Minimal urlopen()-return stand-in supporting context-manager use."""

    def __init__(self, body: bytes, content_type: str = "", status: int = 200) -> None:
        super().__init__(body)
        self.headers = _FakeHeaders(content_type)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
        return False


class _FakeHeaders:
    def __init__(self, content_type: str) -> None:
        self._ct = content_type

    def get_content_type(self) -> str:
        return self._ct


def _http_error(code: int, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://example.invalid/",
        code=code,
        msg=f"HTTP {code}",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(body),
    )


def _release_json(release_id: int = 12345) -> bytes:
    return json.dumps({
        "id": release_id,
        "tag_name": "event-images",
        "upload_url": (
            "https://uploads.github.com/repos/Owner/Repo/releases/"
            f"{release_id}/assets{{?name,label}}"
        ),
    }).encode()


def _asset_json(name: str, repo: str = "Owner/Repo", tag: str = "event-images") -> bytes:
    return json.dumps({
        "id": 99999,
        "name": name,
        "browser_download_url": (
            f"https://github.com/{repo}/releases/download/{tag}/{name}"
        ),
    }).encode()


def _patched_urlopen(responses: list):
    """Patch ``urlopen`` to return / raise the given items in sequence.

    Each item is either a callable accepting (request, **kw) or a ready
    response; raising values can also be passed (instances of Exception).
    """
    iter_responses = iter(responses)

    def fake(req, *_args, **_kw):
        item = next(iter_responses)
        if isinstance(item, Exception):
            raise item
        return item

    return mock.patch("rehost_image.urllib.request.urlopen", side_effect=fake)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
PNG_SHA8 = "a1f76d95"  # validated in main() against actual sha256(PNG_BYTES)[:8]


def test_slug_safe():
    # Accent folding keeps Portuguese names readable: `dragão` -> `dragao`.
    assert _slug_safe("ESCAMA: de dragão 1#") == "escama-de-dragao-1"
    assert _slug_safe("   weird   --  whitespace  ") == "weird-whitespace"
    assert _slug_safe("!!!") == "event"


def test_rehost_happy_path_release_exists():
    """Fetch succeeds, release is found via GET, asset upload returns URL."""
    expected_name = f"myevent-name-20260417-{PNG_SHA8}.png"
    responses = [
        _FakeResponse(PNG_BYTES, "image/png"),                 # _fetch
        _FakeResponse(_release_json(), "application/json"),    # GET release
        _FakeResponse(_asset_json(expected_name), "application/json"),  # upload
    ]
    with _patched_urlopen(responses):
        url = rehost(
            "https://example.com/whatever.png",
            "MyEvent Name",
            dt.date(2026, 4, 17),
            repo="Owner/Repo",
            token="ghp_test",
        )
    assert url == (
        f"https://github.com/Owner/Repo/releases/download/event-images/{expected_name}"
    ), url


def test_rehost_creates_release_when_missing():
    """If the GET returns 404, a POST creates the release and upload proceeds."""
    expected_name = f"myevent-20260417-{PNG_SHA8}.png"
    responses = [
        _FakeResponse(PNG_BYTES, "image/png"),                 # _fetch
        _http_error(404, b'{"message":"Not Found"}'),          # GET release -> 404
        _FakeResponse(_release_json(67890), "application/json"),  # POST create
        _FakeResponse(_asset_json(expected_name), "application/json"),  # upload
    ]
    with _patched_urlopen(responses):
        url = rehost(
            "https://example.com/x.png",
            "MyEvent",
            dt.date(2026, 4, 17),
            repo="Owner/Repo",
            token="ghp_test",
        )
    assert "releases/download/event-images" in url


def test_rehost_returns_existing_url_on_422():
    """Re-uploading the same image (sha-named) returns the deterministic URL."""
    expected_name = f"myevent-20260417-{PNG_SHA8}.png"
    responses = [
        _FakeResponse(PNG_BYTES, "image/png"),                 # _fetch
        _FakeResponse(_release_json(), "application/json"),    # GET release
        _http_error(422, b'{"errors":[{"code":"already_exists"}]}'),  # upload -> 422
    ]
    with _patched_urlopen(responses):
        url = rehost(
            "https://example.com/x.png",
            "MyEvent",
            dt.date(2026, 4, 17),
            repo="Owner/Repo",
            token="ghp_test",
        )
    assert url == (
        f"https://github.com/Owner/Repo/releases/download/event-images/{expected_name}"
    ), url


def test_rehost_rejects_html():
    responses = [_FakeResponse(b"<html>hi</html>", "text/html")]
    with _patched_urlopen(responses):
        try:
            rehost(
                "https://www.facebook.com/somepage",
                "x", dt.date(2026, 4, 17),
                repo="Owner/Repo", token="t",
            )
        except RehostError as exc:
            assert "content-type" in str(exc)
            return
    raise AssertionError("expected RehostError on HTML response")


def test_rehost_rejects_oversize():
    huge = b"X" * (rehost_image.MAX_IMAGE_BYTES + 1)
    responses = [_FakeResponse(huge, "image/jpeg")]
    with _patched_urlopen(responses):
        try:
            rehost(
                "https://example.com/huge.jpg",
                "x", dt.date(2026, 4, 17),
                repo="Owner/Repo", token="t",
            )
        except RehostError as exc:
            assert "exceeds" in str(exc)
            return
    raise AssertionError("expected RehostError on oversize response")


def test_rehost_wraps_network_errors():
    responses = [urllib.error.URLError("nope")]
    with _patched_urlopen(responses):
        try:
            rehost(
                "https://example.com/x.jpg",
                "x", dt.date(2026, 4, 17),
                repo="Owner/Repo", token="t",
            )
        except RehostError as exc:
            assert "fetch failed" in str(exc)
            return
    raise AssertionError("expected RehostError on URLError")


def test_rehost_rejects_non_http_urls():
    # No urlopen call should happen — the URL is rejected up front.
    with _patched_urlopen([]):
        try:
            rehost(
                "ftp://example.com/x.jpg",
                "x", dt.date(2026, 4, 17),
                repo="Owner/Repo", token="t",
            )
        except RehostError as exc:
            assert "fetchable URL" in str(exc)
            return
    raise AssertionError("expected RehostError on non-http URL")


def test_rehost_propagates_unexpected_release_error():
    """A 500 from the release lookup is *not* swallowed (only 404 is)."""
    responses = [
        _FakeResponse(PNG_BYTES, "image/png"),                 # _fetch
        _http_error(500, b'{"message":"internal"}'),           # GET release -> 500
    ]
    with _patched_urlopen(responses):
        try:
            rehost(
                "https://example.com/x.png",
                "x", dt.date(2026, 4, 17),
                repo="Owner/Repo", token="t",
            )
        except RehostError as exc:
            assert "500" in str(exc)
            return
    raise AssertionError("expected RehostError on 500 from GET release")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> int:
    # Compute the actual sha8 once so test assertions stay correct even if
    # PNG_BYTES is changed.
    import hashlib
    actual = hashlib.sha256(PNG_BYTES).hexdigest()[:8]
    if actual != PNG_SHA8:
        print(
            f"PNG_SHA8 constant out of sync with PNG_BYTES "
            f"(expected {actual!r}); update the constant.",
            file=sys.stderr,
        )
        return 2

    tests = [
        test_slug_safe,
        test_rehost_happy_path_release_exists,
        test_rehost_creates_release_when_missing,
        test_rehost_returns_existing_url_on_422,
        test_rehost_rejects_html,
        test_rehost_rejects_oversize,
        test_rehost_wraps_network_errors,
        test_rehost_rejects_non_http_urls,
        test_rehost_propagates_unexpected_release_error,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  ok  {fn.__name__}")
        except AssertionError as exc:
            print(f"FAIL  {fn.__name__}: {exc}", file=sys.stderr)
            failed += 1
    if failed:
        print(f"{failed} failure(s)", file=sys.stderr)
        return 1
    print(f"OK ({len(tests)} tests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
