# 交互式 HTML 教程模板指南

本文件定义 `index.html` 的完整规范。HTML 自包含（除 highlight.js 走 CDN 外无外部依赖），浏览器打开即用。

## 目录
1. 整体结构
2. CSS 设计系统（含可直接套用的完整样式）
3. 各组成部分的 HTML 骨架
4. 知识点章节的固定节奏
5. SVG 图示规范
6. 内联 JS（复制、测验、滚动监听）
7. 分批写入策略

---

## 1. 整体结构

```
<!DOCTYPE html>
<html lang="zh-CN">
<head> ... <style>设计系统</style> </head>
<body>
  <button class="menu-toggle">☰</button>          移动端菜单按钮
  <div class="progress-bar"><div class="progress-fill"></div></div>   顶部进度条
  <nav class="sidebar"> 自绘SVG logo + 章节导航 </nav>
  <main class="main">
    <div class="hero"> ... </div>                  Hero 区
    <section id="overview"> 00 总览 </section>
    <section id="..."> 01..N 知识点章节 </section>
    <section id="project"> 最后 实战章节 </section>
  </main>
  <script> highlight.js + 内联JS </script>
</body>
</html>
```

---

## 2. CSS 设计系统

用 CSS 变量定义主题色，**换技术栈时只改 `:root` 里的主色变量**即可。下面是完整可套用的样式（把 `--accent` 系列换成目标技术栈的官方色）。

