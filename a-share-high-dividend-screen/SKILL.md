---
name: a-share-high-dividend-screen
description: Screen A-share high-dividend stocks across industries with TuShare and AKShare, append technology or AI theme candidates, calculate 10-year PE historical percentiles, and output score-sorted CSV artifacts. Use when analyzing A股红利股、高股息、行业TopN、主题补充、PE历史分位、综合分排序, or refreshing files like a_share_high_dividend_industry_top3_*.csv.
---

# A股高股息筛选

## Overview

Use this skill to recreate the A-share high-dividend screening workflow used in
`cbqpt`: broad industry coverage, optional theme append, 10-year PE percentile,
and configurable composite scoring.

Prefer the bundled script for repeatable runs:

```bash
python3 .agents/skills/a-share-high-dividend-screen/scripts/screen_a_share_high_dividend.py
```

Run it from `/Users/eclipse/Documents/projects/cbqpt` unless the user gives a
different checkout.

## Default Workflow

1. Confirm the desired scoring formula, hard filters, and themes if the user
   asks for a new market scan. If the user names a formula explicitly, use it.
2. Pull the latest usable TuShare `daily_basic` snapshot for A股 valuation
   fields: `dv_ttm`, `total_mv`, `pe_ttm`, `pb`.
3. Pull TuShare `stock_basic` for stock names, board, list date, and industry.
4. Pull AKShare `stock_yjbb_em` for the report period requested by the user
   or `20260331` by default: ROE, profit YoY, gross margin.
5. Apply hard filters:
   - exclude ST and delisting-risk names by stock name;
   - include 主板、创业板、科创板 by default;
   - require `股息率TTM >= 3`;
   - require `总市值亿元 >= 100`;
   - require positive `PE`, `PB`, and `ROE_2026Q1`.
6. Calculate `10年PE历史分位` from TuShare `daily_basic.pe_ttm`.
   Use the last 10 years ending on the snapshot date; if listed for less than
   10 years, start at `list_date`. Ignore missing and non-positive PE values.
7. Recalculate `综合分` from the configured weights.
8. Select each industry's TopN rows, then append matching theme candidates that
   pass filters but were not already selected.
9. Sort final output by `综合分` descending and write CSV with `utf-8-sig`.
10. Verify row count, required columns, no missing score inputs, and descending
    sort before reporting the file paths.
11. Send a short DingTalk 工作通知 summary via the enterprise internal app robot
    when notification config is enabled in `分析配置.json`; include runtime,
    output file, and `🏆 综合分Top10：`.

## Script Usage

The script writes these files under `data/outputs` by default:

- `a_share_high_dividend_industry_top3_<trade_date>.csv`
- `a_share_high_dividend_industry_top3_<trade_date>_latest.csv`
- `a_share_high_dividend_all_candidates_<trade_date>.csv`
- `a_share_high_dividend_theme_candidates_<trade_date>.csv`
- `a_share_high_dividend_theme_append_<trade_date>.csv`
- `a_share_high_dividend_pe_percentile_<trade_date>_cache.csv`

Useful examples:

```bash
# Default: high-dividend industry Top3 plus built-in tech and AI themes.
python3 .agents/skills/a-share-high-dividend-screen/scripts/screen_a_share_high_dividend.py

# Use a fixed snapshot date and the latest formula requested by the user.
python3 .agents/skills/a-share-high-dividend-screen/scripts/screen_a_share_high_dividend.py \
  --trade-date 20260703 \
  --weight-pe-value 0.40 \
  --weight-dividend 0.30 \
  --weight-roe 0.20 \
  --weight-market-cap 0.05 \
  --weight-gross-margin 0.05 \
  --weight-profit-yoy 0

# Add a custom theme without changing the script.
python3 .agents/skills/a-share-high-dividend-screen/scripts/screen_a_share_high_dividend.py \
  --theme "robot=机器人|人工智能|智能|自动|伺服|机器视觉"

# Run without sending DingTalk notification.
python3 .agents/skills/a-share-high-dividend-screen/scripts/screen_a_share_high_dividend.py \
  --no-notify-dingding
```

## Scoring

All score components are on a 0-100 scale except raw report fields explicitly
requested by the user.

Default formula:

