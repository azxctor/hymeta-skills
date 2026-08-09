#!/usr/bin/env python3
"""Fetch AI industry news into temp.json.

This script uses only the Python standard library so the skill can run in a
plain QwenPaw workspace without extra package installation.
"""

from __future__ import annotations

import argparse
import email.utils
import html
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCES_PATH = ROOT / "sources.json"
DEFAULT_OUTPUT_PATH = ROOT / "temp.json"
USER_AGENT = "Mozilla/5.0 (compatible; QwenPaw-ai_news_individual/1.0)"


DEFAULT_SOURCES = {
    "rss_sources": [
        {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml", "priority_hint": "P0"},
        {"name": "Google DeepMind Blog", "url": "https://deepmind.google/blog/feed/basic/", "priority_hint": "P0"},
        {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "priority_hint": "P1"},
        {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "priority_hint": "P2"},
        {"name": "VentureBeat", "url": "https://venturebeat.com/feed/", "priority_hint": "P2"},
        {"name": "The Decoder", "url": "https://the-decoder.com/feed/", "priority_hint": "P2"},
        {"name": "arXiv cs.AI", "url": "https://export.arxiv.org/rss/cs.AI", "priority_hint": "P2"},
    ]
}


def log(message: str) -> None:
    print(message, file=sys.stderr)


def ssl_context() -> ssl.SSLContext | None:
    value = os.getenv("AI_NEWS_INSECURE_SSL", "").strip().lower()
    if value in {"1", "true", "yes"}:
        log("[warn] AI_NEWS_INSECURE_SSL=1; HTTPS certificate verification is disabled for news fetching")
        return ssl._create_unverified_context()
    return None


class Redirect308Handler(urllib.request.HTTPRedirectHandler):
    def http_error_308(self, req, fp, code, msg, headers):  # type: ignore[no-untyped-def]
        return self.http_error_302(req, fp, code, msg, headers)


def load_sources(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return list(DEFAULT_SOURCES["rss_sources"])
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    sources = data.get("rss_sources") or data.get("sources") or []
    enabled = [source for source in sources if source.get("enabled", True)]
    return enabled or list(DEFAULT_SOURCES["rss_sources"])


def fetch_url(url: str, timeout: int, retries: int) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        current_url = url
        try:
            for _ in range(5):
                req = urllib.request.Request(current_url, headers={"User-Agent": USER_AGENT})
                context = ssl_context()
                handlers: list[urllib.request.BaseHandler] = [Redirect308Handler()]
                if context is not None:
                    handlers.append(urllib.request.HTTPSHandler(context=context))
                opener = urllib.request.build_opener(*handlers)
                try:
                    with opener.open(req, timeout=timeout) as resp:
                        return resp.read()
                except urllib.error.HTTPError as exc:
                    location = exc.headers.get("Location")
                    if exc.code in {301, 302, 303, 307, 308} and location:
                        current_url = urllib.parse.urljoin(current_url, location)
                        continue
                    raise
            raise RuntimeError(f"too many redirects: {url}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"fetch failed: {url}: {last_error}")


def strip_html(value: str) -> str:
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", value or "")
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def text_or_empty(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def parse_datetime(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        dt = email.utils.parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return value


def item_datetime(item: dict[str, Any]) -> datetime | None:
    value = item.get("published_at") or ""
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def parse_rss(content: bytes, source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ET.fromstring(content)
    items: list[dict[str, Any]] = []

    for node in root.findall(".//item"):
        title = text_or_empty(node.find("title"))
        link = text_or_empty(node.find("link"))
        summary = text_or_empty(node.find("description"))
        published = text_or_empty(node.find("pubDate")) or text_or_empty(node.find("published")) or text_or_empty(node.find("updated"))
        if not title or not link:
            continue
        items.append(
            {
                "title": strip_html(title),
                "url": link,
                "summary": strip_html(summary),
                "source": source.get("name") or source.get("url"),
                "source_url": source.get("url"),
                "priority_hint": source.get("priority_hint", ""),
                "published_at": parse_datetime(published),
            }
        )

    atom_ns = "{http://www.w3.org/2005/Atom}"
    for node in root.findall(f".//{atom_ns}entry"):
        title = text_or_empty(node.find(f"{atom_ns}title"))
        link = ""
        for link_node in node.findall(f"{atom_ns}link"):
            href = link_node.attrib.get("href")
            if href:
                link = href
                break
        summary = text_or_empty(node.find(f"{atom_ns}summary")) or text_or_empty(node.find(f"{atom_ns}content"))
        published = text_or_empty(node.find(f"{atom_ns}published")) or text_or_empty(node.find(f"{atom_ns}updated"))
        if not title or not link:
            continue
        items.append(
            {
                "title": strip_html(title),
                "url": link,
                "summary": strip_html(summary),
                "source": source.get("name") or source.get("url"),
                "source_url": source.get("url"),
                "priority_hint": source.get("priority_hint", ""),
                "published_at": parse_datetime(published),
            }
        )

    return items


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("url") or item.get("title") or "").strip().lower()
        key = re.sub(r"[?#].*$", "", key)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def within_window(item: dict[str, Any], days: int) -> bool:
    if days <= 0:
        return True
    dt = item_datetime(item)
    if dt is None:
        return True
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch AI news RSS feeds.")
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--days", type=int, default=int(os.getenv("AI_NEWS_DAYS", "3")))
    parser.add_argument("--limit", type=int, default=int(os.getenv("AI_NEWS_LIMIT", "80")))
    parser.add_argument("--timeout", type=int, default=int(os.getenv("AI_NEWS_TIMEOUT", "25")))
    parser.add_argument("--retries", type=int, default=int(os.getenv("AI_NEWS_RETRIES", "1")))
    args = parser.parse_args()

    sources = load_sources(Path(args.sources))
    all_items: list[dict[str, Any]] = []
    errors: list[str] = []

    for source in sources:
        url = str(source.get("url") or "").strip()
        if not url:
            continue
        try:
            content = fetch_url(url, timeout=args.timeout, retries=args.retries)
            items = parse_rss(content, source)
            all_items.extend(items)
            log(f"[ok] {source.get('name', url)}: {len(items)} items")
        except Exception as exc:
            errors.append(f"{source.get('name', url)}: {exc}")
            log(f"[warn] {source.get('name', url)}: {exc}")

    filtered = [item for item in dedupe(all_items) if within_window(item, args.days)]
    filtered.sort(key=lambda item: item_datetime(item) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    output_items = filtered[: max(args.limit, 1)]

    output_path = Path(args.output)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(output_items, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    log(f"[done] wrote {len(output_items)} items to {output_path}")
    if errors:
        log("[warn] failed sources:")
        for error in errors:
            log(f"  - {error}")

    return 0 if output_items else 2


if __name__ == "__main__":
    raise SystemExit(main())