```css
:root {
  --bg: #0d1117;            /* 暗色背景，可按技术栈微调色相 */
  --bg-soft: #131a24;
  --bg-card: #1b2430;
  --accent: #XXXXXX;        /* 技术栈主色，如 Rust橙#dea584 Go青#00add8 Python蓝#4b8bbe TS蓝#3178c6 Node绿#68a063 K8s蓝#326ce5 Vue绿#42b883 React青#61dafb Docker蓝#2496ed */
  --accent-soft: #XXXXXX;   /* 主色调亮一档 */
  --accent-light: #XXXXXX;  /* 主色调更亮 */
  --text: #e6edf3;
  --text-dim: #9aa9b8;
  --text-faint: #6b7888;
  --border: #232d3a;
  --green: #7ee787;         /* 测验正确/成功 */
  --pink: #ff7b9c;          /* 测验错误 */
  --purple: #c39bf0;
  --sidebar-w: 280px;
  --sans: -apple-system, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --display: 'Segoe UI', system-ui, sans-serif;
  --mono: 'SF Mono', 'JetBrains Mono', 'Fira Code', Consolas, monospace;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: var(--sans); line-height: 1.75; font-size: 16px; }

.sidebar { position: fixed; top: 0; left: 0; width: var(--sidebar-w); height: 100vh; background: var(--bg-soft); border-right: 1px solid var(--border); overflow-y: auto; padding: 28px 0; z-index: 100; }
.sidebar-brand { padding: 0 24px 24px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
.sidebar-brand .logo { display: flex; align-items: center; gap: 10px; font-family: var(--display); font-size: 25px; font-weight: 700; color: var(--accent-soft); letter-spacing: -0.5px; }
.sidebar-brand .sub { font-size: 12px; color: var(--text-faint); margin-top: 6px; letter-spacing: 2px; text-transform: uppercase; }
.nav-section { padding: 8px 0; }
.nav-section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-faint); padding: 8px 24px 4px; }
.nav-link { display: flex; align-items: center; gap: 10px; padding: 7px 24px; color: var(--text-dim); text-decoration: none; font-size: 14px; border-left: 2px solid transparent; transition: all 0.15s; }
.nav-link:hover { background: var(--bg-card); color: var(--text); }
.nav-link.active { color: var(--accent-light); border-left-color: var(--accent); background: var(--bg-card); }
.nav-link .num { font-family: var(--mono); font-size: 11px; color: var(--text-faint); min-width: 18px; }

.main { margin-left: var(--sidebar-w); max-width: 860px; padding: 64px 56px 120px; }
.hero { margin-bottom: 64px; }
.hero .eyebrow { color: var(--accent-soft); font-family: var(--mono); font-size: 13px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 16px; }
.hero h1 { font-family: var(--display); font-size: 50px; line-height: 1.1; font-weight: 700; letter-spacing: -1px; margin-bottom: 20px; }
.hero h1 .accent { color: var(--accent-soft); }
.hero p { font-size: 19px; color: var(--text-dim); max-width: 640px; }

section { margin-bottom: 80px; scroll-margin-top: 32px; }
.chapter-tag { display: inline-block; font-family: var(--mono); font-size: 12px; color: var(--accent-light); border: 1px solid var(--accent); border-radius: 4px; padding: 2px 10px; margin-bottom: 16px; letter-spacing: 1px; }
h2 { font-family: var(--display); font-size: 32px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 12px; line-height: 1.2; }
h3 { font-size: 22px; font-weight: 600; margin: 36px 0 12px; color: var(--accent-light); }
h4 { font-size: 17px; font-weight: 600; margin: 24px 0 8px; }
p { margin-bottom: 16px; color: var(--text); }
.lead { font-size: 18px; color: var(--text-dim); margin-bottom: 24px; }
code:not(pre code) { font-family: var(--mono); font-size: 0.88em; background: var(--bg-card); color: var(--accent-light); padding: 2px 6px; border-radius: 4px; }
ul, ol { margin: 0 0 16px 24px; }
li { margin-bottom: 6px; }

.analogy { background: linear-gradient(135deg, rgba(120,120,120,0.1), rgba(120,120,120,0.04)); border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 8px; padding: 20px 24px; margin: 24px 0; }
.analogy .label { font-size: 12px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent-light); font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
.analogy p:last-child { margin-bottom: 0; }

.concept { background: var(--bg-soft); border: 1px solid var(--border); border-radius: 8px; padding: 16px 20px; margin: 20px 0; }
.concept .label { font-size: 12px; letter-spacing: 1px; color: var(--purple); text-transform: uppercase; margin-bottom: 6px; }

.viz { background: var(--bg-soft); border: 1px solid var(--border); border-radius: 8px; padding: 28px; margin: 28px 0; text-align: center; }
.viz svg { max-width: 100%; height: auto; }
.viz-caption { font-size: 13px; color: var(--text-faint); margin-top: 16px; font-style: italic; }

.example { border: 1px solid var(--border); border-radius: 8px; margin: 20px 0; overflow: hidden; }
.example-header { background: var(--bg-soft); padding: 12px 18px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; user-select: none; transition: background 0.15s; }
.example-header:hover { background: var(--bg-card); }
.example-header .title { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 10px; }
.example-header .title .ico { color: var(--accent-soft); }
.example-header .toggle { font-family: var(--mono); font-size: 12px; color: var(--text-faint); transition: transform 0.2s; }
.example.open .example-header .toggle { transform: rotate(90deg); }
.example-body { max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
.example.open .example-body { max-height: 4000px; }

.code-wrap { position: relative; }
pre { margin: 0; overflow-x: auto; background: #090d12 !important; }
pre code { font-family: var(--mono); font-size: 13.5px; line-height: 1.6; padding: 18px 20px !important; display: block; }
.copy-btn { position: absolute; top: 10px; right: 10px; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-dim); font-family: var(--mono); font-size: 11px; padding: 5px 10px; border-radius: 5px; cursor: pointer; opacity: 0; transition: all 0.15s; }
.code-wrap:hover .copy-btn { opacity: 1; }
.copy-btn:hover { background: var(--accent); color: #fff; border-color: var(--accent); }
.copy-btn.copied { background: var(--green); color: #090d12; border-color: var(--green); }

.standalone-code { margin: 20px 0; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.standalone-code .code-label { background: var(--bg-soft); padding: 8px 16px; font-family: var(--mono); font-size: 12px; color: var(--text-faint); border-bottom: 1px solid var(--border); }

.quiz { background: var(--bg-soft); border: 1px solid var(--border); border-radius: 8px; padding: 20px 24px; margin: 24px 0; }
.quiz .q-label { font-size: 12px; letter-spacing: 1px; color: var(--green); text-transform: uppercase; margin-bottom: 10px; }
.quiz .question { font-weight: 600; margin-bottom: 14px; }
.quiz-options { display: flex; flex-direction: column; gap: 8px; }
.quiz-opt { text-align: left; background: var(--bg-card); border: 1px solid var(--border); color: var(--text); padding: 10px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; font-family: var(--mono); transition: all 0.15s; }
.quiz-opt:hover { border-color: var(--accent-soft); }
.quiz-opt.correct { background: rgba(126,231,135,0.15); border-color: var(--green); color: var(--green); }
.quiz-opt.wrong { background: rgba(255,123,156,0.15); border-color: var(--pink); color: var(--pink); }
.quiz-feedback { margin-top: 12px; font-size: 14px; color: var(--text-dim); min-height: 20px; }

.project-step { border-left: 2px solid var(--border); padding-left: 24px; margin: 24px 0; position: relative; }
.project-step::before { content: ''; position: absolute; left: -7px; top: 6px; width: 12px; height: 12px; background: var(--accent); border-radius: 50%; }
.project-step .step-num { font-family: var(--mono); font-size: 12px; color: var(--accent-soft); letter-spacing: 1px; }

.callout { background: rgba(120,120,120,0.08); border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 8px; padding: 14px 20px; margin: 20px 0; font-size: 14.5px; }
.callout .label { color: var(--accent-light); font-weight: 600; font-size: 12px; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }

.cmd-table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }
.cmd-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
.cmd-table td:first-child { font-family: var(--mono); color: var(--accent-light); white-space: nowrap; }
.cmd-table td:last-child { color: var(--text-dim); }

.progress-bar { position: fixed; top: 0; left: var(--sidebar-w); right: 0; height: 3px; background: transparent; z-index: 200; }
.progress-fill { height: 100%; background: var(--accent); width: 0%; transition: width 0.1s; }

@media (max-width: 900px) {
  .sidebar { transform: translateX(-100%); transition: transform 0.3s; }
  .sidebar.show { transform: translateX(0); }
  .main { margin-left: 0; padding: 40px 24px 80px; }
  .progress-bar { left: 0; }
  .hero h1 { font-size: 38px; }
  .menu-toggle { display: flex !important; }
}
.menu-toggle { display: none; position: fixed; top: 16px; right: 16px; z-index: 300; background: var(--accent); color: #fff; border: none; width: 44px; height: 44px; border-radius: 8px; font-size: 20px; cursor: pointer; align-items: center; justify-content: center; }
```

