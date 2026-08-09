# 验证、打包与交付

## 验证策略

不同技术栈用不同验证方式（详见 `stack-conventions.md` 末尾的小结表）。原则：**能实跑就实跑，跑不了就如实说明并人工审校**。

### 沙箱环境常见情况
- Node.js / npm / npx / tsc 通常可用 → 前端框架、TypeScript、Node 可实际构建/运行
- python3 / pip 通常可用（用 `pip install --break-system-packages`）→ Python 可实跑
- rustc / go / helm / docker daemon 往往**不可用**，且网络白名单受限装不上 → 人工审校或写轻量校验脚本
- 网络白名单一般含 npmjs/pypi/github 等，可 `npm install` / `pip install`，但 helm.sh 等不在内

### 各类验证手段
- **运行/编译**：`python3 file.py`、`npx tsc --strict`、`node --check`、`npx vite build`
- **前端 SFC/JSX 编译**：装 `@vue/compiler-sfc` 或 `@babel/preset-react`，逐文件编译
- **YAML 语法**：`python3 -c "import yaml; list(yaml.safe_load_all(open('x.yaml')))"`
- **Helm 渲染**：缺 helm 时写 Python 脚本模拟 `{{ .Values.x }}` 替换和 `{{- if }}` 块，校验渲染后是合法 YAML
- **人工审校**：检查关键指令/语法结构存在且正确

### 验证时的注意点
- 验证用的临时文件、依赖、构建产物**都要在打包前清理**
- 装依赖跑构建后，记得 `rm -rf node_modules dist`
- 发现并修复的问题要在最终报告里如实提及

---

## 打包与交付流程

### 沙箱无法写用户本地路径
Claude 运行在隔离沙箱，**无法直接写入用户本地文件系统**（如 macOS 的 `/Users/...`）。因此采用：生成在沙箱 → 打包 zip → 通过 `present_files` 交付 → 用户下载后解压到目标路径。

### 累积式合集
维护一个 `learn/` 目录容纳所有已生成的技术栈，打包成单个 `learn_tutorials.zip`。每新增一个技术栈就更新这个合集，用户最终得到包含全部已学技术栈的一个 zip。

### 每完成一个技术栈的收尾步骤

```bash
# 1. 清理所有构建产物与缓存
cd /home/claude   # 或 learn/ 的父目录
find learn -type d -name node_modules -exec rm -rf {} + 2>/dev/null
find learn -type d -name dist -exec rm -rf {} + 2>/dev/null
find learn -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find learn -name "*.pyc" -delete 2>/dev/null
find learn -name "package-lock.json" -delete 2>/dev/null

# 2. 更新顶层 learn/README.md（见下方格式）

# 3. 重新打包
rm -f learn_tutorials.zip
zip -r -q learn_tutorials.zip learn

# 4. 复制到输出目录（用户能看到的地方）
cp learn_tutorials.zip /mnt/user-data/outputs/
```

然后用 `present_files` 交付 `learn_tutorials.zip`（可同时附上本次新增的 `index.html` 让用户预览）。

### 顶层 learn/README.md 格式

```markdown
# 技术栈交互式教程合集

按技术栈分类的交互式 HTML 教程 + 配套代码示例 + 实战项目。

## 已完成的技术栈

| 技术栈 | 教程 | 知识点示例 | 实战项目 |
|--------|------|-----------|----------|
| **Rust** | `rust/index.html` | 9 个 (`.rs`) | 异步命令行 Todo 管理器 |
| ... |

## 目录结构
（展示 learn/<栈>/index.html + examples/ + project/ 的树）

## 如何使用
- 看教程：浏览器打开任意 <技术栈>/index.html
- 跑示例：进 examples/，每个文件头注释有运行方式
- 跑实战：进 project/，按其 README.md 操作

## 教学设计理念
每个知识点遵循「生活化类比 → 概念说明 → SVG 图示 → 代码示例 → 交互练习」。
```

### 交付时的报告

向用户清晰报告：
- 本次完成的技术栈，教程行数、示例数、项目文件数
- 每部分的验证情况（如实说明哪些实跑通过、哪些人工审校、有何环境限制）
- 下载后保存到本地的命令，例如：

```bash
mv ~/Downloads/learn_tutorials.zip <用户的目标路径>/
cd <用户的目标路径>
unzip learn_tutorials.zip
# 浏览器打开 learn/<技术栈>/index.html 即可学习
```

- 当前进度（已完成 N 个，还剩哪些），并询问是否继续下一个
