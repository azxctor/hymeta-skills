# Blue Tech Infographic Style Guide

## Visual DNA

Create a clean Chinese technology explainer graphic, like a SaaS architecture whitepaper converted into a polished infographic.

- Canvas: wide 16:9, preferably 2048x1152 or 2560x1440.
- Background: white `#FFFFFF` or very pale blue `#F4F8FF`.
- Main navy: `#0B2A66` for title and primary text.
- Accent blue: `#1266D6` or `#1E6BE3` for icons, numbers, arrows, and active blocks.
- Light panel fill: `#EEF6FF`, `#F6FAFF`, `#EAF3FF`.
- Border: thin blue `#8DBBFF` or `#B9D5FF`.
- Optional positive green: `#168A4A` for low-risk/success/server elements.
- Optional warning red: `#E11D1D` for "Yes", risk, or required approval paths.
- Avoid purple, orange, beige, dark backgrounds, noisy texture, photo backgrounds, shadows, and 3D render style.

## Typography

- Chinese-first. Use English in parentheses for key technical terms.
- Title: large, bold, navy, centered or panel-header aligned.
- Subtitle: smaller gray-blue `#52627A`.
- Body: black or near-navy, high contrast.
- Labels: short phrases, not paragraphs.
- Preserve exact user-provided Chinese terms. If inventing labels, keep them compact.
- Ask image2 for crisp, correctly spelled, non-overlapping Chinese and English text.

## Layout Patterns

### Pattern A: Layered Defense / Concentric Model

Use for security, permissions, governance, system layers, capability maturity.

- Left or center: large concentric circles in pale-to-medium blue.
- Core: solid bright blue circle with white icon and label.
- Outer layers: numbered circles `1`, `2`, `3`, short title and English translation.
- Side annotations: line icons with dotted connector lines.
- Right side: optional approval or decision flow in a bordered panel.
- Bottom: legend bar with 4-6 compact icon+label items.

### Pattern B: Three-Layer System

Use for memory systems, storage tiers, model stacks, product architecture.

- Top-to-bottom stacked horizontal rounded cards.
- Each card contains: left icon, numbered blue circle, Chinese layer name, English term, short explanation.
- Use vertical arrows for compression, retrieval, transformation, or feedback.
- Right side: dashed vertical lifecycle panel with 4-5 steps.
- Keep cards wide, calm, and evenly spaced.

### Pattern C: Dual Architecture / Flow Comparison

Use for protocols, tools, integration models, workflows, agent architecture.

- Two main panels side by side, each with a pale header strip.
- Left panel: numbered step workflow, vertically stacked cards connected by arrows.
- Right panel: architecture graph with host/client/server nodes and directional arrows.
- Include a dashed insight box for key efficiency or comparison message.
- Bottom: relationship chain with three large icon cards connected by arrows.

## Icon Style

- Use simple vector-like line icons, flat blue, consistent stroke width.
- Icons should be functional: shield, lock, database, notebook, eye, brain, magnifier, clipboard, gear, code file, monitor, link, server, graduation cap.
- No mascot, cartoon, photo-realistic object, sticker style, or skeuomorphic rendering.

## Prompt Template

Replace bracketed fields before use.

```text
Create a polished blue-white Chinese technical infographic in the same visual style as the provided reference images: clean SaaS architecture diagram, white/pale-blue background, navy headline, bright blue accents, rounded rectangles, thin blue borders, flat vector line icons, numbered blue circles, arrows and dashed connectors, crisp readable Chinese text with English terms in parentheses.

Topic: [TOPIC]
Main title: [TITLE]
Subtitle: [SUBTITLE or omit]

Layout: [choose Pattern A / Pattern B / Pattern C, then describe exact sections]

Content:
[Write the exact headings, labels, and short explanations. Keep each label concise.]

Design requirements:
- 16:9 wide canvas, high resolution, lots of whitespace.
- Color palette: navy #0B2A66, accent blue #1266D6, pale blue panels #EEF6FF and #F6FAFF, thin borders #8DBBFF.
- Chinese-first typography, English technical terms in parentheses where useful.
- Use simple blue vector icons that match the meaning of each module.
- Ensure all text is sharp, correctly spelled, horizontally aligned, non-overlapping, and fully inside its container.
- Keep the style professional, minimal, educational, and diagrammatic.
```

## Negative Prompt

```text
No photo background, no people, no 3D render, no heavy shadows, no glassmorphism, no neon cyberpunk, no dark theme, no complex gradients, no purple/orange dominant palette, no decorative blobs, no clutter, no illegible text, no distorted Chinese characters, no overlapping labels, no random English filler, no cartoon mascot.
```

## Example Prompt

```text
Create a polished blue-white Chinese technical infographic in the same visual style as the provided reference images: clean SaaS architecture diagram, white/pale-blue background, navy headline, bright blue accents, rounded rectangles, thin blue borders, flat vector line icons, numbered blue circles, arrows and dashed connectors, crisp readable Chinese text with English terms in parentheses.

Topic: Agent Context Engineering
Main title: Agent Context Engineering 架构
Subtitle: 从输入治理到长期记忆的上下文管理闭环

Layout: Pattern C dual architecture. Left panel title "上下文处理四步流程", showing four vertical rounded cards connected by blue arrows. Right panel title "上下文资产架构", showing Host, Context Router, Memory Store, Tool Registry, Knowledge Base, and Output Evaluator nodes connected by arrows. Add a dashed insight box explaining "减少无效上下文，提高推理稳定性". Bottom legend bar: "输入过滤 -> 上下文压缩 -> 记忆检索 -> 工具调用 -> 输出评估".

Content:
1 定义任务边界 (Task Boundary): 明确目标、约束与输出格式
2 压缩上下文 (Context Compression): 提取关键信息，降低 token 噪声
3 检索记忆 (Memory Retrieval): 调用项目知识、历史决策与偏好
4 执行与评估 (Execute & Evaluate): 工具调用后检查结果质量

Design requirements:
- 16:9 wide canvas, high resolution, lots of whitespace.
- Color palette: navy #0B2A66, accent blue #1266D6, pale blue panels #EEF6FF and #F6FAFF, thin borders #8DBBFF.
- Chinese-first typography, English technical terms in parentheses where useful.
- Use simple blue vector icons that match the meaning of each module.
- Ensure all text is sharp, correctly spelled, horizontally aligned, non-overlapping, and fully inside its container.
- Keep the style professional, minimal, educational, and diagrammatic.
```
