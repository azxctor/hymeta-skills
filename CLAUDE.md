# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A collection of **Agent Skills** — prompt/instruction packages, not an application. There is no build, no test suite, no linter, no root package manifest. Each top-level directory is one self-contained skill that gets copied or symlinked into an agent's skills directory at install time.

Editing here means editing Markdown that an agent will later read as instructions. The "correctness" bar is whether an agent following the file produces consistent, high-quality output — not whether code compiles.

## Skill anatomy

```
<skill-name>/
├── SKILL.md          # required — entry point, YAML frontmatter + instructions
├── references/       # optional — deep detail loaded on demand
├── assets/           # optional — binary style references (PNG, etc.)
├── scripts/          # optional — executable code the skill invokes
└── agents/openai.yaml # optional — non-Claude host manifest
```

`SKILL.md` frontmatter carries `name` and `description`. The `description` is the routing signal — it must state both *what* the skill does and *when to trigger it*, including the natural-language phrasings (Chinese and English) a user would actually type. Several descriptions here deliberately enumerate trigger phrases and explicit "do NOT use for…" exclusions; preserve that when editing.

**Progressive disclosure is the core pattern.** `SKILL.md` stays short and tells the agent to read a specific `references/*.md` at a specific step ("**必须先阅读 `references/html-template-guide.md`**"). Heavy detail belongs in `references/`, never inlined. When adding detail, extend or add a reference file and point to it from the workflow step that needs it.

### Paths inside SKILL.md are install paths, not repo paths

This trips people up. Skills reference themselves by where they will be *installed*, which has no relation to this repo's layout:

- `a-share-high-dividend-screen` → `.agents/skills/<name>/scripts/...`, run from a **`cbqpt`** checkout
- `ai_news_individual` → `${QWENPAW_WORKING_DIR:-$HOME/.qwenpaw}/workspaces/default/skills/<name>/`
- `docx` / `pdf` / `pptx` / `xlsx` → relative, via `cd {this_skill_dir} && python scripts/...`

Do not "fix" these to match the repo. Two skills also target the **QwenPaw** runtime rather than Claude Code — `ai_news_individual` instructs the agent to use QwenPaw's file-write tool and forbids `read_file` in favor of `python3 -c`. That is intentional host-specific wording.

## Two provenance classes — know which you are editing

