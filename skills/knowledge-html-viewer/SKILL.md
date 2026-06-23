---
name: knowledge-html-viewer
description: "生成美观的功能讲解、原理介绍、知识点 HTML 页面，内嵌 AI 文生图模型生成的原理配图。⭐ **仅当用户明确出现以下任一信号词时才触发**（因为生图成本较高，非显式请求不走此流程）：
✅ **触发信号词**：'HTML'、'html 页面'、'可视化讲解'、'图解'、'图文并茂'、'配图讲'、'原理图'、'示意图'、'流程图'、'架构图'、'知识点页面'、'讲解文档/页面'。具体例句：'写个 HTML 讲讲 xxx'、'帮我可视化讲解 xxx'、'给 xxx 配几张原理图'、'把文档做成 HTML'、'做个图文页面'。
❌ **不要触发**：用户只说'讲讲 xxx'、'介绍一下 xxx'、'xxx 是什么'、'xxx 的原理'、'给我说说 xxx'等普通问答需求时，走纯文字回答，不要调用此 skill。只有用户明确想要'页面/文档/图解'形式的产出时才触发。"
---

# 知识库 HTML 可视化生成器

将项目知识点、功能原理、代码讲解转换为**图文并茂**的 HTML 页面。**每份产出必须内嵌 AI 文生图生成的原理配图**（**至少 4 张，最多 10 张**，按"原理点 1:1 配图"原则——**凡是适合配图、或者配图能更清楚解释的地方一律必须配图**，不要为了控量而省图，也不要机械凑数）。纯文字 HTML 一律视为不合格。

⚠️ **重点提醒**：本 skill 重点是**讲解**，配图只是辅助。**每张图周围必须有 ≥ 250 字中文讲解**（背景动机 + 引出句 + 3~6 条带字段名的要点 + 代码/取舍），**全文中文字数 ≥ 图片张数 × 300**。详见下面 Gotchas 第 10 条「禁止图多文少」。

## ⭕ 触发门槛（成本控制）

本 skill 会调用 AI 文生图模型，**成本较高**，必须满足以下任一才能启动：

1. 用户消息中出现显式信号词：**HTML**、**可视化**、**图解**、**图文并茂**、**配图/原理图/示意图**、**页面/文档形式产出**
2. 用户明确要求生成文件或页面（而不是只要文本回答）

❌ **严禁触发的场景**：
- 用户只说「讲讲 xxx」「介绍一下 xxx」「xxx 是什么」「xxx 的原理是什么」「给我说说 xxx」 → 走**普通文本回答**，不调用本 skill
- 用户仅请求概念解释、代码阅读、问答（无页面/文档诉求）
- 不确定时 → 先问用户「需要生成 HTML 页面（带 GPT Image 2 配图）还是文本回答就够了？」，不要默认启动生图流程

## Gotchas（硬规则，不可违反）

