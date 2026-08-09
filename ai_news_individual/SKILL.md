---
name: ai_news_individual
description: AI 资讯每日个人定向推送 - 抓取 AI 行业资讯和 GitHub 热榜，生成固定模板日报，并通过 hymeta 钉钉机器人单聊推送给指定用户。
metadata:
  qwenpaw:
    emoji: "🗞️"
    requires:
      env:
        - DINGTALK_CLIENT_ID
        - DINGTALK_CLIENT_SECRET
---

# 🚀 AI 行业速递 | 个人定向推送 Skill

当用户要求“发送 AI 行业速递”“给某些 userId 推送 AI 新闻”“每日 AI 资讯单聊推送”时使用本 Skill。

## 🚀 执行流程（严格按顺序）

必须先进入当前 Skill 目录。默认路径如下；如果 QwenPaw 安装在其他 workspace，请使用实际路径。

```bash
cd "${QWENPAW_WORKING_DIR:-$HOME/.qwenpaw}/workspaces/default/skills/ai_news_individual/"
```

### Step 1: 准备
1. **解析用户 ID**：从用户指令提取 `userIdList`；若用户未指定，默认使用 `["0160641832681292680"]`（黄翌）。
2. **确认钉钉环境变量**：
   - `DINGTALK_CLIENT_ID`：hymeta 应用的 Client ID，例如 `dingazyug2orfmkrd0ul`。
   - `DINGTALK_CLIENT_SECRET`：hymeta 应用的 Client Secret，只能从环境变量读取，禁止写入报告或代码。
   - `DINGTALK_ROBOT_CODE`：可选；hymeta 机器人的 RobotCode。若未设置，发送脚本默认使用 `DINGTALK_CLIENT_ID`。
3. 进入目录执行后续步骤。

### Step 2: 获取数据
```bash
python3 get_ai_info.py        # 输出 temp.json
python3 get_github_info.py    # 输出 github_temp.json (超时设为 ≥400s)
```

**校验**：运行下方脚本，`temp.json` 为空则终止。
```bash
python3 -c "import json,os; ai=json.load(open('temp.json')); print(f'AI资讯:{len(ai)}条'); gh=json.load(open('github_temp.json')) if os.path.exists('github_temp.json') else []; print(f'GitHub:{len(gh)}条')"
```

### Step 3: 筛选数据（优先级漏斗）
使用 `python3 -c` 读取 JSON（**禁止** `read_file`）。

**筛选规则（满 5 条即停）：**
1. **P0 巨头动向**：OpenAI/Anthropic/阿里/腾讯等发布新模型或重大更新（必选 1-2 条）。
2. **P1 研发效能**：Cursor/Claude Code/IDE 等编程工具新能力（必选 1-2 条）。
3. **P2 落地应用**：有实际场景的产品/技术，**过滤**无落地融资/股价/人事（补齐至 5 条）。

### Step 4: 生成报告（填空模式）
⚠️ **核心铁律：你只是个填空机器！严禁修改模板骨架！**

**操作**：只能将下方 `{xxx}` 替换为实际内容。**不得增删任何字符、换行、Emoji 或标题。**

```markdown
# 🗞️ AI 行业速递 | {month} 月 {day} 日
> 聚焦今日核心动态，一分钟掌握 AI 行业风向。

---

### 📈 今日 AI 焦点
- **{company_1}**：{summary_1} [点击查看]({url_1})
- **{company_2}**：{summary_2} [点击查看]({url_2})
- **{company_3}**：{summary_3} [点击查看]({url_3})
- **{company_4}**：{summary_4} [点击查看]({url_4})
- **{company_5}**：{summary_5} [点击查看]({url_5})

---

### 🔥 GitHub 热榜
> (若无数据则整段删除，有数据则输出 3 条)
- **{repo_1}** ⭐{stars_1} (今日+{stars_today_1})：{advantage_1}。🎯 适合：{scenario_1}。 [点击查看]({link_1})
- **{repo_2}** ⭐{stars_2} (今日+{stars_today_2})：{advantage_2}。🎯 适合：{scenario_2}。 [点击查看]({link_2})
- **{repo_3}** ⭐{stars_3} (今日+{stars_today_3})：{advantage_3}。🎯 适合：{scenario_3}。 [点击查看]({link_3})

---

### 💡 极简洞察
> 🔬 **技术风向**：{tech_trend} (20字内)

> 💰 **商业嗅觉**：{business_trend} (20字内)
```

**填写注意：**
- `{repo}`：仅仓库名，不含 `owner/`。
- `{url}` / `{link}`：100% 原样复制 JSON 中的链接，**严禁修改/伪造**。
- `{summary}`：每条 30 字内，内容必须精简。
- `GitHub 热榜`：若 `github_temp.json` 为空，删除整段 GitHub 热榜。

### Step 5: 保存与检查
1. **写入文件**：使用 QwenPaw 的文件写入工具将填充后的内容写入当前目录的 `temp.md`。
2. **强制校验**：
   ```bash
   ls -la temp.md && wc -c temp.md
   ```
   文件必须存在且 `>800 bytes`，否则终止报错。

### Step 6: 发送到个人
```bash
python3 send_ai_info.py
```

若用户明确指定其他收件人，则覆盖默认值：

```bash
python3 send_ai_info.py --userIdList '["提取的ID"]'
```

发送脚本使用 hymeta 钉钉机器人 OpenAPI 单聊直推：

- 获取 token：`POST https://api.dingtalk.com/v1.0/oauth2/accessToken`
- 发送消息：`POST https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend`
- 消息类型：`sampleMarkdown`

发送完成后检查 `send_result.json`，确认无 `invalidStaffIdList` 和 `flowControlledStaffIdList`。

## 🚫 绝对红线
1. **禁止自创排版**：模板里的 `#`、`###`、`---`、Emoji 一个都不能改，只能填空。
2. **禁止泄露密钥**：不得把 `DINGTALK_CLIENT_SECRET` 写入 `SKILL.md`、`temp.md`、日志或聊天回复。
3. **禁止绕过脚本**：只能用 `send_ai_info.py` 发送，不能用 `curl` 或手写请求临时发送。
4. **禁止语雀归档**：本 Skill 只做个人单聊推送，不调用语雀接口。
5. **禁止跳步**：必须走完 Step 1 → 2 → 3 → 4 → 5 → 6。
