#!/usr/bin/env python3
"""Daily darshan feed for the Bhakti Kutir app.

Hare Krishna Mandir, Ahmedabad posts an album of the day's darshan in its
website gallery every day, titled like "2026-11-15 Darshan". This script
finds the latest of those albums, collects the links of their photos, and
writes them to a small JSON file that the app reads every day:

    {
      "version": 1,
      "source": "https://harekrishnamandir.org/gallery?category=daily-darshan",
      "credit": "Hare Krishna Mandir, Ahmedabad",
      "updatedAt": "2026-11-15T03:07:12Z",
      "albums": [                       # newest first, up to 7 days
        {"date": "2026-11-15", "title": "2026-11-15 Darshan",
         "url": "https://harekrishnamandir.org/gallery/2026-11-15-darshan-2",
         "photos": ["https://api.harekrishnamandir.org/uploads/gallery/...jpg",
                    ...]}
      ]
    }

The photos stay on the temple's own server; only their links are listed.
If the website cannot be read, or no album is found, the script exits with an
error and the previous file is left as it was (the app keeps showing the last
darshan it has).

Usage: darshan_feed.py OUTPUT.json
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

SITE = "https://harekrishnamandir.org"
LISTS = [
    SITE + "/gallery?category=daily-darshan",
    SITE + "/gallery",
]
CREDIT = "Hare Krishna Mandir, Ahmedabad"
KEEP_DAYS = 7
MAX_PHOTOS = 40
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36 "
    "BhaktiKutirDarshanFeed/1.0"
)
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

# "/gallery/2026-11-15-darshan-2", "/gallery/2026-10-09-darshan-2026-10-09"
ALBUM_RE = re.compile(r"/gallery/((\d{4})-(\d{2})-(\d{2})-darshan[a-z0-9-]*)")
# A photo on the temple's server (also inside Next.js /_next/image links,
# once the page has been unescaped and URL-decoded).
PHOTO_RE = re.compile(
    r"https://api\.harekrishnamandir\.org/uploads/(?:legacy/)?gallery/"
    r"[A-Za-z0-9._/-]+?\.(?:jpe?g|png|webp)",
    re.IGNORECASE,
)


def fetch(url: str, tries: int = 3) -> str:
    last: Exception | None = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-IN,en;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 - retried, then reported
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"could not read {url}: {last}")


def _plain(page: str) -> str:
    """The page with HTML entities and %-escapes undone, so photo links
    hidden inside /_next/image?url=... become ordinary links."""
    text = html.unescape(page)
    # Escaped slashes in embedded JSON ("https:\\/\\/api...").
    text = text.replace("\\/", "/")
    return urllib.parse.unquote(text)


def find_albums(page: str, today: dt.date) -> dict[str, dt.date]:
    """Darshan album slugs on a gallery listing, with their dates."""
    found: dict[str, dt.date] = {}
    for m in ALBUM_RE.finditer(_plain(page)):
        slug = m.group(1)
        try:
            day = dt.date(int(m.group(2)), int(m.group(3)), int(m.group(4)))
        except ValueError:
            continue
        # Never a date in the future (a typo in an album name).
        if day <= today + dt.timedelta(days=1):
            found[slug] = day
    return found


def find_photos(page: str) -> list[str]:
    """Photo links on an album page, in page order, each once. The album's
    cover (its share image) comes first."""
    seen: list[str] = []
    for m in PHOTO_RE.finditer(_plain(page)):
        url = m.group(0)
        if url not in seen:
            seen.append(url)
    return seen[:MAX_PHOTOS]


def title_of(page: str, fallback: str) -> str:
    m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', page)
    if not m:
        m = re.search(r"<title>([^<]+)</title>", page)
    if not m:
        return fallback
    title = html.unescape(m.group(1)).split("|")[0].strip()
    return title or fallback


def build_feed(today: dt.date) -> dict:
    albums: dict[str, dt.date] = {}
    errors = []
    for url in LISTS:
        try:
            albums.update(find_albums(fetch(url), today))
        except RuntimeError as e:
            errors.append(str(e))
    if not albums:
        raise RuntimeError("no darshan albums found. " + " ".join(errors))

    # Newest days first; one entry per day (two albums of one day merge).
    by_day: dict[dt.date, list[str]] = {}
    for slug, day in albums.items():
        by_day.setdefault(day, []).append(slug)
    out = []
    for day in sorted(by_day, reverse=True)[:KEEP_DAYS]:
        photos: list[str] = []
        title = f"{day.isoformat()} Darshan"
        url = ""
        for slug in sorted(by_day[day]):
            page_url = f"{SITE}/gallery/{slug}"
            try:
                page = fetch(page_url)
            except RuntimeError as e:
                print(f"skipped {page_url}: {e}", file=sys.stderr)
                continue
            got = find_photos(page)
            if got and not url:
                url = page_url
                title = title_of(page, title)
            photos += [p for p in got if p not in photos]
        if photos:
            out.append(
                {
                    "date": day.isoformat(),
                    "title": title,
                    "url": url,
                    "photos": photos[:MAX_PHOTOS],
                }
            )
        time.sleep(1)
    if not out:
        raise RuntimeError("darshan albums found, but no photos in them")
    return {
        "version": 1,
        "source": LISTS[0],
        "credit": CREDIT,
        "albums": out,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = argv[1]
    today = dt.datetime.now(IST).date()
    feed = build_feed(today)

    try:
        with open(path, encoding="utf-8") as f:
            old = json.load(f)
    except (OSError, ValueError):
        old = {}
    same = {k: v for k, v in old.items() if k != "updatedAt"} == feed
    feed["updatedAt"] = (
        old.get("updatedAt")
        if same and old.get("updatedAt")
        else dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=1)
        f.write("\n")
    latest = feed["albums"][0]
    print(
        f"{'unchanged' if same else 'updated'}: latest {latest['date']} "
        f"({len(latest['photos'])} photos), {len(feed['albums'])} days"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
