#!/usr/bin/env python3
"""Self-tests for parse_rehost_request.resolve / parse_issue_body.

Run with: python scripts/test_parse_rehost_request.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_rehost_request import parse_issue_body, resolve  # noqa: E402


def test_dispatch_happy_path():
    url, slug, date = resolve(
        event_name="workflow_dispatch",
        dispatch_url="https://example.com/flyer.jpg",
        dispatch_slug="my-event",
        dispatch_date="2026-04-18",
        issue_body=None,
    )
    assert (url, slug, date) == ("https://example.com/flyer.jpg", "my-event", "2026-04-18")


def test_dispatch_missing_raises():
    try:
        resolve(
            event_name="workflow_dispatch",
            dispatch_url="https://x/y",
            dispatch_slug="",
            dispatch_date="2026-04-18",
            issue_body=None,
        )
    except ValueError as exc:
        assert "slug" in str(exc)
        return
    raise AssertionError("expected ValueError")


def test_dispatch_bad_date_raises():
    try:
        resolve(
            event_name="workflow_dispatch",
            dispatch_url="https://x/y",
            dispatch_slug="s",
            dispatch_date="April 18",
            issue_body=None,
        )
    except ValueError as exc:
        assert "yyyy-mm-dd" in str(exc)
        return
    raise AssertionError("expected ValueError")


def test_issue_body_plain_keys():
    body = """
    url: https://example.com/flyer.png
    slug: fest-de-sopas
    date: 2026-04-18
    """
    url, slug, date = resolve(
        event_name="issues",
        dispatch_url=None, dispatch_slug=None, dispatch_date=None,
        issue_body=body,
    )
    assert (url, slug, date) == ("https://example.com/flyer.png", "fest-de-sopas", "2026-04-18")


def test_issue_body_inside_code_block():
    body = """
    Hey, please rehost this:

    ```yaml
    url: https://example.com/flyer.png
    slug: fest-de-sopas
    date: 2026-04-18
    ```

    Thanks!
    """
    url, _, _ = resolve(
        event_name="issues",
        dispatch_url=None, dispatch_slug=None, dispatch_date=None,
        issue_body=body,
    )
    assert url == "https://example.com/flyer.png"


def test_issue_body_first_wins():
    """Later references in prose shouldn't override the real inputs."""
    body = """
    url: https://example.com/flyer.png
    slug: fest-de-sopas
    date: 2026-04-18

    (Note: we previously had `url: https://example.com/old.png` in the
    submission, but that was wrong.)
    """
    url, _, _ = resolve(
        event_name="issues",
        dispatch_url=None, dispatch_slug=None, dispatch_date=None,
        issue_body=body,
    )
    assert url == "https://example.com/flyer.png"


def test_issue_body_missing_raises():
    body = """
    url: https://example.com/flyer.png
    date: 2026-04-18
    """
    try:
        resolve(
            event_name="issues",
            dispatch_url=None, dispatch_slug=None, dispatch_date=None,
            issue_body=body,
        )
    except ValueError as exc:
        assert "slug" in str(exc)
        return
    raise AssertionError("expected ValueError")


def test_unsupported_event():
    try:
        resolve(
            event_name="push",
            dispatch_url=None, dispatch_slug=None, dispatch_date=None,
            issue_body=None,
        )
    except ValueError as exc:
        assert "unsupported event" in str(exc)
        return
    raise AssertionError("expected ValueError")


def test_parse_issue_body_strips_backticks():
    parsed = parse_issue_body("url: `https://example.com/x.png`\nslug: s\ndate: 2026-04-18\n")
    assert parsed["url"] == "https://example.com/x.png"


def main() -> int:
    tests = [
        test_dispatch_happy_path,
        test_dispatch_missing_raises,
        test_dispatch_bad_date_raises,
        test_issue_body_plain_keys,
        test_issue_body_inside_code_block,
        test_issue_body_first_wins,
        test_issue_body_missing_raises,
        test_unsupported_event,
        test_parse_issue_body_strips_backticks,
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
