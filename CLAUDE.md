# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A collection of **Agent Skills** — prompt/instruction packages, not an application. There is no build, no test suite, no linter, no package manifest. Each top-level directory is one self-contained skill that gets copied or symlinked into an agent's skills directory (e.g. `~/.claude/skills/`, or `.agents/skills/` for OpenAI-style hosts).

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

`SKILL.md` frontmatter carries `name` and `description` (optionally `license`). The `description` is the routing signal — it must state both *what* the skill does and *when to trigger it*, including the natural-language phrasings (Chinese and English) a user would actually type. Several descriptions here deliberately list trigger phrases; preserve that when editing.

**Progressive disclosure is the core pattern.** `SKILL.md` stays short and tells the agent to read a specific `references/*.md` at a specific step ("**必须先阅读 `references/html-template-guide.md`**"). Heavy detail belongs in `references/`, never inlined into `SKILL.md`. When adding detail to a skill, extend or add a reference file and point to it from the workflow step that needs it.

`agents/openai.yaml` is a parallel manifest for OpenAI-style hosts — `interface.display_name`, `short_description`, `default_prompt` (uses `$skill-name` invocation syntax), `brand_color`, and `policy.allow_implicit_invocation`. Only `a-share-high-dividend-screen` and `image2-blue-tech-infographic` ship one; it is optional and does not affect Claude Code.

## The skills

| Directory | Domain |
| --- | --- |
| `a-share-high-dividend-screen/` | A股高股息量化筛选 — the only skill with executable code |
| `frontend-design/` | General production-grade frontend: components, pages, apps |
| `taste-skill/` | Landing pages / portfolios / redesigns only (declares `name: design-taste-frontend`) |
| `image2-blue-tech-infographic/` | Prompt generation for blue-white Chinese technical infographics |
| `tech-tutorial-builder/` | Interactive HTML tutorial + examples + runnable project, zipped |

### Two frontend skills — pick deliberately

`frontend-design` and `taste-skill` overlap and are both anti-"AI slop". They are not interchangeable: `taste-skill` scopes itself explicitly to landing pages, portfolios, and redesigns and declares dashboards, data tables, and multi-step product UI **out of scope** (§13). Route anything app-like to `frontend-design`. When editing either, check the other for a contradicting rule.

`taste-skill` is ~1200 lines organized as numbered sections (§0 brief inference → §14 pre-flight check) plus appendices. Its rules are explicitly contextual — "None of it fires automatically" — so new rules must state their trigger condition, not read as unconditional law.

## Running the A-share script

**This script cannot run from this repository.** `find_project_root()` walks up from the current working directory looking for `utils/tushare_config.py` and raises if absent — it must be executed from inside a `cbqpt` checkout, which supplies the TuShare client. Requires `pandas`, `numpy`, `requests`, `akshare`.

```bash
# from the cbqpt repo root, not from here
python3 .agents/skills/a-share-high-dividend-screen/scripts/screen_a_share_high_dividend.py

# pin the snapshot date and reweight the composite score
python3 .../screen_a_share_high_dividend.py --trade-date 20260703 \
  --weight-pe-value 0.40 --weight-dividend 0.30 --weight-roe 0.20 \
  --weight-market-cap 0.05 --weight-gross-margin 0.05

# dry run — suppress the DingTalk push
python3 .../screen_a_share_high_dividend.py --no-notify-dingding
```

Use `--no-notify-dingding` for any test or manual run. DingTalk credentials resolve **environment variable first** (`DINGTALK_CLIENT_ID` / `DINGTALK_CLIENT_SECRET` / `DINGTALK_AGENT_ID`), with `分析配置.json` in the *cbqpt* repo as fallback — that config file is committed there, so the secret must stay empty in it. The push is a 工作通知 via an enterprise internal app robot, not a webhook robot; address-book scopes are not granted, so `userid_list` cannot be discovered programmatically and is configured by hand.

If the skill's documented behavior changes, `SKILL.md` and the script's `parse_args()` defaults must be updated together — the SKILL.md scoring formula, hard filters, and output filenames all mirror script constants.

## Conventions when adding or editing a skill

- Directory name should equal frontmatter `name`. Four of five follow this; `taste-skill/` declares `design-taste-frontend` and does not. Claude Code resolves skills by directory name, so match the directory when creating anything new.
- Match the existing file's language. `tech-tutorial-builder` is Chinese throughout; `a-share-high-dividend-screen` is English prose about Chinese-labeled data with Chinese column names (`综合分`, `10年PE历史分位`) kept verbatim — those strings are contracts with the CSV output, don't translate them.
- Skills that produce artifacts end with an explicit verification step listing what to check before claiming completion (see `a-share-high-dividend-screen` §Validation Checklist, `tech-tutorial-builder` 步骤 4). Keep that shape for new artifact-producing skills.
- `frontend-design/SKILL.md` frontmatter points at `LICENSE.txt`, which is not present in the repo.

## Git

Single `main` branch tracking `origin/main` at `git@github.com:azxctor/hymeta-skills.git`. Commit messages in this repo are Chinese.
