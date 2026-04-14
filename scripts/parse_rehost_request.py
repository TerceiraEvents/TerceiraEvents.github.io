#!/usr/bin/env python3
"""Resolve (url, slug, date) for the rehost-image workflow.

Two input shapes:

- ``workflow_dispatch`` — ``url``, ``slug``, ``date`` arrive as the job's
  ``inputs``. We pass them straight through after normalising.

- ``issues`` (with the ``rehost-image`` label) — parse the issue body
  for ``url:``, ``slug:``, ``date:`` lines. Fenced code blocks are
  allowed; we just scan line-by-line for ``key: value`` rows so YAML
  and markdown both work.

On success, write ``key=value\\n`` lines to ``$GITHUB_OUTPUT`` (i.e.
stdout; the workflow pipes us into it). On any missing field, emit a
GitHub Actions error annotation and exit non-zero so the job fails
visibly instead of silently re-hosting nothing.

Kept as a standalone script (not inside rehost_image.py) so its test
suite stays hermetic — no workflow envvars mocked, no urlopen stubs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys


_KEY_LINE_RE = re.compile(
    r"^\s*(?P<key>url|slug|date)\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_issue_body(body: str) -> dict[str, str]:
    """Return the first url/slug/date triple found in an issue body."""
    result: dict[str, str] = {}
    for match in _KEY_LINE_RE.finditer(body or ""):
        key = match.group("key").lower()
        if key in result:
            # First occurrence wins; issue templates can quote the key
            # later in prose and we don't want that to override.
            continue
        result[key] = match.group("value").strip().strip("`")
    return result


def _validate(url: str | None, slug: str | None, date_str: str | None) -> tuple[str, str, str]:
    missing = [k for k, v in (("url", url), ("slug", slug), ("date", date_str)) if not v]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")
    assert url and slug and date_str  # for type-checkers
    try:
        dt.date.fromisoformat(date_str)
    except ValueError as exc:
        raise ValueError(f"date {date_str!r} is not ISO yyyy-mm-dd") from exc
    return url, slug, date_str


def resolve(
    *,
    event_name: str,
    dispatch_url: str | None,
    dispatch_slug: str | None,
    dispatch_date: str | None,
    issue_body: str | None,
) -> tuple[str, str, str]:
    """Pick the input triple for the current workflow event."""
    if event_name == "workflow_dispatch":
        return _validate(dispatch_url, dispatch_slug, dispatch_date)
    if event_name == "issues":
        parsed = parse_issue_body(issue_body or "")
        return _validate(parsed.get("url"), parsed.get("slug"), parsed.get("date"))
    raise ValueError(f"unsupported event: {event_name!r}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--url", default="")
    parser.add_argument("--slug", default="")
    parser.add_argument("--date", default="")
    parser.add_argument("--issue-body", default="")
    return parser


def main(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv[1:])
    try:
        url, slug, date_str = resolve(
            event_name=args.event_name,
            dispatch_url=args.url or None,
            dispatch_slug=args.slug or None,
            dispatch_date=args.date or None,
            issue_body=args.issue_body or None,
        )
    except ValueError as exc:
        # Annotate the run so it's visible in the Actions UI.
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    print(f"url={url}")
    print(f"slug={slug}")
    print(f"date={date_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
