#!/usr/bin/env python3
"""Fail if any event's image: URL points at a host that won't stay reachable.

Background: issue #66 documented five events whose flyer URLs had rotted:
three Facebook CDN (scontent.*.fbcdn.net) thumbs — short-lived oe= tokens
and hotlink-blocked, one https://www.facebook.com/<page> which is HTML
not an image, and one https://fb.me/e/... which is a Facebook event
redirect. Forbidding these hosts at CI time prevents the pattern from
re-accumulating. Issue #67 tracks the positive side (auto re-hosting).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


FORBIDDEN_IMAGE_HOST_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^https?://[^/]*\.fbcdn\.net/", re.IGNORECASE),
        "Facebook CDN thumb (scontent.*.fbcdn.net). These URLs carry a "
        "short-lived `oe=` token and are hotlink-blocked by Facebook; "
        "they go 403 within days. Re-host the image to "
        "/assets/images/events/ or drop it into a GH issue comment and "
        "use that user-attachment URL.",
    ),
    (
        re.compile(r"^https?://fb\.me/", re.IGNORECASE),
        "fb.me redirect. This is a Facebook event/post shortlink, not "
        "an image — it returns HTML, never a flyer. Open the target "
        "event in Facebook, grab the actual flyer image, and re-host.",
    ),
    (
        # Bare facebook.com page URL: `/<handle>` with nothing structural
        # after it. Catches e.g. https://www.facebook.com/MunicipioPraiaVitoria
        # but not e.g. /photo/?fbid=... which at least points at a photo.
        re.compile(
            r"^https?://(www\.)?facebook\.com/[^/?#]+/?(?:[?#].*)?$",
            re.IGNORECASE,
        ),
        "Facebook page URL. This is an HTML page, not an image — it will "
        "never render as a flyer. Pull the actual image off the page and "
        "re-host it.",
    ),
]


def classify(url: str) -> str | None:
    """Return a human-readable rejection reason, or None if the URL is OK."""
    if not url:
        return None
    for pattern, reason in FORBIDDEN_IMAGE_HOST_PATTERNS:
        if pattern.search(url):
            return reason
    return None


def validate_file(path: Path) -> list[str]:
    """Return a list of human-readable errors for any bad image: values."""
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        return [f"{path}: expected a top-level YAML list, got {type(data).__name__}"]

    errors: list[str] = []
    for i, event in enumerate(data):
        image = event.get("image") if isinstance(event, dict) else None
        if not image:
            continue
        reason = classify(image)
        if reason is None:
            continue
        name = (event.get("name") if isinstance(event, dict) else None) or f"(unnamed #{i})"
        errors.append(f"{name}\n    image: {image}\n    why:   {reason}")
    return errors


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    targets = [Path(p) for p in argv[1:]] or [repo_root / "_data" / "special_events.yml"]

    any_error = False
    for target in targets:
        errs = validate_file(target)
        if errs:
            any_error = True
            print(f"{target}: rejected {len(errs)} image URL(s):", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
        else:
            print(f"{target}: OK (no forbidden image hosts)")

    return 1 if any_error else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
