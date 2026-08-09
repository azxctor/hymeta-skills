#!/usr/bin/env python3
"""Send temp.md as a DingTalk one-to-one robot markdown message."""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
BATCH_SEND_URL = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
DEFAULT_FILE = ROOT / "temp.md"
DEFAULT_RESULT_FILE = ROOT / "send_result.json"
DEFAULT_CACHE_FILE = ROOT / ".dingtalk_token_cache.json"
DEFAULT_USER_IDS = ["0160641832681292680"]
USER_AGENT = "QwenPaw-ai_news_individual/1.0"


def log(message: str) -> None:
    print(message, file=sys.stderr)


def ssl_context() -> ssl.SSLContext | None:
    value = os.getenv("DINGTALK_INSECURE_SSL", "").strip().lower()
    if value in {"1", "true", "yes"}:
        log("[warn] DINGTALK_INSECURE_SSL=1; HTTPS certificate verification is disabled for DingTalk requests")
        return ssl._create_unverified_context()
    return None


def env_first(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip()
    return ""


def require_env(*names: str) -> str:
    value = env_first(*names)
    if not value:
        joined = " / ".join(names)
        raise SystemExit(f"missing required environment variable: {joined}")
    return value


def parse_user_ids(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        raise SystemExit("--userIdList cannot be empty")
    try:
        value = json.loads(raw)
        if isinstance(value, str):
            user_ids = [value]
        elif isinstance(value, list):
            user_ids = [str(item).strip() for item in value if str(item).strip()]
        else:
            raise ValueError("not a string or list")
    except Exception:
        user_ids = [part.strip() for part in re.split(r"[,;\s]+", raw) if part.strip()]
    if not user_ids:
        raise SystemExit("no valid DingTalk userId found in --userIdList")
    return user_ids


def chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def request_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None, timeout: int = 30) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req_headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
            content = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {url}: {error_body}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"request failed {url}: {exc}") from exc
    try:
        return json.loads(content) if content else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON response from {url}: {content[:500]}") from exc


def load_cached_token(cache_file: Path, client_id: str) -> str:
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return ""
    if data.get("client_id") != client_id:
        return ""
    if float(data.get("expires_at", 0)) <= time.time() + 300:
        return ""
    return str(data.get("access_token") or "")


def save_cached_token(cache_file: Path, client_id: str, token: str, expires_in: int) -> None:
    data = {
        "client_id": client_id,
        "access_token": token,
        "expires_at": time.time() + max(expires_in - 300, 60),
    }
    cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        cache_file.chmod(0o600)
    except OSError:
        pass


def get_access_token(client_id: str, client_secret: str, cache_file: Path, timeout: int) -> str:
    cached = load_cached_token(cache_file, client_id)
    if cached:
        log("[ok] using cached DingTalk access token")
        return cached

    corp_id = env_first("DINGTALK_CORP_ID")
    if corp_id:
        url = f"https://api.dingtalk.com/v1.0/oauth2/{corp_id}/token"
        payload = {"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
    else:
        url = TOKEN_URL
        payload = {"appKey": client_id, "appSecret": client_secret}

    data = request_json(url, payload, timeout=timeout)
    token = str(data.get("accessToken") or data.get("access_token") or "")
    expires_in = int(data.get("expireIn") or data.get("expires_in") or 7200)
    if not token:
        raise RuntimeError(f"DingTalk token response missing accessToken: {data}")
    save_cached_token(cache_file, client_id, token, expires_in)
    log("[ok] fetched DingTalk access token")
    return token


def title_from_markdown(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                return title[:80]
    return "AI 行业速递"


def build_payload(robot_code: str, user_ids: list[str], markdown: str) -> dict[str, Any]:
    msg_param = {"title": title_from_markdown(markdown), "text": markdown}
    return {
        "robotCode": robot_code,
        "userIds": user_ids,
        "msgKey": "sampleMarkdown",
        "msgParam": json.dumps(msg_param, ensure_ascii=False),
    }


def send_batch(access_token: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    return request_json(
        BATCH_SEND_URL,
        payload,
        headers={"x-acs-dingtalk-access-token": access_token},
        timeout=timeout,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Send AI news markdown to DingTalk robot one-to-one chats.")
    parser.add_argument(
        "--userIdList",
        default=os.getenv("DINGTALK_DEFAULT_USER_IDS", json.dumps(DEFAULT_USER_IDS)),
        help='JSON array or comma-separated DingTalk userIds, default: \'["0160641832681292680"]\'',
    )
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="Markdown report file, default: temp.md")
    parser.add_argument("--result", default=str(DEFAULT_RESULT_FILE), help="JSON send result output path")
    parser.add_argument("--cache", default=str(os.getenv("DINGTALK_TOKEN_CACHE", DEFAULT_CACHE_FILE)))
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("DINGTALK_BATCH_SIZE", "20")))
    parser.add_argument("--timeout", type=int, default=int(os.getenv("DINGTALK_TIMEOUT", "30")))
    parser.add_argument("--dry-run", action="store_true", help="Validate payload and write send_result.json without sending")
    args = parser.parse_args()

    user_ids = parse_user_ids(args.userIdList)
    report_path = Path(args.file)
    if not report_path.exists():
        raise SystemExit(f"report file not found: {report_path}")
    markdown = report_path.read_text(encoding="utf-8").strip()
    if len(markdown.encode("utf-8")) <= 800:
        raise SystemExit("report file is too small; expected >800 bytes")

    client_id = require_env("DINGTALK_CLIENT_ID", "DINGTALK_APP_KEY")
    client_secret = require_env("DINGTALK_CLIENT_SECRET", "DINGTALK_APP_SECRET")
    robot_code = env_first("DINGTALK_ROBOT_CODE") or client_id
    batch_size = max(1, min(args.batch_size, 100))

    result: dict[str, Any] = {"dry_run": bool(args.dry_run), "robotCode": robot_code, "userIds": user_ids, "batches": []}

    if args.dry_run:
        for batch in chunked(user_ids, batch_size):
            result["batches"].append({"request": build_payload(robot_code, batch, markdown), "response": None})
        Path(args.result).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        log(f"[dry-run] wrote payload preview to {args.result}")
        return 0

    access_token = get_access_token(client_id, client_secret, Path(args.cache), args.timeout)
    has_partial_failure = False
    for batch in chunked(user_ids, batch_size):
        payload = build_payload(robot_code, batch, markdown)
        response = send_batch(access_token, payload, args.timeout)
        result["batches"].append({"request_userIds": batch, "response": response})
        invalid = response.get("invalidStaffIdList") or []
        limited = response.get("flowControlledStaffIdList") or []
        if invalid or limited:
            has_partial_failure = True
            log(f"[warn] invalid={invalid} flow_controlled={limited}")

    Path(args.result).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"[done] wrote send result to {args.result}")
    return 3 if has_partial_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
