---
name: image2-blue-tech-infographic
description: Create image2 prompts for clean blue-white Chinese technical infographics, architecture diagrams, process diagrams, layered models, comparison panels, and knowledge cards matching the user's reference style. Use when the user asks to generate images, diagrams, posters, architecture visuals, or reusable prompts in a blue tech infographic style with Chinese text, bilingual labels, numbered steps, rounded cards, icons, arrows, and structured AI/Agent/MCP/technology content.
---

# Image2 Blue Tech Infographic

Use this skill to produce high-fidelity prompts for image2 that match the reference style: crisp blue-white technical knowledge diagrams with Chinese-first typography, bilingual technical labels, rounded modules, line icons, arrows, and dense but readable architecture layouts.

## Workflow

1. Extract the user's topic, audience, output platform, and required text.
2. Convert the topic into a diagram grammar:
   - layered model
   - multi-step workflow
   - two-column architecture comparison
   - lifecycle pipeline
   - hub-and-spoke protocol architecture
   - bottom relationship chain or summary legend
3. Keep all visible text short and production-ready. Prefer Chinese headings with English terms in parentheses.
4. Generate an image2 prompt using the style guide in [references/style-guide.md](references/style-guide.md).
5. If the user provided exact copy, preserve it. If not, propose concise Chinese labels and ask image2 to render clean, legible text.

## Reference Assets

When image2 supports reference images, attach these assets as style references:

- [assets/agent-security-permission-architecture.png](assets/agent-security-permission-architecture.png)
- [assets/agent-memory-system.png](assets/agent-memory-system.png)
- [assets/function-calling-mcp-architecture.png](assets/function-calling-mcp-architecture.png)

Use them for style, layout density, color, icon treatment, and typography. Do not copy their exact topic content unless the user requests it.

## Output Format

Return a ready-to-use prompt, plus optional negative prompt and size recommendation:

```text
Prompt:
...

Negative prompt:
...

Recommended size:
16:9, 2048x1152 or 2560x1440
```

## Quality Bar

The prompt must explicitly require:

- clean white or very pale blue background
- navy headline, bright blue accents, pale blue panels
- Chinese-first text with optional English terms
- clear hierarchy and enough whitespace
- rounded rectangles, thin blue strokes, simple line icons
- arrows, dashed lines, numbered circles, legends where useful
- no decorative gradients, no stock photo elements, no 3D realism
- all text sharp, non-overlapping, horizontally aligned, and readable