1. **禁止手写 HTML**。用 `create_file` 直接创建 `.html` 会导致代码块 `white-space: pre` 丢失、缩进消失、格式全部错乱。必须走「先写 `.md` → 脚本转换」的路径。
2. **禁止跳过 Markdown 步骤**。即使内容很简单，也必须先写 `.md` 再调脚本转换。
3. **禁止用 `<span>` 做代码高亮**。脚本和模板已内置 Prism.js 高亮。
4. **🚫 禁止交付纯文字 HTML**。一旦 skill 被触发，配图就是**强制**步骤，不是可选项。必须主动出 **4~10 张**原理图，**按原理点 1:1 覆盖**：每一个值得解释的原理/流程/对比/结构/总览都要有自己的图，不要把多个原理点合并成一张图省事，也不要因为"已经够 4 张了"就放弃后续配图。只有用户在本次请求里明确说"不要图"时才跳过。
5. **🚫 禁止用 ASCII 字符画/框图代替真正的图片**。`+----+`、`──>`、`│ │` 这种字符拼出来的"图"一律不算配图，必须改用文生图模型出真图。尤其是"一图概括/总览/全景图/Cheat Sheet"这种章节，**最该配图、最不能用字符画糊弄**。
6. **配图覆盖率自检**：写完 .md 后逐章扫一遍——**只要某章节有"流程/结构/对比/分层/状态机/时序/总览"性质的原理讲解，就必须有对应配图**。发现遗漏立刻回 Step 2 补图，不要带着裸文字章节进 Step 4。
7. **⚠️ 异步文生图：建任务 ≠ 拿到图片 URL**：大多数文生图 API（OpenAI gpt-image-1、Google Imagen、Stable Diffusion 等）的异步流程是"`generate` 建任务返回 `job_id` → `get_status` 轮询拿 `image_url`"两步。具体工具/接口名以你接入的 provider 文档为准。同一 provider 通常会有多个看起来都像的查询接口，**只有官方文档指定的那个**才能真正拿到最终 URL，其他接口可能只返回任务元数据或报"生图记录未完成生成"。
8. **生图失败必须分清原因再处理，质量优先**：任务状态为"失败"时先看返回的 message：
   - **限流类**（message 含"限流"、"rate limit"、"too many requests"、"模型提供方限流"、"QPS"、"频率" 等）→ **绝对不要简化 prompt**！原 prompt 是为了画质设计的，简化会牺牲质量。正确做法：`sleep 30s`（必要时 60s）后**用原 prompt 重新建任务**，失败继续等更久，循环到出图为止。质量第一，宁可多等也不降级 prompt。
   - **数据格式错误类**（message 含"图片生成接口返回数据格式错误"、"格式" 等）→ 这才是 prompt 本身的问题，立即缩短 prompt、减少复杂视觉描述、去掉特殊符号，重新建任务。
   - **其他未知错误** → 先 sleep 30s 用原 prompt 重试一次；连续 2 次同类失败再考虑简化。
   - 通用原则：**失败不等于放弃配图，继续重试直到成功**；但简化 prompt 是最后手段，不能作为限流的应对方式。
9. **📂 输出路径强制约束**：所有生成的 `.md` 和 `.html` 文件**必须**保存到 `~/Desktop/html/` 目录下（即桌面的 `html` 文件夹）。禁止写到当前工作目录、项目目录或其他位置。若目录不存在，先 `mkdir -p ~/Desktop/html` 再写入。
10. **🚫 禁止图多文少（图文失衡红线）**：本 skill 名字叫"知识库 HTML 可视化讲解"，重点是**讲解**，配图只是辅助。**每张图必须配足够的文字说明**，否则页面会变成"看图猜原理"的 PPT，失去技术讲解价值。硬性要求：
    - **每张图周围至少 250 字中文讲解**（图前 1 段引出 + 图后 3~6 条要点列表 + 必要的代码/字段对照），不达标算失衡。
    - **每张图必须有 figcaption 之外的正文说明**：脚本会把 `![alt](url)` 渲染成 `<figure><img><figcaption>alt</figcaption></figure>`，但 figcaption 只是一句话标题，**不能代替正文讲解**。
    - **整篇文章字数下限**：`图片张数 × 300 字`（例如 7 张图 → 全文不少于 2100 字纯中文正文，不含代码块和图片 alt）。
    - **每章必须包含的 4 个文字模块**：①「为什么需要这个机制」背景动机 1~2 句；②图前的「下图展示了 XXX」引出句；③图后的 3~6 条**带具体字段名/常量名/文件路径**的要点列表；④「设计取舍 / 关键技巧 / 易踩坑点」收尾段 1~3 句。缺任一模块都算文字不足。
    - **代码片段**：涉及关键算法/常量/数据结构时必须贴 5~30 行真实代码（带 ts/js/python 等语言标识），不要用自然语言空描述。
    - **配图自身的字段名/术语**必须在正文逐个解释**，不要让读者去图里猜。比如图里画了 `argsHash + resultHash`，正文就要写"`argsHash` 用 stableStringify 排序键名后 sha256；`resultHash` 对 polling 类工具特别提取 status/exitCode/aggregated 等关键字段后再哈希"。
    - 写完 .md 后**必须自检**：每张图上下 30 行内的正文是否 ≥ 250 字、是否有要点列表、是否解释了图里的术语；任一不达标 → 立刻补文字，不要带着"图大于文"的章节进 Step 4。

