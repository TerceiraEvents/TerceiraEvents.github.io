#!/usr/bin/env python3
"""Self-tests for rehost_image.

Network-free: we stub out ``urllib.request.urlopen`` so the tests are
deterministic and don't reach Wikipedia/Facebook/anywhere from CI.

Run with: python scripts/test_rehost_image.py
"""
from __future__ import annotations

import datetime as dt
import io
import sys
import tempfile
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rehost_image  # noqa: E402
from rehost_image import RehostError, _slug_safe, rehost  # noqa: E402


class _FakeResponse(io.BytesIO):
    """Minimal urlopen()-return stand-in supporting context-manager use."""

    def __init__(self, body: bytes, content_type: str) -> None:
        super().__init__(body)
        self.headers = _FakeHeaders(content_type)

    def __enter__(self):  # pragma: no cover - trivial
        return self

    def __exit__(self, *_exc):  # pragma: no cover - trivial
        self.close()
        return False


class _FakeHeaders:
    def __init__(self, content_type: str) -> None:
        self._ct = content_type

    def get_content_type(self) -> str:
        return self._ct


def _run_with_mock(body: bytes, content_type: str, *, side_effect=None):
    target = "rehost_image.urllib.request.urlopen"
    if side_effect is not None:
        patch = mock.patch(target, side_effect=side_effect)
    else:
        patch = mock.patch(target, return_value=_FakeResponse(body, content_type))
    return patch


def test_slug_safe():
    # Accent folding keeps Portuguese names readable: `dragão` -> `dragao`.
    assert _slug_safe("ESCAMA: de dragão 1#") == "escama-de-dragao-1"
    assert _slug_safe("   weird   --  whitespace  ") == "weird-whitespace"
    assert _slug_safe("!!!") == "event"  # fall-back when nothing survives


def test_rehost_writes_expected_path():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        with _run_with_mock(png_bytes, "image/png"):
            dest = rehost(
                "https://example.com/whatever.png",
                "MyEvent Name",
                dt.date(2026, 4, 17),
                dest_dir=tmpdir,
            )
        assert dest == tmpdir / "myevent-name-20260417.png"
        assert dest.read_bytes() == png_bytes


def test_rehost_rejects_html():
    with tempfile.TemporaryDirectory() as tmp:
        with _run_with_mock(b"<html>hi</html>", "text/html"):
            try:
                rehost(
                    "https://www.facebook.com/somepage",
                    "x", dt.date(2026, 4, 17),
                    dest_dir=Path(tmp),
                )
            except RehostError as exc:
                assert "content-type" in str(exc)
                return
        raise AssertionError("expected RehostError on HTML response")


def test_rehost_rejects_oversize():
    with tempfile.TemporaryDirectory() as tmp:
        huge = b"X" * (rehost_image.MAX_IMAGE_BYTES + 1)
        with _run_with_mock(huge, "image/jpeg"):
            try:
                rehost(
                    "https://example.com/huge.jpg",
                    "x", dt.date(2026, 4, 17),
                    dest_dir=Path(tmp),
                )
            except RehostError as exc:
                assert "exceeds" in str(exc)
                return
        raise AssertionError("expected RehostError on oversize response")


def test_rehost_wraps_network_errors():
    with tempfile.TemporaryDirectory() as tmp:
        with _run_with_mock(
            b"", "",
            side_effect=urllib.error.URLError("nope"),
        ):
            try:
                rehost(
                    "https://example.com/x.jpg",
                    "x", dt.date(2026, 4, 17),
                    dest_dir=Path(tmp),
                )
            except RehostError as exc:
                assert "fetch failed" in str(exc)
                return
        raise AssertionError("expected RehostError on URLError")


def test_rehost_rejects_non_http_urls():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            rehost("ftp://example.com/x.jpg", "x", dt.date(2026, 4, 17), dest_dir=Path(tmp))
        except RehostError as exc:
            assert "fetchable URL" in str(exc)
            return
    raise AssertionError("expected RehostError on non-http URL")


def main() -> int:
    tests = [
        test_slug_safe,
        test_rehost_writes_expected_path,
        test_rehost_rejects_html,
        test_rehost_rejects_oversize,
        test_rehost_wraps_network_errors,
        test_rehost_rejects_non_http_urls,
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
