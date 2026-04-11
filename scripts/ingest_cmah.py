#!/usr/bin/env python3
"""Ingest events from the CMAH iCal feed into _data/special_events.yml.

Source: https://angradoheroismo.pt/events.ics

This script only ADDS new events. It never modifies existing entries.
Dedup keys:
  1. `source_uid` (iCal UID) — catches re-runs of the same event.
  2. Normalized `(name, date)` tuple — catches events previously added manually.

Run with --dry-run to preview without modifying the file.
Run with --max-events N to cap additions per invocation (default: 20).

The script is text-append-based: it parses the YAML only for dedup, and
appends new entries as hand-formatted text. This preserves the file's
existing comments, quoting, and section headers.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import logging
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

import icalendar
import yaml

CMAH_ICAL_URL = "https://angradoheroismo.pt/events.ics"
REPO_ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = REPO_ROOT / "_data" / "special_events.yml"
USER_AGENT = "TerceiraEventsBot/1.0 (+https://terceiraevents.github.io)"
DESCRIPTION_MAX_CHARS = 500
DEFAULT_MAX_EVENTS = 20
LOOKAHEAD_DAYS = 365

# Conservative CMAH category → tag slug mapping. Anything not in this map is
# left untagged rather than guessed at. Keep tag slugs in sync with
# _data/event_tags.yml.
CATEGORY_TAG_MAP = {
    "Cinema": "cinema",
    "Exposições": "exhibition",
    "Exposição": "exhibition",
    "Música": "live-music",
    "Concertos": "live-music",
    "Concerto": "live-music",
    "Conferências e Literatura": "literature",
    "Literatura": "literature",
    "Livros": "literature",
    "Teatro": "theater",
    "Dança": "dance",
    "Festas Tradicionais e Touradas": "bullfighting",
    "Festas Tradicionais eTouradas": "bullfighting",  # CMAH typo seen in feed
    "Formações": "workshop",
    "Workshop": "workshop",
    "Workshops": "workshop",
    "Gastronomia": "food-drink",
    "Ar livre": "outdoor",
    "Família": "kid-friendly",
    "Infantil": "kid-friendly",
}

logger = logging.getLogger("ingest_cmah")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def normalize_name(name: str) -> str:
    """Normalize a name for dedup: lowercase, strip accents, unify dashes/quotes.

    Also decodes HTML entities because CMAH sometimes serializes `&` as `&amp;`
    in iCal fields (non-standard but observed in the feed).
    """
    name = html.unescape(name)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.lower()
    # Unify fancy quotes so "Foo" matches «Foo» (curly, guillemets, angle)
    name = re.sub(r"[\u00ab\u00bb\u2018\u2019\u201c\u201d\u2039\u203a\"']+", '"', name)
    # Unify dash variants (em, en, hyphen, minus, figure dash, ...) to a plain "-"
    name = re.sub(r"[\u2010-\u2015\u2212\-]+", "-", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


# Portuguese/English stopwords to ignore when comparing name similarity.
# Small, noisy function words that don't meaningfully distinguish events.
_DEDUP_STOPWORDS = frozenset(
    {
        "a", "o", "as", "os", "de", "do", "da", "dos", "das",
        "e", "em", "no", "na", "nos", "nas", "um", "uma",
        "the", "of", "and", "at", "in", "on", "for", "to",
    }
)


def _tokenize(name: str) -> frozenset[str]:
    """Extract non-stopword word tokens from a normalized name."""
    tokens = re.findall(r"\w+", normalize_name(name))
    return frozenset(t for t in tokens if t not in _DEDUP_STOPWORDS)


def is_similar_match(a_name: str, b_name: str) -> bool:
    """Return True if two event names look like the same event.

    Uses word-level set similarity on content tokens (stopwords stripped):

    - Jaccard |A∩B|/|A∪B| ≥ 0.6 catches near-identical names with small
      differences ("do Livro" vs "de livro", Cinema "Ready or Not 2 — O Ritual"
      vs "Ready or Not 2: O Ritual (2D)", etc).

    - Overlap coefficient |A∩B|/min(|A|,|B|) ≥ 0.8 catches asymmetric cases
      where one name is a short version and the other adds a long marketing
      suffix ("Concerto: Notas em Movimento" vs "Concerto: Notas em
      Movimento - quando a tradição encontra a energia académica").

    Requiring each input ≥3 content tokens AND ≥3 shared content tokens
    keeps false positives low on generic short names like "Cinema: X".
    """
    if normalize_name(a_name) == normalize_name(b_name):
        return True
    a_tokens = _tokenize(a_name)
    b_tokens = _tokenize(b_name)
    if len(a_tokens) < 3 or len(b_tokens) < 3:
        return False
    shared = a_tokens & b_tokens
    if len(shared) < 3:
        return False
    union = a_tokens | b_tokens
    jaccard = len(shared) / len(union)
    if jaccard >= 0.6:
        return True
    overlap = len(shared) / min(len(a_tokens), len(b_tokens))
    return overlap >= 0.8


def fetch_ical(url: str) -> icalendar.Calendar:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return icalendar.Calendar.from_ical(data)


def extract_date_time(prop) -> tuple[dt.date, str | None]:
    """Return (date, HH:MM or None) from a DTSTART property.

    iCal DATE-only values (VALUE=DATE) come back as timezone-aware datetimes
    at midnight; we detect those via the VALUE parameter and strip the time.
    """
    value = prop.dt
    value_param = prop.params.get("VALUE") if hasattr(prop, "params") else None
    if value_param == "DATE":
        if isinstance(value, dt.datetime):
            return (value.date(), None)
        return (value, None)
    if isinstance(value, dt.datetime):
        return (value.date(), value.strftime("%H:%M"))
    if isinstance(value, dt.date):
        return (value, None)
    raise ValueError(f"unexpected DTSTART type: {type(value).__name__}")


def parse_location(loc: str) -> tuple[str, str]:
    """Split a CMAH LOCATION string into (venue, address).

    CMAH format: "Venue Name, Street, Angra do Heroísmo, Ilha Terceira,
                  9700-xxx, Região Autónoma dos Açores, Portugal"
    """
    if not loc:
        return ("", "")
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    if not parts:
        return ("", "")
    if len(parts) == 1:
        return (parts[0], "")
    venue = parts[0]
    # Drop generic regional trailers to keep addresses short and legible.
    drop = {"Portugal", "Região Autónoma dos Açores", "Ilha Terceira"}
    address = ", ".join(p for p in parts[1:] if p not in drop)
    return (venue, address)


def clean_description(text: str) -> str:
    """Unescape iCal, decode HTML entities, strip tags, collapse whitespace, truncate."""
    if not text:
        return ""
    # iCal escape sequences
    text = (
        text.replace("\\n", " ")
        .replace("\\N", " ")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > DESCRIPTION_MAX_CHARS:
        truncated = text[:DESCRIPTION_MAX_CHARS].rsplit(" ", 1)[0]
        text = truncated + "…"
    return text


def map_tags(categories) -> list[str]:
    if categories is None:
        return []
    if hasattr(categories, "cats"):
        cats = [str(c) for c in categories.cats]
    elif isinstance(categories, (list, tuple)):
        cats = [str(c) for c in categories]
    else:
        cats = [str(categories)]
    tags: list[str] = []
    for c in cats:
        slug = CATEGORY_TAG_MAP.get(c.strip())
        if slug and slug not in tags:
            tags.append(slug)
    return tags


def build_map_url(venue: str) -> str:
    query = urllib.parse.quote(f"{venue} Angra do Heroísmo")
    return f"https://www.google.com/maps/search/?api=1&query={query}"


# ---------------------------------------------------------------------------
# YAML dedup + append
# ---------------------------------------------------------------------------


def load_existing_yaml(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        raise ValueError(
            f"{path}: expected a top-level YAML list, got {type(data).__name__}"
        )
    return data


def build_dedup_index(
    existing: list[dict],
) -> tuple[dict[dt.date, list[str]], set[str]]:
    """Build a dedup index from existing events.

    Returns:
      - date_to_names: map of date → list of raw names on that date
        (normalization happens inside is_similar_match).
      - source_uids: set of CMAH UIDs already present.
    """
    date_to_names: dict[dt.date, list[str]] = {}
    source_uids: set[str] = set()
    for ev in existing:
        if not isinstance(ev, dict):
            continue
        name = ev.get("name")
        date = ev.get("date")
        if name and isinstance(date, dt.date):
            date_to_names.setdefault(date, []).append(str(name))
        sid = ev.get("source_uid")
        if sid:
            source_uids.add(str(sid))
    return date_to_names, source_uids


def matches_existing(
    cmah_name: str,
    cmah_date: dt.date,
    date_to_names: dict[dt.date, list[str]],
) -> bool:
    for existing_name in date_to_names.get(cmah_date, []):
        if is_similar_match(cmah_name, existing_name):
            return True
    return False


def yaml_double_quote(s: str) -> str:
    """Double-quote a string for YAML, escaping backslashes and quotes."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


_BARE_UNSAFE = re.compile(r"""[:#'"\\{}\[\],&*!|>%@`]""")


def yaml_value(s: str) -> str:
    """Return a YAML scalar representation, quoting when needed."""
    if s is None or s == "":
        return '""'
    if _BARE_UNSAFE.search(s):
        return yaml_double_quote(s)
    if s.startswith(("-", "?", "!")) or s != s.strip():
        return yaml_double_quote(s)
    return s


def format_event_yaml(event: dict) -> str:
    """Hand-format a single event as a YAML list item."""
    out: list[str] = []
    out.append(f"- date: {event['date'].isoformat()}")
    out.append(f"  name: {yaml_double_quote(event['name'])}")
    out.append(f"  venue: {yaml_value(event['venue'])}")
    if event.get("address"):
        out.append(f"  address: {yaml_value(event['address'])}")
    if event.get("map_url"):
        out.append(f"  map_url: {event['map_url']}")
    if event.get("time"):
        out.append(f'  time: "{event["time"]}"')
    if event.get("description"):
        out.append(f"  description: {yaml_double_quote(event['description'])}")
    if event.get("source_url"):
        out.append(f"  source_url: {event['source_url']}")
    if event.get("source_uid"):
        out.append(f'  source_uid: "{event["source_uid"]}"')
    if event.get("tags"):
        out.append("  tags:")
        for t in event["tags"]:
            out.append(f"  - {t}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be added without modifying the file",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=DEFAULT_MAX_EVENTS,
        help="Max events to add per invocation (default: %(default)s)",
    )
    parser.add_argument("--url", default=CMAH_ICAL_URL, help="iCal feed URL")
    parser.add_argument(
        "--yaml-path",
        type=Path,
        default=YAML_PATH,
        help="Path to special_events.yml",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    try:
        cal = fetch_ical(args.url)
    except Exception as e:  # noqa: BLE001 — we want to swallow any fetch error
        logger.warning("failed to fetch %s: %s — exiting cleanly", args.url, e)
        return 0

    existing = load_existing_yaml(args.yaml_path)
    date_to_names, source_uids = build_dedup_index(existing)
    logger.info(
        "loaded %d existing events (%d with source_uid)",
        len(existing),
        len(source_uids),
    )

    today = dt.date.today()
    lookahead = today + dt.timedelta(days=LOOKAHEAD_DAYS)

    candidates: list[dict] = []
    skipped_dedup = 0
    skipped_window = 0
    for component in cal.walk("VEVENT"):
        try:
            uid = str(component.get("UID", "")).strip()
            summary = str(component.get("SUMMARY", "")).strip()
            if not summary:
                continue
            dtstart = component.get("DTSTART")
            if dtstart is None:
                continue
            date, time = extract_date_time(dtstart)
            if date < today or date > lookahead:
                skipped_window += 1
                continue
            if uid and uid in source_uids:
                skipped_dedup += 1
                continue
            if matches_existing(summary, date, date_to_names):
                skipped_dedup += 1
                continue
            venue, address = parse_location(str(component.get("LOCATION", "")))
            description = clean_description(str(component.get("DESCRIPTION", "")))
            url = str(component.get("URL", "")).strip() or None
            categories = component.get("CATEGORIES")
            tags = map_tags(categories)

            event = {
                "date": date,
                "name": summary,
                "venue": venue or "Angra do Heroísmo",
                "address": address,
                "map_url": build_map_url(venue or "Angra do Heroísmo"),
                "time": time,
                "description": description,
                "source_url": url,
                "source_uid": uid or None,
                "tags": tags,
            }
            candidates.append(event)
        except Exception as e:  # noqa: BLE001
            logger.warning("skipping malformed VEVENT: %s", e)
            continue

    logger.info(
        "found %d new candidate events (skipped %d dedup, %d out-of-window)",
        len(candidates),
        skipped_dedup,
        skipped_window,
    )

    if not candidates:
        logger.info("nothing to add.")
        return 0

    candidates.sort(key=lambda e: e["date"])

    if len(candidates) > args.max_events:
        logger.warning(
            "capping %d candidates to --max-events=%d",
            len(candidates),
            args.max_events,
        )
        candidates = candidates[: args.max_events]

    block = f"\n# Auto-ingested from CMAH ({today.isoformat()})\n"
    for ev in candidates:
        block += format_event_yaml(ev) + "\n"

    if args.dry_run:
        sys.stdout.write(block)
        logger.info("[dry-run] would add %d events", len(candidates))
        return 0

    with args.yaml_path.open("a", encoding="utf-8") as f:
        f.write(block)

    logger.info("added %d events to %s", len(candidates), args.yaml_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