## 输出目录

**统一输出到**：`~/Desktop/html/`（macOS 桌面的 html 文件夹）

进入任何生成步骤前先确保目录存在：

```bash
mkdir -p ~/Desktop/html
OUT_DIR="$HOME/Desktop/html"
```

- `.md` 文件 → `$OUT_DIR/xxx.md`
- `.html` 文件 → `$OUT_DIR/xxx.html`
- 同名直接覆盖，不做增量追加

## 定位 SKILL_DIR

在执行脚本前先定位本 skill 安装目录（即本 SKILL.md 所在目录）：

```bash
# 示例
SKILL_DIR="$HOME/.agents/skills/knowledge-html-viewer"
```

## 工作流（5 步）

```
Step 0: 建目录       → mkdir -p ~/Desktop/html（所有产出都落到这里）
Step 1: 收集素材     → 阅读代码/文档，提炼要点、找出需要配图的原理
Step 2: 生成配图     → 调用文生图建任务接口 + 轮询查状态接口取 URL
Step 3: 写 Markdown  → 用 create_file 在 ~/Desktop/html/ 下创建 .md，用 ![alt](url) 嵌入图片
Step 4: 脚本转换     → 调用 generate_html.py 生成 ~/Desktop/html/xxx.html
Step 5: 验证         → 用 open 命令打开浏览器检查
```

### Step 1: 收集素材

阅读相关代码文件，提取：
- 功能背景和动机
- 架构设计（模块关系、数据流）
- 核心实现（关键类、方法、代码片段）
- 配置项和使用方式
- **【必做】列出 4~10 个"必须配图"的原理点**（例如：整体架构、关键流程、状态机、对比关系、时序、分层、错误恢复路径、一图概括/总览等）。**少于 4 个视为收集不充分，回到素材阅读继续挖**；超过 10 个时合并最相近的两个，但不要为了凑下限或压上限而牺牲解释力。判断标准只有一个：**这个点用文字讲清楚费劲、配图能秒懂吗？是 → 必须配图**。

### Step 2: 生成配图（必做）

对 Step 1 列出的每个原理点**各生成 1 张图**（**4~10 张**）。**此步骤不可跳过**——没图就不能进入 Step 3。**特别提醒**：「一图概括 / 总览 / 全景 / Cheat Sheet / 全链路」这类章节是配图的高优先级位置，绝不允许用 ASCII 字符画替代——这种章节本身就是为"看图就懂"而存在的。

#### 2.1 建任务

并发调用你接入的文生图 API（推荐：OpenAI `gpt-image-1` / DALL·E 3、Google Imagen、Stability AI / Stable Diffusion API、本地 ComfyUI、或任意支持文生图的 MCP 工具）。常用参数：

| 参数 | 推荐值 | 说明 |
|---|---|---|
| `prompt` | 见下方模板 | **必须英文，长度控制在 300~600 字符内**，太长容易失败 |
| `aspectRatio` | `"16:9"` 或 `"4:3"` | 技术原理图优先宽屏 |
| `imgCount` | `1` | 单张即可 |

**prompt 模板（Notion 风格原理图）**：

```
A clean Notion-style infographic illustrating <one-sentence concept>.
Show <element A>, <element B>, <element C> connected by <arrows / lines / blocks>.
Minimalist hand-drawn look, soft pastel palette, subtle shadows,
plenty of white space, thin strokes, tiny English labels on each block.
No photo-realistic rendering, no 3D, flat 2D diagram only.
```

写 prompt 的硬规则：
- **只用英文**（中文 prompt 易失败）
- **一句话主旨 + 3~5 个视觉要素 + 风格描述**，不要堆砌形容词
- **不要引号嵌套**、不要特殊符号
- **失败先看 message 分清原因再处理**（详见 Gotcha 第 8 条）：限流/QPS 类 → `sleep 30~60s` 用原 prompt 重试，**禁止简化**；只有"数据格式错误"才砍 1/3 修饰词重写。质量优先，宁可多等也不降级 prompt。