```text
综合分 =
  (100 - 10年PE历史分位) * 40%
  + 股息率分位 * 30%
  + ROE分位 * 20%
  + 总市值分位 * 5%
  + 销售毛利率_2026Q1 * 5%
```

Interpret `10年PE历史分位` as valuation expensiveness: lower is cheaper. When a
formula says `(100 - 10年PE历史分位)`, use PE value score where higher is better.

If the user asks for `净利润同比_2026Q1 * 10%`, treat it as the raw YoY
percentage unless they explicitly ask for a percentile. Missing raw report
fields are scored as `0` and should be mentioned in the final note.

## Theme Append Rules

Use built-in themes when the user asks for technology or AI coverage:

- `tech`: 科技、半导体、芯片、存储、光模块、通信、电信、IT设备、元器件、互联网。
- `ai_robot`: 机器人、AI、人工智能、智能制造、自动化、机器视觉、伺服、工控、传感、工业软件。

Theme append means: keep the broad industry TopN output, then append additional
qualified theme rows not already selected. Do not replace the industry pool.

Preserve negative findings. If a theme has no high-dividend names under the hard
filters, say that clearly and keep the candidate/append CSV for auditability.

## DingTalk Notification

Push goes through a DingTalk **enterprise internal app robot** (工作通知), not a
custom robot webhook. The script exchanges `client_id` / `client_secret` for an
access token at `POST https://api.dingtalk.com/v1.0/oauth2/accessToken`, then
sends via `POST /topapi/message/corpconversation/asyncsend_v2`.

By default it sends a text summary after completion or failure when all of these
are true:

- `发送通知` is `真` in the project root `分析配置.json`;
- `发送方式` is `钉钉`;
- `钉钉应用机器人.启用` is `真` (absent node defaults to enabled);
- `client_id`, `client_secret`, and `agent_id` all resolve;
- at least one receiver resolves: `userid_list`, `dept_id_list`, or
  `发给全部可见范围` is `真`.

Credentials resolve **environment variable first, `分析配置.json` as fallback**:

| Env var | Config key under `钉钉应用机器人` |
| --- | --- |
| `DINGTALK_CLIENT_ID` | `client_id` |
| `DINGTALK_CLIENT_SECRET` | `client_secret` |
| `DINGTALK_AGENT_ID` | `agent_id` |
| `DINGTALK_USERID_LIST` (comma-separated) | `userid_list` |
| `DINGTALK_DEPT_ID_LIST` (comma-separated) | `dept_id_list` |
| `DINGTALK_TO_ALL_USER` | `发给全部可见范围` |

Keep `client_secret` empty in `分析配置.json` and supply it via
`DINGTALK_CLIENT_SECRET` — that file is checked into the repo.

The success message includes elapsed time, completion time, snapshot date,
final row count, industry count, theme candidate/append counts, output CSV
filename, and `🏆 综合分Top10：`.

Use `--no-notify-dingding` for dry runs, tests, or manual analysis where no
DingTalk message should be sent. Never print or expose the client secret or
access token in terminal output or final responses; `send_dingding_text` and
`fetch_dingding_access_token` mask them in every error path.

The app needs the 工作通知 send scope. Address-book scopes
(`qyapi_get_department_member` / `qyapi_get_department_list`) are **not** granted
on the current app, so `userid_list` cannot be discovered programmatically —
it must be configured by hand.

## Validation Checklist

Before claiming completion:

- Read the generated CSV back with `pandas.read_csv(..., encoding="utf-8-sig")`.
- Confirm `综合分` is monotonic descending.
- Confirm required columns exist:
  `行业`, `证券代码`, `证券名称`, `股息率TTM`, `总市值亿元`, `PE`,
  `10年PE历史分位`, `PB`, `ROE_2026Q1`, `净利润同比_2026Q1`,
  `销售毛利率_2026Q1`, `综合分`.
- Confirm the `_latest.csv` copy matches the main CSV if one is written.
- Report the exact output path and top 5-10 names.

## Caveats

- Eastmoney/AKShare endpoints may be slow or briefly unavailable. Retry once or
  rerun; the script caches PE percentile results as it progresses.
- TuShare `daily_basic` may have no data on weekends or holidays. Search
  backward for the latest usable trading date unless the user fixed a date.
- Do not present this as investment advice. Treat it as a quantitative
  candidate screen that still needs business-quality and risk review.
