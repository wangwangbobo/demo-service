# knowledge-html-viewer

把代码讲解、功能原理、知识点写成**图文并茂**的单页 HTML。每篇产出强制内嵌 4–10 张 AI 文生图生成的原理配图，配合"四段式"中文讲解（背景 → 引出 → 配图 → 要点/代码/取舍），自带侧边目录、Prism.js 代码高亮、浅色/暗色主题切换。

> 这是一个 **agent skill**——`SKILL.md` + 配套脚本/模板的目录包，给 AI 编码助手（Claude Code、Cursor、QoderWork 等）加载用。Agent 读 `SKILL.md`，按 5 步工作流跑：收集素材 → 生成配图 → 写 Markdown → 脚本转 HTML → 浏览器验证。

## 它能做什么

你跟 agent 说"写个 HTML 讲讲长期记忆的实现原理"，agent 会：

1. 读相关源码和文档，提炼出 4–10 个"必须配图"的原理点（整体架构、关键流程、状态机、对比关系、一图概括等）。
2. 并发提交文生图任务（OpenAI `gpt-image-1` / Google Imagen / Stable Diffusion / 本地 ComfyUI / 任意 MCP 文生图工具——你接哪个用哪个）。
3. 轮询取回图片 URL，按"四段式"模板写到 Markdown 里。
4. 跑 `scripts/generate_html.py` 把 Markdown 转成带 TOC、代码高亮、主题切换的单文件 HTML。
5. `open` 打开浏览器自检。

`SKILL.md` 里设了几条硬规则避免输出走样：

- **禁止纯文字 HTML**——skill 一被触发，配图就是强制的（除非用户当次明确说"不要图"）。
- **禁止图多文少**——每张图周围必须 ≥ 250 字中文讲解，全文中文字数 ≥ `图片张数 × 300`。
- **禁止 ASCII 字符画代替真图**——`+----+` / `──>` / `│ │` 一律不算配图。
- **限流不能简化 prompt**——质量优先，宁可 sleep 重试也不降级 prompt。

这几条是作者自己写过几十篇内部图解攒下来的"反 PPT 化"纪律，外部用户嫌严可以自行松绑。

## 安装

把目录拷进 agent 的 skills 文件夹：

```bash
# Claude Code / Anthropic 系
cp -r knowledge-html-viewer ~/.agents/skills/

# 或任意读 SKILL.md 的 skill 加载器
```

Agent 会通过 `SKILL.md` 顶部的 `description` 字段自动发现。

## 目录结构

```
knowledge-html-viewer/
├── SKILL.md                          # 给 agent 看的操作手册（中文）
├── README.md                         # 本文件
├── LICENSE                           # Apache 2.0
├── scripts/
│   ├── generate_html.py              # Markdown → 单文件 HTML 转换器
│   └── batch_generate.py             # 批量包装器
└── templates/
    ├── base_template.html            # CSS + JS + 布局（浅/暗主题）
    └── example_config.json           # 批量模式示例配置
```

## 不用 agent 也能跑

如果你已经手写了带图片 URL 的 Markdown，转换脚本可以独立用：

```bash
python3 scripts/generate_html.py \
  --title "我的页面" \
  --content path/to/input.md \
  --output path/to/output.html \
  --theme dark \
  --toc true
```

参数：

- `--title`：页面标题（支持中文）。
- `--content`：Markdown 文件路径，或直接传 Markdown 字符串。
- `--output`：输出 HTML 路径。
- `--theme`：`light` 或 `dark`。
- `--toc`：`true` / `false`，是否渲染侧边目录。

脚本纯 Python 标准库实现，要求 Python ≥ 3.8，**不用 `pip install`**。

## 文生图 provider 任选

`SKILL.md` 在文生图这一步刻意做了 **provider-agnostic**——接哪个都行：

| Provider | 模式 | 备注 |
|---|---|---|
| OpenAI `gpt-image-1` / DALL·E 3 | 同步 | 一次调用直接返回 URL |
| Google Imagen（Vertex AI） | 异步 | 建任务 + 轮询状态 |
| Stability AI / SD API | 同步 + 异步 | 两种模式都有 |
| 本地 ComfyUI / SD-WebUI | 自建 | 无 quota 顾虑 |
| MCP 文生图工具 | 视实现而定 | agent 会调对应的 `*_generate` + `*_get_status` 配对 |

`SKILL.md` 里的 prompt 模板（Notion 风格信息图、柔和色调、扁平 2D）对各家 provider 出图都比较稳定。

## 为什么固定输出到 `~/Desktop/html/`

`SKILL.md` 把所有产出都强制写到 `~/Desktop/html/`。理由是运维性的——所有图解集中在一个文件夹方便 grep 旧文章、互相引用。换成任意目录都行，重点是**每次都用同一个目录**。

## License

Apache License 2.0。详见 `LICENSE`。

## 一点说明

skill 格式参考了 Anthropic 在 Claude Code 里推的"agent skill"约定。**4–10 张配图下限**、**字数 ≥ 图数 × 300**、**四段式章节模板**这些数字是作者自己的偏好，针对"原理/架构/状态机"类讲解调出来的；轻量教程或快速上手类可以适当放宽，但建议改之前先想清楚为什么。