每次调用都会返回一个任务 ID（不同 provider 字段名不同，如 `job_id` / `generation_id` / `generateUuid` 等），**记录下来**用于后续查询。

#### 2.2 查询结果

对每个任务 ID 调用 provider 文档指定的"查状态/取结果"接口（**只有这个接口能拿到最终 URL**，不要瞎试同一 provider 下其他看起来相似的接口）。

返回结构示例（具体字段名以 provider 文档为准）：
```json
{
  "job_id": "xxx-yyy-zzz",
  "status": "succeeded",
  "images": [{"imageUrl": "https://your-cdn.example.com/.../xxx.png"}]
}
```

状态码：
| status | 含义 | 处理 |
|---|---|---|
| pending / running | 生成中 | 等 15~30s 后再查 |
| succeeded | 成功 | 记录 `images[0].imageUrl` |
| failed | 失败 | **先看 message 判断原因**：<br/>① 含"限流/rate limit/QPS/throttled" → **不要简化 prompt**，`sleep 30~60s` 后用原 prompt 重建任务，循环到出图<br/>② 含"数据格式错误/format/invalid" → 简化 prompt（缩短、去特殊符号）重建任务<br/>③ 其他未知错误 → 先 sleep 30s 用原 prompt 重试一次，再考虑简化

⚠️ 即使用户在前面对话里创建过任务，也**必须用 provider 指定的"查状态"接口取 URL**，别去试同 provider 的"素材库/历史记录"类接口——这类接口通常只返回已完成的素材，对未完成的任务会报错或返回空。

## Step 3: 创建 Markdown 文件（必须内嵌图片 + 充足文字讲解）

用 `create_file` 写 `.md`，**文件路径必须是 `~/Desktop/html/xxx.md`**。**配图只是辅助，文字讲解才是主体**。每个章节都按下面的「四段式」模板组织：背景动机 → 图前引出 → 配图 → 图后讲解（要点 + 代码 + 取舍）。

#### ✅ 标准章节模板（每章必须包含 4 个文字模块）

```markdown
## 3. ID Sanitize（strict / strict9）+ 畸形名推断

并非所有模型 provider 都接受任意字符的 toolCallId。比如 Mistral 严格要求 **9 个 alphanumeric 字符**；Cloud Code Assist 类 provider 要求 strict alphanumeric。OpenClaw 用两种 mode 一刀切兼容，必要时用 sha256 哈希补齐。<!-- ① 背景动机 1~2 句 -->

更棘手的是：模型偶发会把工具名编码进 toolCallId（典型 `functionsread3` / `functionswrite4`），此时严格 router 直接 `Tool not found`。下图展示了 sanitize 双 mode + 6 候选 token 推断 的完整流程：<!-- ② 图前引出句 -->

![ID Sanitize 双 mode 与畸形名候选推断](https://your-cdn.example.com/2026/05/28/39b0c89b33c57d02.png)

**关键要点**（结合上图逐项对照）：<!-- ③ 图后 3~6 条带字段名/文件路径的要点 -->

- **strict 模式**：直接 `replace(/[^a-zA-Z0-9]/g, '')`，空串退化为常量 `defaulttoolid`，对应代码 [`tool-call-id.ts:42`](file:///path/tool-call-id.ts#L42)
- **strict9 模式**：≥9 字符直接截断；<9 字符走 `sha256(rawId).slice(0,9)`，避免 Mistral 协议拒绝
- **6 候选 token**：原值 / 去尾数字 / 去 `:._/-` 数字 / `/` 改 `.` / 剥 `functions?` 前缀 / 剥 `tools?` 前缀，**只有恰好命中一个 allowedToolName 才返回真名**（避免误判）
- **保守判定 `looksLikeMalformedToolNameCounter`**：`/^(?:functions?|tools?)[._-]?/i` 与 `/(?:[:._-]\d+|\d+)$/` 双正则都命中才算"模型自己编出来的工具名"，正常工具名一律不动

```ts
// 关键代码片段（必须贴真实代码，不要用自然语言空描述）
function inferToolNameFromToolCallId(rawId, allowedToolNames) {
  const candidates = buildCandidateTokens(rawId);
  const hits = new Set<string>();
  for (const c of candidates) {
    const real = resolveStructuredAllowedToolName(c, allowedToolNames);
    if (real) hits.add(real);
  }
  return hits.size === 1 ? [...hits][0] : null;
}
```

**设计取舍**：宁可返回 `null` 让上层把整个 toolCall 丢回模型重发，也不允许"多个候选不一致时挑一个"——错误工具名导致的副作用（写错文件、发错消息）远比一次重试昂贵。<!-- ④ 收尾段 1~3 句 -->
```