---

## 3. HTML 骨架

### 侧边栏
```html
<nav class="sidebar">
  <div class="sidebar-brand">
    <div class="logo"><!-- 自绘 SVG logo -->Vue 3</div>
    <div class="sub">Interactive Course</div>
  </div>
  <div class="nav-section">
    <div class="nav-section-title">开始</div>
    <a class="nav-link" href="#overview"><span class="num">00</span>框架总览</a>
  </div>
  <div class="nav-section">
    <div class="nav-section-title">核心知识点</div>
    <a class="nav-link" href="#xxx"><span class="num">01</span>章节名</a>
    <!-- ...更多 -->
  </div>
  <div class="nav-section">
    <div class="nav-section-title">实战</div>
    <a class="nav-link" href="#project"><span class="num">NN</span>项目名</a>
  </div>
</nav>
```

### Hero
```html
<div class="hero">
  <div class="eyebrow">// 一句话标语</div>
  <h1>用 <span class="accent">技术栈</span> 做<br>某件事</h1>
  <p>一段引人入胜的介绍，说明这门技术解决什么问题、本教程会带你到哪。</p>
</div>
```

### 总览章节（00）
含：语言哲学/定位的生活化类比、核心优势列表、一张"知识地图"SVG（展示各章节如何串联）、学习建议 callout。

### 实战章节
含：用到的知识点清单（callout）、项目目标、架构 SVG 图、`.project-step` 分步拆解、核心代码（用 `.standalone-code`）、运行方式 callout、结尾祝贺语。

---

## 4. 知识点章节的固定节奏

每个知识点 `<section>` 按此顺序：

```html
<section id="章节id">
  <span class="chapter-tag">CHAPTER 0N</span>
  <h2>章节标题</h2>
  <p class="lead">一句话点题。</p>

  <!-- ① 生活化类比 -->
  <div class="analogy">
    <div class="label">🔧 生活化类比：贴切的日常场景</div>
    <p>用熟悉的事物解释抽象概念，建立直觉。</p>
  </div>

  <!-- ② 概念说明（行文，或用 .concept 块） -->
  <p>正式但简洁的概念解释...</p>

  <!-- ③ SVG 图示（关系/结构/流程类知识点强烈建议） -->
  <h3>可视化：xxx</h3>
  <div class="viz">
    <svg viewBox="0 0 ...">...</svg>
    <div class="viz-caption">图解说明</div>
  </div>

  <!-- ④ 可折叠代码示例 -->
  <div class="example">
    <div class="example-header" onclick="this.parentElement.classList.toggle('open')">
      <span class="title"><span class="ico">▸</span> 示例：xxx</span>
      <span class="toggle">›</span>
    </div>
    <div class="example-body">
      <div class="code-wrap">
        <pre><code class="language-xxx">代码</code></pre>
        <button class="copy-btn" onclick="copyCode(this)">复制</button>
      </div>
    </div>
  </div>

  <!-- ⑤ 交互测验（可选，约半数章节加） -->
  <div class="quiz" data-answer="1">
    <div class="q-label">✓ 检验理解</div>
    <div class="question">问题？</div>
    <div class="quiz-options">
      <button class="quiz-opt" onclick="answerQuiz(this,0)">选项A</button>
      <button class="quiz-opt" onclick="answerQuiz(this,1)">选项B（正确）</button>
      <button class="quiz-opt" onclick="answerQuiz(this,2)">选项C</button>
    </div>
    <div class="quiz-feedback"></div>
  </div>
</section>
```

