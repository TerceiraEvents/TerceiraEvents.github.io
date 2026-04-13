#!/usr/bin/env python3
"""Re-host a flyer image as a GitHub release asset.

Given a URL, a slug, and a date, this tool:

1. Fetches the image with browser-style headers + an origin Referer.
2. Verifies the response is actually an image type we recognize.
3. Uploads the bytes as an asset on a long-lived GitHub release
   (default tag: ``event-images``), creating the release if missing.
4. Prints the asset's permanent ``releases/download/...`` URL on stdout.

The image bytes never enter the git repo — they live in GitHub's release
storage, so cloning the repo stays cheap. The asset name is
``<slug>-<yyyymmdd>-<sha8>.<ext>``; the sha8 makes re-uploading the same
image produce the same name (so re-runs are idempotent).

Background: issue #66 documented five events whose flyer URLs had rotted
(Facebook CDN with short-lived ``oe=`` tokens + hotlink blocks; Facebook
*page* URLs used as images; ``fb.me`` event redirects). Issue #67 tracks
this pipeline; ``scripts/validate_image_hosts.py`` is the paired CI
guard that rejects those same hosts at PR time.

CLI usage::

    GITHUB_TOKEN=ghp_xxx \\
        python scripts/rehost_image.py <url> <slug> <yyyy-mm-dd> \\
        [--repo owner/name] [--tag event-images]

In a GitHub Actions context, ``GITHUB_TOKEN`` and ``GITHUB_REPOSITORY``
are already in the env, so neither flag is needed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_RELEASE_TAG = "event-images"
DEFAULT_RELEASE_NAME = "Event flyer images (auto-managed)"
DEFAULT_RELEASE_BODY = (
    "Auto-managed by `scripts/rehost_image.py`. Each asset is a flyer "
    "image referenced from `_data/special_events.yml`. Do not delete "
    "individual assets — events linking to them will lose their flyer."
)

# Keep us under GitHub's 2 GB per-asset ceiling with plenty of headroom,
# and refuse anything that smells like "someone pasted a random web page
# URL" — a 10 MB HTML document is still garbage as an image.
MAX_IMAGE_BYTES = 10 * 1024 * 1024

CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


class RehostError(Exception):
    """The fetch or the upload failed in a way the caller should handle."""


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def _slug_safe(value: str) -> str:
    """Collapse a slug to ``[a-z0-9-]`` so it is safe as a filename.

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


# ---------------------------------------------------------------------------
# Fetching the source image
# ---------------------------------------------------------------------------

def _fetch(url: str, *, timeout: float = 20.0) -> tuple[bytes, str]:
    """Return ``(body, content_type)`` for ``url``, with browser headers."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise RehostError(f"not a fetchable URL: {url!r}")

    # Pretend to be a browser and include a Referer equal to the image's
    # own origin. Many CDNs (Instagram/Facebook) hotlink-block empty or
    # foreign referers; origin-matching is what the target site sends.
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
            f"{len(body)}); refusing to upload: {url!r}"
        )
    if content_type not in CONTENT_TYPE_EXTENSIONS:
        raise RehostError(
            f"response content-type is {content_type!r}, not an image we "
            f"recognize; refusing to upload: {url!r}"
        )
    return body, content_type


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def _gh_request(
    url: str,
    *,
    token: str,
    method: str = "GET",
    body: bytes | None = None,
    content_type: str | None = None,
    timeout: float = 30.0,
) -> tuple[int, bytes]:
    """Make a single authenticated GitHub API call. Raises ``HTTPError`` on >= 400."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "TerceiraEventsBot/1.0 rehost_image.py",
    }
    if content_type is not None:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read()


