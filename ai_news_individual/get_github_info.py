#!/usr/bin/env python3
"""Fetch daily GitHub trending repositories into github_temp.json."""

from __future__ import annotations

import argparse
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
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_PATH = ROOT / "github_temp.json"
TRENDING_URL = "https://github.com/trending?since=daily"
SEARCH_URL = "https://api.github.com/search/repositories"
USER_AGENT = "Mozilla/5.0 (compatible; QwenPaw-ai_news_individual/1.0)"
AI_KEYWORDS = [
    "ai",
    "agent",
    "agents",
    "llm",
    "llms",
    "rag",
    "openai",
    "claude",
    "anthropic",
    "gemini",
    "qwen",
    "deepseek",
    "transformer",
    "diffusion",
    "inference",
    "cursor",
    "copilot",
    "mcp",
    "embedding",
    "machine learning",
]


def log(message: str) -> None:
    print(message, file=sys.stderr)


def ssl_context() -> ssl.SSLContext | None:
    value = os.getenv("GITHUB_INSECURE_SSL", "").strip().lower()
    if value in {"1", "true", "yes"}:
        log("[warn] GITHUB_INSECURE_SSL=1; HTTPS certificate verification is disabled for GitHub fetching")
        return ssl._create_unverified_context()
    return None


def fetch_url(url: str, timeout: int, retries: int) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"fetch failed: {url}: {last_error}")


def strip_tags(value: str) -> str:
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", value or "")
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def number_from_text(value: str) -> int:
    match = re.search(r"(\d[\d,]*)", value or "")
    if not match:
        return 0
    return int(match.group(1).replace(",", ""))


def parse_trending(content: bytes) -> list[dict[str, Any]]:
    text = content.decode("utf-8", errors="replace")
    blocks = re.split(r"<article\s+class=\"Box-row\"", text)
    repos: list[dict[str, Any]] = []

    for block in blocks[1:]:
        href_match = re.search(r'href="/([^"/\s]+/[^"/\s]+)"', block)
        if not href_match:
            continue
        full_name = html.unescape(href_match.group(1)).strip()
        if "/" not in full_name:
            continue
        owner, name = full_name.split("/", 1)

        desc_match = re.search(r"<p[^>]*>(.*?)</p>", block, flags=re.S)
        description = strip_tags(desc_match.group(1)) if desc_match else ""

        language_match = re.search(r'itemprop="programmingLanguage"[^>]*>(.*?)</span>', block, flags=re.S)
        language = strip_tags(language_match.group(1)) if language_match else ""

        stars_total = 0
        stars_match = re.search(rf'href="/{re.escape(full_name)}/stargazers"[^>]*>(.*?)</a>', block, flags=re.S)
        if stars_match:
            stars_total = number_from_text(strip_tags(stars_match.group(1)))

        stars_today = 0
        today_match = re.search(r"(\d[\d,]*)\s+stars?\s+today", strip_tags(block), flags=re.I)
        if today_match:
            stars_today = int(today_match.group(1).replace(",", ""))

        repos.append(
            {
                "repo": name,
                "owner": owner,
                "full_name": full_name,
                "url": f"https://github.com/{full_name}",
                "description": description,
                "language": language,
                "stars": stars_total,
                "stars_today": stars_today,
                "source": "github_trending_daily",
            }
        )

    return repos


def looks_ai_related(repo: dict[str, Any]) -> bool:
    haystack = " ".join([repo.get("repo", ""), repo.get("owner", ""), repo.get("full_name", ""), repo.get("description", "")]).lower()
    return any(keyword in haystack for keyword in AI_KEYWORDS)


def fetch_search_fallback(timeout: int, retries: int, limit: int) -> list[dict[str, Any]]:
    query = "AI OR LLM OR agent OR RAG stars:>100"
    params = urllib.parse.urlencode({"q": query, "sort": "updated", "order": "desc", "per_page": limit})
    content = fetch_url(f"{SEARCH_URL}?{params}", timeout=timeout, retries=retries)
    data = json.loads(content.decode("utf-8"))
    repos: list[dict[str, Any]] = []
    for item in data.get("items", []):
        repos.append(
            {
                "repo": item.get("name", ""),
                "owner": item.get("owner", {}).get("login", ""),
                "full_name": item.get("full_name", ""),
                "url": item.get("html_url", ""),
                "description": item.get("description") or "",
                "language": item.get("language") or "",
                "stars": item.get("stargazers_count") or 0,
                "stars_today": 0,
                "source": "github_search_fallback",
            }
        )
    return repos


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch AI-related GitHub daily trending repositories.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--limit", type=int, default=int(os.getenv("GITHUB_TRENDING_LIMIT", "20")))
    parser.add_argument("--timeout", type=int, default=int(os.getenv("GITHUB_TRENDING_TIMEOUT", "60")))
    parser.add_argument("--retries", type=int, default=int(os.getenv("GITHUB_TRENDING_RETRIES", "1")))
    parser.add_argument("--include-non-ai", action="store_true")
    args = parser.parse_args()

    repos: list[dict[str, Any]] = []
    try:
        repos = parse_trending(fetch_url(TRENDING_URL, timeout=args.timeout, retries=args.retries))
        log(f"[ok] github trending: {len(repos)} repos")
    except Exception as exc:
        log(f"[warn] github trending fetch failed: {exc}")
        try:
            repos = fetch_search_fallback(timeout=args.timeout, retries=args.retries, limit=args.limit)
            log(f"[ok] github search fallback: {len(repos)} repos")
        except Exception as fallback_exc:
            log(f"[warn] github search fallback failed: {fallback_exc}")
            repos = []

    filtered = repos if args.include_non_ai else [repo for repo in repos if looks_ai_related(repo)]
    if len(filtered) < 3:
        for repo in repos:
            if repo not in filtered:
                filtered.append(repo)
            if len(filtered) >= 3:
                break

    filtered.sort(key=lambda item: (item.get("stars_today", 0), item.get("stars", 0)), reverse=True)
    output = filtered[: max(args.limit, 1)]

    output_path = Path(args.output)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    log(f"[done] wrote {len(output)} repos to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