**代码块中的 HTML 转义**：在 `<pre><code>` 里写代码时，`<` 写成 `&lt;`、`>` 写成 `&gt;`，否则浏览器会当标签解析（JSX/Vue 模板/泛型尤其注意）。

---

## 5. SVG 图示规范

- 用 `viewBox` 适配宽度（如 `0 0 700 330`），`font-family="monospace"`
- 颜色用十六进制直接写（SVG 内不便用 CSS 变量），与主题色协调
- 箭头用 `<marker>` 定义复用
- 适合的图示类型：知识地图（章节关系）、数据流、组件树、架构图、生命周期、状态机、分层结构、网络拓扑
- 图是为了表达**关系/结构/流程**，不要为画而画

箭头 marker 模板：
```html
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
  <path d="M0,0 L6,3 L0,6 Z" fill="#6b7888"/>
</marker></defs>
<!-- 用法：<line x1=.. y1=.. x2=.. y2=.. stroke="#6b7888" marker-end="url(#arrow)"/> -->
```

---

## 6. 内联 JS（放在 body 末尾）

先引入 highlight.js 和需要的语言包，再放功能 JS：

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/<lang>.min.js"></script>
<!-- 按需引入语言包：python javascript typescript xml(含HTML/Vue模板) yaml bash dockerfile rust go json 等 -->
<script>
  hljs.highlightAll();

  function copyCode(btn) {
    const code = btn.parentElement.querySelector('code').innerText;
    navigator.clipboard.writeText(code).then(() => {
      const orig = btn.textContent;
      btn.textContent = '已复制 ✓'; btn.classList.add('copied');
      setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1500);
    });
  }

  function answerQuiz(btn, idx) {
    const quiz = btn.closest('.quiz');
    const answer = parseInt(quiz.dataset.answer);
    const feedback = quiz.querySelector('.quiz-feedback');
    quiz.querySelectorAll('.quiz-opt').forEach(b => b.disabled = true);
    if (idx === answer) {
      btn.classList.add('correct');
      feedback.textContent = '✓ 回答正确！'; feedback.style.color = '#7ee787';
    } else {
      btn.classList.add('wrong');
      quiz.querySelectorAll('.quiz-opt')[answer].classList.add('correct');
      feedback.textContent = '✗ 再想想，正确答案已高亮。'; feedback.style.color = '#ff7b9c';
    }
  }

  const sections = document.querySelectorAll('section');
  const navLinks = document.querySelectorAll('.nav-link');
  const progressFill = document.getElementById('progressFill');
  function onScroll() {
    let current = '';
    sections.forEach(sec => { if (window.scrollY >= sec.offsetTop - 100) current = sec.id; });
    navLinks.forEach(link => link.classList.toggle('active', link.getAttribute('href') === '#' + current));
    const scrolled = window.scrollY / (document.body.scrollHeight - window.innerHeight);
    progressFill.style.width = Math.min(scrolled * 100, 100) + '%';
  }
  window.addEventListener('scroll', onScroll); onScroll();
  navLinks.forEach(link => link.addEventListener('click', () => {
    if (window.innerWidth <= 900) document.querySelector('.sidebar').classList.remove('show');
  }));
</script>
```

注意：highlight.js 没有专门的 Vue/JSX 语言，用 `xml`（模板部分）或 `javascript`/`typescript`。Dockerfile 用 `dockerfile`，compose/k8s 用 `yaml`。

可选增强：在某个知识点放一个真正可交互的 mini demo（用 `.live-demo` 容器 + 几行原生 JS），让学习者直接感受效果（如计数器演示响应式/状态）。

---

## 7. 分批写入策略

HTML 约 1000-1350 行，避免单次 `create_file` 过大：

1. `create_file` 写入：`<!DOCTYPE>` → `<head>`(含完整 `<style>`) → 侧边栏 → Hero → 总览章节(00)，到此为止不闭合 body。
2. `cat >> learn/<栈>/index.html << 'HTMLEOF'` 追加知识点章节 01-05。
3. 再次 `cat >>` 追加知识点章节 06-N。
4. 最后一次 `cat >>` 追加实战章节 + `</main>` + `<script>`(highlight.js + 内联JS) + `</body></html>`。

每次追加后可 `wc -l` 确认行数增长正常。