#### ❌ 反面案例（图多文少，不合格）

```markdown
## 3. ID Sanitize

下图展示了 sanitize 流程：

![ID Sanitize](https://your-cdn.example.com/...)

关键点：
- 双 mode
- 6 候选
```

这种"一句引出 + 一张图 + 三个名词" 的写法**直接不合格**——读者看完只知道"有这个东西"，但不知道字段名、不知道边界条件、不知道为什么这么设计。

#### 字数自检

写完 .md 后用以下命令自检：

```bash
# 统计每张图前后 30 行的中文字数（粗略）
awk '/!\[.*\]\(http/{print NR}' xxx.md  # 找到图片所在行号
# 对每个行号 N，wc -m 统计 [N-30, N+30] 之间的字符数，应 ≥ 250
```

或更直接：**全文中文字符数 ≥ 图片张数 × 300**。例如 7 张图 → 全文中文字符 ≥ 2100。低于这个值一律回去补内容。

#### 内容规范

- 纯标准 Markdown，不要掺 HTML 标签
- 标题用 `#`、列表用 `-`、粗体用 `**`、表格用 `|` 分隔
- 代码块用三反引号 + 语言标识（`python` / `bash` / `json` / `ts` 等），**关键章节必须贴 5~30 行真实代码**
- 图片链接直接用 Step 2 拿到的 **公网 CDN URL**（不要下载到本地再引用相对路径）
- 文件/符号引用尽量用 `[name](file:///path)` markdown 链接形式，便于读者跳转源码

### Step 4: 调用脚本生成 HTML

```bash
mkdir -p ~/Desktop/html
python3 "$SKILL_DIR/scripts/generate_html.py" \
  --title "页面标题" \
  --content "$HOME/Desktop/html/xxx.md" \
  --output "$HOME/Desktop/html/xxx.html" \
  --theme dark \
  --toc true
```

参数说明：
- `--title`：页面标题（支持中文）
- `--content`：`.md` 文件路径
- `--output`：输出 `.html` 路径
- `--theme`：`light` 或 `dark`（技术讲解推荐 `dark`）
- `--toc`：是否生成侧边目录

脚本已内置 `![alt](url)` → `<figure><img><figcaption>` 的转换，配图会带说明文字展示。

### Step 5: 验证

```bash
open ~/Desktop/html/xxx.html
```

浏览器里重点检查（任一失败都算不合格）：
- **图片是否全部正常加载**（预期 **4~10 张**，CDN URL 偶尔需等 1~2s）
- **图片是否覆盖所有关键原理**（不能出现"有一段原理讲解却没有配图"，尤其是"一图概括/总览"章节绝对不能是 ASCII 框图）
- **是否存在任何 ASCII 字符画 / `+--+` 框图 / `──>` 拼图** —— 一旦发现，立刻回 Step 2 出真图替换
- **🆕 文字密度检查（防图多文少）**：
  - 每张图上下 30 行内是否有完整的「背景 + 引出 + 要点列表 + 代码/取舍」四段式正文
  - 每张图周围中文字数 ≥ 250；全文中文字数 ≥ `图片张数 × 300`
  - 配图里出现的字段名/常量名/文件路径，正文是否逐个解释（不要让读者看图猜术语）
  - 关键算法章节是否贴了 5~30 行真实代码（不能只有自然语言空描述）
  - 出现「图很大、图旁只有 1~2 行字」「图占 2/3 屏幕、文字占 1/3」的章节 → **立刻回 Step 3 补文字**，不要交付
- 代码块缩进是否保留
- 侧边目录是否生成
- 主题配色是否生效