def _ensure_release(repo: str, tag: str, token: str) -> str:
    """Return the release's ``upload_url`` template, creating the release if missing.

    The template looks like
    ``https://uploads.github.com/repos/OWNER/REPO/releases/123/assets{?name,label}``.
    """
    api = (
        f"https://api.github.com/repos/{repo}/releases/tags/"
        f"{urllib.parse.quote(tag, safe='')}"
    )
    try:
        _, body = _gh_request(api, token=token)
        return json.loads(body)["upload_url"]
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise RehostError(
                f"GET {api} failed with HTTP {exc.code}: {exc.read()!r}"
            ) from exc

    # 404 — create it.
    create_url = f"https://api.github.com/repos/{repo}/releases"
    payload = json.dumps({
        "tag_name": tag,
        "name": DEFAULT_RELEASE_NAME,
        "body": DEFAULT_RELEASE_BODY,
    }).encode("utf-8")
    try:
        _, body = _gh_request(
            create_url,
            token=token,
            method="POST",
            body=payload,
            content_type="application/json",
        )
    except urllib.error.HTTPError as exc:
        raise RehostError(
            f"POST {create_url} failed with HTTP {exc.code}: {exc.read()!r}"
        ) from exc
    return json.loads(body)["upload_url"]


def _asset_browser_url(repo: str, tag: str, name: str) -> str:
    """Construct the deterministic public URL for an uploaded asset."""
    return (
        f"https://github.com/{repo}/releases/download/"
        f"{urllib.parse.quote(tag, safe='')}/"
        f"{urllib.parse.quote(name, safe='.-_')}"
    )


def _upload_asset(
    upload_url_template: str,
    *,
    name: str,
    body: bytes,
    content_type: str,
    token: str,
    repo: str,
    tag: str,
) -> str:
    """POST `body` as an asset named `name`. Returns the public download URL.

    On HTTP 422 (asset name already exists), assumes the existing asset has the
    same content (we use a content sha in the name) and returns the
    deterministic URL anyway. Re-running on the same image is then a no-op.
    """
    base = upload_url_template.split("{")[0]
    url = f"{base}?name={urllib.parse.quote(name, safe='.-_')}"
    try:
        _, resp = _gh_request(
            url,
            token=token,
            method="POST",
            body=body,
            content_type=content_type,
        )
        return json.loads(resp)["browser_download_url"]
    except urllib.error.HTTPError as exc:
        if exc.code == 422:
            return _asset_browser_url(repo, tag, name)
        raise RehostError(
            f"POST {url} failed with HTTP {exc.code}: {exc.read()!r}"
        ) from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def rehost(
    url: str,
    slug: str,
    event_date: dt.date,
    *,
    repo: str,
    token: str,
    tag: str = DEFAULT_RELEASE_TAG,
) -> str:
    """Fetch ``url`` and upload it as a release asset. Return the public URL."""
    body, content_type = _fetch(url)
    ext = CONTENT_TYPE_EXTENSIONS[content_type]
    sha8 = hashlib.sha256(body).hexdigest()[:8]
    name = f"{_slug_safe(slug)}-{event_date.strftime('%Y%m%d')}-{sha8}.{ext}"
    upload_template = _ensure_release(repo, tag, token)
    return _upload_asset(
        upload_template,
        name=name,
        body=body,
        content_type=content_type,
        token=token,
        repo=repo,
        tag=tag,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url", help="source image URL to fetch")
    parser.add_argument("slug", help="event slug (used in the asset filename)")
    parser.add_argument("date", help="event date in yyyy-mm-dd")
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="owner/name (default: $GITHUB_REPOSITORY)",
    )
    parser.add_argument(
        "--tag",
        default=DEFAULT_RELEASE_TAG,
        help=f"release tag to upload to (default: {DEFAULT_RELEASE_TAG})",
    )
    return parser


def main(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv[1:])
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not set in env", file=sys.stderr)
        return 2
    if not args.repo:
        print("--repo not given and $GITHUB_REPOSITORY not set", file=sys.stderr)
        return 2
    try:
        event_date = _parse_date(args.date)
    except ValueError:
        print(f"invalid date {args.date!r}: expected yyyy-mm-dd", file=sys.stderr)
        return 2
    try:
        public_url = rehost(
            args.url, args.slug, event_date,
            repo=args.repo, token=token, tag=args.tag,
        )
    except RehostError as exc:
        print(f"rehost failed: {exc}", file=sys.stderr)
        return 1
    print(public_url)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
