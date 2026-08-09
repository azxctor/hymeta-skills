# ai_news_individual

QwenPaw Skill package for one-to-one AI news delivery through the hymeta DingTalk robot.

## Files

- `SKILL.md` - QwenPaw skill instructions.
- `get_ai_info.py` - fetches RSS AI news into `temp.json`.
- `get_github_info.py` - fetches GitHub daily trending repositories into `github_temp.json`.
- `send_ai_info.py` - sends `temp.md` through DingTalk robot one-to-one markdown messages.
- `sources.json` - editable RSS source list.
- `config.example.env` - environment variable template.

## Required Environment

Set these in QwenPaw environment variables:

```bash
export DINGTALK_CLIENT_ID="dingazyug2orfmkrd0ul"
export DINGTALK_CLIENT_SECRET="..."
export DINGTALK_ROBOT_CODE="dingazyug2orfmkrd0ul"
export DINGTALK_DEFAULT_USER_IDS='["0160641832681292680"]'
```

`DINGTALK_ROBOT_CODE` is optional in the script; if omitted, it defaults to `DINGTALK_CLIENT_ID`.
`DINGTALK_DEFAULT_USER_IDS` is optional; if omitted, the script defaults to `["0160641832681292680"]`.

## Manual Smoke Test

```bash
python3 get_ai_info.py
python3 get_github_info.py
python3 -c "import json; print(len(json.load(open('temp.json')))); print(len(json.load(open('github_temp.json'))))"
python3 send_ai_info.py --dry-run
```

Remove `--dry-run` only after `temp.md` has been reviewed and the target user IDs are correct.

## Notes

- This package does not call Yuque.
- The DingTalk Client Secret must stay in environment variables only.
- The sender uses `sampleMarkdown` through `POST /v1.0/robot/oToMessages/batchSend`.
- If a local Python install has broken CA certificates, use `AI_NEWS_INSECURE_SSL=1`
  or `GITHUB_INSECURE_SSL=1` only for fetch debugging. Do not use
  `DINGTALK_INSECURE_SSL=1` unless you are deliberately testing in a trusted
  network.