| Class | Skills | Rule |
| --- | --- | --- |
| **Hand-authored** (this project's own) | `a-share-high-dividend-screen`, `ai_news_individual`, `frontend-design`, `taste-skill`, `image2-blue-tech-infographic`, `tech-tutorial-builder` | Edit freely |
| **Vendored upstream** (Anthropic built-ins) | `docx`, `pdf`, `pptx`, `xlsx` | Treat as read-only |

The vendored four are identifiable by `metadata.builtin_skill_version: "1.1"` plus `license: Proprietary. LICENSE.txt has complete terms` and a bundled `LICENSE.txt`. They are upstream copies — local edits are lost on the next version bump, so make changes upstream, not here.

Their `scripts/office/` helper library (51 files: `pack.py`, `unpack.py`, `validate.py`, `soffice.py`, `helpers/`, `schemas/`, `validators/`) is **duplicated into `docx`, `pptx`, and `xlsx` separately** — near-identical but `soffice.py` already differs between them. A fix in one does not propagate to the others.

`metadata:` in frontmatter is host-specific and varies by skill: `metadata.qwenpaw` (emoji + `requires.env`) for `ai_news_individual`, `metadata.builtin_skill_version` for the vendored four. `agents/openai.yaml` is a third, parallel manifest for OpenAI-style hosts — `interface.display_name`, `short_description`, `default_prompt` (uses `$skill-name` invocation syntax), `brand_color`, `policy.allow_implicit_invocation`. Only `a-share-high-dividend-screen` and `image2-blue-tech-infographic` ship one. None of these affect Claude Code.

## The skills

| Directory | Domain |
| --- | --- |
| `a-share-high-dividend-screen/` | A股高股息量化筛选 → 排序 CSV + 钉钉工作通知 |
| `ai_news_individual/` | AI 资讯 + GitHub 热榜 → 日报 → 钉钉单聊推送 |
| `frontend-design/` | General production-grade frontend: components, pages, apps |
| `taste-skill/` | Landing pages / portfolios / redesigns only (declares `name: design-taste-frontend`) |
| `image2-blue-tech-infographic/` | Prompt generation for blue-white Chinese technical infographics |
| `tech-tutorial-builder/` | Interactive HTML tutorial + examples + runnable project, zipped |
| `docx/` `pdf/` `pptx/` `xlsx/` | Vendored Anthropic document-manipulation skills |

### Two frontend skills — pick deliberately

`frontend-design` and `taste-skill` overlap and are both anti-"AI slop". They are not interchangeable: `taste-skill` scopes itself explicitly to landing pages, portfolios, and redesigns and declares dashboards, data tables, and multi-step product UI **out of scope** (§13). Route anything app-like to `frontend-design`. When editing either, check the other for a contradicting rule.

`taste-skill` is ~1200 lines organized as numbered sections (§0 brief inference → §14 pre-flight check) plus appendices. Its rules are explicitly contextual — "None of it fires automatically" — so new rules must state their trigger condition, not read as unconditional law.

### Both DingTalk skills share one app, two different APIs

`a-share-high-dividend-screen` and `ai_news_individual` both push through the same **hymeta** enterprise internal app and both resolve `DINGTALK_CLIENT_ID` / `DINGTALK_CLIENT_SECRET` from the environment. They use different endpoints and must not be conflated:

| | a-share | ai_news_individual |
| --- | --- | --- |
| Channel | 工作通知 | 机器人单聊 |
| Send API | `/topapi/message/corpconversation/asyncsend_v2` | `/v1.0/robot/oToMessages/batchSend` |
| Extra config | `agent_id`, receiver lists | `DINGTALK_ROBOT_CODE` (falls back to client ID) |

Both fetch tokens from `POST https://api.dingtalk.com/v1.0/oauth2/accessToken`. Neither may print the secret or token in output. Address-book scopes are not granted on this app, so `userid_list` cannot be discovered programmatically — it is configured by hand (default recipient is hardcoded in both).

## Running things

Nothing at the repo root is runnable. The two skills with executable code run from elsewhere:

```bash
# a-share: MUST run from a cbqpt checkout — find_project_root() walks up looking for
# utils/tushare_config.py and raises if absent. Needs pandas, numpy, requests, akshare.
python3 .agents/skills/a-share-high-dividend-screen/scripts/screen_a_share_high_dividend.py \
  --trade-date 20260703 --weight-pe-value 0.40 --weight-dividend 0.30 --weight-roe 0.20

# Always use this for tests and manual runs — suppresses the DingTalk push
python3 .../screen_a_share_high_dividend.py --no-notify-dingding

# ai_news_individual: strict 6-step pipeline, no step may be skipped
cd ai_news_individual/
python3 get_ai_info.py        # → temp.json
python3 get_github_info.py    # → github_temp.json (allow ≥400s timeout)
python3 send_ai_info.py --userIdList '["<id>"]'   # then check send_result.json

# vendored document skills
cd docx && python scripts/<script>.py   # pdf OCR extras: pip install pytesseract pdf2image
```

`ai_news_individual` writes runtime artifacts (`temp.json`, `github_temp.json`, `temp.md`, `send_result.json`, `.dingtalk_token_cache.json`) into its own directory. Its nested `.gitignore` already excludes all of them — keep it that way; the token cache holds a live access token.

If a skill's documented behavior changes, `SKILL.md` and the script must be updated together — the a-share SKILL.md scoring formula, hard filters, and output filenames all mirror script constants and `parse_args()` defaults.

## Conventions when adding or editing a skill

- Directory name should equal frontmatter `name`. Nine of ten follow this; `taste-skill/` declares `design-taste-frontend` and does not. Claude Code resolves skills by directory name, so match the directory when creating anything new.
- Match the existing file's language. `tech-tutorial-builder` and `ai_news_individual` are Chinese throughout; `a-share-high-dividend-screen` is English prose about Chinese-labeled data with Chinese column names (`综合分`, `10年PE历史分位`) kept verbatim — those strings are contracts with the CSV output, don't translate them.
- Skills that produce artifacts end with an explicit verification step listing what to check before claiming completion (`a-share` §Validation Checklist, `tech-tutorial-builder` 步骤 4, `ai_news_individual` Step 5's `wc -c temp.md` > 800 bytes gate). Keep that shape for new artifact-producing skills.
- `ai_news_individual`'s Step 4 report template is fill-in-the-blank only — its `#`/`###`/`---`/emoji skeleton is declared immutable ("你只是个填空机器"). Do not reformat it when editing surrounding prose.
- `frontend-design/SKILL.md` frontmatter points at `LICENSE.txt`, which is not present in that directory (the vendored four do ship theirs).

## The superpowers plugin is installed

`superpowers` v6.2.0 (obra/superpowers, MIT) is installed **globally**, via `superpowers-marketplace` — not vendored into this repo and not a project-scoped dependency. It contributes 14 skills under the `superpowers:` namespace covering TDD, systematic debugging, plan writing/execution, subagent dispatch, git worktrees, and code review.

Two of them matter directly for work here:

- **`superpowers:writing-skills`** — the natural tool for authoring or editing anything in this repo. Reach for it before hand-rolling a new `SKILL.md`.
- **`superpowers:using-superpowers`** — a session-start directive requiring a skill invocation before any response. It applies to *this agent's* behavior, not to the skills stored here.

Be careful not to conflate the two layers: `superpowers:test-driven-development` and `superpowers:verification-before-completion` assume a codebase with a runnable test suite. This repo has none — the artifacts are Markdown instruction files. Apply their *spirit* (verify before claiming completion, use the skill's own validation checklist) rather than looking for tests to run.

The plugin also ships hooks that fire at session start. If its workflow conflicts with a stored skill's own mandated process — `ai_news_individual`'s six-step 铁律, `taste-skill`'s §14 pre-flight — the stored skill's process wins for that task, since it is the deliverable being executed.

## Git

Single `main` branch tracking `origin/main` at `git@github.com:azxctor/hymeta-skills.git`. **The repository is public.** Commit messages are Chinese. `ai_news_individual/config.example.env` intentionally contains a real DingTalk client ID and recipient user ID with only the secret placeholdered — that was a deliberate call, not an oversight.