## 端到端示例

用户说："写个 HTML 讲讲长期记忆功能的原理"（注意：用户**没说**要配图，但按硬规则仍必须配图）

完整执行序列：

```bash
# 0. 建目录（所有产出都落到这里）
mkdir -p ~/Desktop/html

# 1. 收集素材：阅读 src/agentscope/memory/... 等文件
#    列出需要配图的 5 个点：整体架构、三段回退、双 loop 桥接、三 ID 隔离、一图概括

# 2. 并发建 5 个生图任务 + 查询结果（必须用 provider 指定的"查状态"接口）
#    → 拿到 5 个 imageUrl

# 3. 写 ~/Desktop/html/long-term-memory.md，在对应章节用 ![xxx](cdn_url) 嵌入

# 4. 生成 HTML 到桌面 html 文件夹
SKILL_DIR="$HOME/.agents/skills/knowledge-html-viewer"
python3 "$SKILL_DIR/scripts/generate_html.py" \
  --title "长期记忆功能原理（图解版）" \
  --content "$HOME/Desktop/html/long-term-memory.md" \
  --output "$HOME/Desktop/html/long-term-memory.html" \
  --theme dark \
  --toc true

# 5. 打开验证
open ~/Desktop/html/long-term-memory.html
```

## 批量生成

多篇文档用 `batch_generate.py`：

```bash
python3 "$SKILL_DIR/scripts/batch_generate.py" \
  --config config.json \
  --output-dir ./docs/html/
```

## 模板与样式

- 模板位置：`$SKILL_DIR/templates/base_template.html`
- 模板内置 `white-space: pre` 代码块样式、响应式布局、代码复制按钮
- 支持浅色/暗色主题切换（CSS 变量在 `:root`）
- 自定义样式：改 `base_template.html` 中 `:root` 的 CSS 变量

## 错误恢复

| 问题 | 原因 | 解决 |
|------|------|------|
| 代码块缩进丢失 | 手写了 HTML | 删掉 .html，回 Step 3 写 .md，再走 Step 4 |
| 脚本报 FileNotFoundError | SKILL_DIR 路径错误 | 确认 SKILL.md 的实际路径，重新设置 SKILL_DIR |
| 中文标题乱码 | 文件编码非 UTF-8 | 确保 .md 文件以 UTF-8 保存 |
| 脚本报 ModuleNotFoundError | 缺少 Python 依赖 | 脚本仅依赖标准库，检查 Python 版本 ≥ 3.8 |
| 生图失败（数据格式错误） | prompt 过长/有特殊符号/中文 | 简化为纯英文短 prompt 重试 |
| 生图失败（限流 / rate limit / 模型提供方限流） | 上游 QPS 限制 | **绝对不要简化 prompt**！`sleep 30~60s` 后用原 prompt 重建任务，质量优先 |
| 生图任务一直 pending/running | 排队中 | 等 15~30s 再查，不要轮询过快 |
| HTML 里图片裂图 | URL 写错或图未生成完就嵌入 | 确认 Step 2 拿到的是 succeeded 状态的 URL |
| 试图用素材库/历史记录接口查图 | 用错工具 | **唯一正确做法：用 provider 文档指定的"查状态/取结果"接口** |
| 产出的 HTML 没有配图 / 只有文字 | 跳过了 Step 2 | **不合格**，必须补 4~10 张原理图重新生成 |
| 章节有原理讲解但无配图 | 收集素材时漏列了原理点 | 回 Step 1 补齐原理点清单，再走 Step 2 补图 |
| "一图概括/总览"章节是 ASCII 框图 | 用字符画糊弄了真图位 | **严重不合格**，必须用文生图模型出真图替换 |
| 配图只有 2~3 张 | 触发了旧版下限 | 现在下限是 4 张；回 Step 1 补原理点，最多到 10 张 |
| 文件写到了项目目录或当前工作目录 | 忘了强制输出路径 | 删掉错误位置的文件，重新写到 `~/Desktop/html/` |
| `~/Desktop/html/` 不存在导致写入失败 | 没先建目录 | `mkdir -p ~/Desktop/html` 再写 |
