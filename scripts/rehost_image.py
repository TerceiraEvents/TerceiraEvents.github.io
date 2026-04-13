#!/usr/bin/env python3
"""Download a flyer image and re-host it inside the repo.

Given a URL, a slug, and a date, this tool fetches the image with
browser-style headers, validates the content-type, writes it to

    assets/images/events/<slug>-<yyyymmdd>.<ext>

and prints the Jekyll path (``/assets/images/events/...``) on stdout.
Returns a non-zero exit code if the fetch fails for any reason — callers
should treat "no image" as acceptable rather than writing a dead URL.

Motivation: issue #66 documented five events whose `image:` URLs had
rotted (Facebook CDN expired `oe=` tokens + hotlink blocks, Facebook
*page* URLs used as images, fb.me event redirects). Issue #67 tracks
this pipeline; ``scripts/validate_image_hosts.py`` is the paired CI
guard that rejects those same hosts at PR time.

Usage::

    python scripts/rehost_image.py <url> <slug> <yyyy-mm-dd>
"""
from __future__ import annotations

import datetime as dt
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEST_DIR = REPO_ROOT / "assets" / "images" / "events"

# Keep us under GitHub's 100 MB file ceiling with plenty of headroom, and
# refuse anything that smells like "someone pasted a random web page URL"
# — a 10 MB HTML document is still garbage as an image.
MAX_IMAGE_BYTES = 10 * 1024 * 1024

CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


class RehostError(Exception):
    """Fetched URL was unreachable, wrong type, or too large."""


def _slug_safe(value: str) -> str:
    """Collapse a slug to [a-z0-9-] so it is safe as a filename.

    Folds accents first (``dragão`` -> ``dragao``) so Portuguese event
    names produce readable filenames instead of ``drag-o``.
    """
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "event"


def _parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def _fetch(url: str, *, timeout: float = 20.0) -> tuple[bytes, str]:
    """Return (body, content_type) for `url`, with browser-style headers.

    Raises RehostError on any failure (HTTP error, timeout, bad type,
    oversize, unreadable content-type). The caller decides whether to
    skip the event or fall back to another source.
    """
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise RehostError(f"not a fetchable URL: {url!r}")

    # Pretend to be a browser and include a Referer equal to the image's
    # own origin. Many CDNs (Instagram/Facebook in particular) hotlink-
    # block empty / foreign referers; origin-matching is what the target
    # site itself would send.
    referer = f"{parsed.scheme}://{parsed.netloc}/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": referer,
    }
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = (response.headers.get_content_type() or "").lower()
            body = response.read(MAX_IMAGE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RehostError(f"fetch failed for {url!r}: {exc}") from exc

    if len(body) > MAX_IMAGE_BYTES:
        raise RehostError(
            f"response exceeds {MAX_IMAGE_BYTES} bytes (got at least "
            f"{len(body)}); refusing to commit: {url!r}"
        )
    if content_type not in CONTENT_TYPE_EXTENSIONS:
        raise RehostError(
            f"response content-type is {content_type!r}, not an image we "
            f"recognize; refusing to commit: {url!r}"
        )
    return body, content_type


def rehost(url: str, slug: str, event_date: dt.date, *, dest_dir: Path = DEST_DIR) -> Path:
    """Download `url` and write it to `<dest_dir>/<slug>-<yyyymmdd>.<ext>`.

    Returns the written path (absolute). Caller is responsible for turning
    that into the Jekyll-relative ``/assets/...`` string they want in YAML.
    """
    body, content_type = _fetch(url)
    ext = CONTENT_TYPE_EXTENSIONS[content_type]
    slug_clean = _slug_safe(slug)
    filename = f"{slug_clean}-{event_date.strftime('%Y%m%d')}.{ext}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    dest.write_bytes(body)
    return dest


def _jekyll_path(dest: Path) -> str:
    """Turn an absolute path under the repo into a leading-slash site path."""
    rel = dest.resolve().relative_to(REPO_ROOT)
    return "/" + rel.as_posix()


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(
            "usage: rehost_image.py <url> <slug> <yyyy-mm-dd>",
            file=sys.stderr,
        )
        return 2
    url, slug, date_str = argv[1], argv[2], argv[3]
    try:
        event_date = _parse_date(date_str)
    except ValueError:
        print(f"invalid date {date_str!r}: expected yyyy-mm-dd", file=sys.stderr)
        return 2
    try:
        dest = rehost(url, slug, event_date)
    except RehostError as exc:
        print(f"rehost failed: {exc}", file=sys.stderr)
        return 1
    print(_jekyll_path(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
