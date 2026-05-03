# Thesis Skills

一个面向本科毕业论文/毕业设计的 Codex skill。目标是把“程序源码 + 学校模板 + PDF 文献 + 截图/测试材料 + 草稿正文”整理成 AI 可执行的论文写作流程，让 AI 先建立标准、事实、证据和风格报告，再按章节写作或修改。

核心 skill：`thesis-standardizer`

## 适合做什么

- 把程序源码整理成本科毕业论文资料包。
- 根据学校模板、导师要求和公开标准建立论文标准配置。
- 从 PDF 文献中抽取候选参考文献，并建立正文引用与文末参考文献的交叉引用闭环。
- 管理图、表、公式、截图、draw.io 源文件和正文引用位置。
- 初始化 `paper-context/workflow/`，用多个 Markdown 文件持续记录当前论文执行阶段、步骤、进度、证据缺口和修改日志。
- 读取 Word `.docx` 批注，把导师批注整理成待办清单，再按批注修改论文并记录修订日志。
- 生成 AIGC 风格风险报告，再对高风险段落做定向学术化修改。
- 检查论文中是否存在无证据功能、虚构引用、模糊归因、空泛结论和 AI 工作流痕迹。

## 模块分层

```text
thesis-standardizer/
  SKILL.md                         # AI 入口：模块路由、规则、质量门
  references/                      # 按模块加载的详细工作流
  scripts/                         # 可重复执行的确定性脚本
  assets/thesis-ai-standard/        # 复制到论文项目里的模板包
  agents/openai.yaml               # UI 元数据
```

功能按 7 个模块拆开：

| 模块 | 入口 reference | 脚本 | 用途 |
|------|----------------|------|------|
| 标准模块 | `standards-and-template-resolution.md` | `check_thesis_workspace.py` | 解析学校模板、导师要求、国标版本和默认规则 |
| 程序证据模块 | `source-to-thesis-workflow.md` | `build_project_evidence.py` | 扫描源码、技术栈、API、数据库、测试线索 |
| 文献引用模块 | `literature-and-pdf-workflow.md` | `extract_pdf_references.py`, `build_literature_crossrefs.py` | 抽取 PDF 参考文献候选并建立交叉引用 |
| AIGC 风格模块 | `aigc-style-governance.md` | `analyze_aigc_style.py` | 生成风格风险报告并指导定向修改 |
| 工作台日志模块 | `workflow-state-management.md` | `init_workflow_logs.py` | 生成并维护多个 Markdown 进度文件 |
| Word 批注模块 | `word-comment-revision-workflow.md` | `extract_docx_comments.py` | 抽取 Word 批注，生成修改待办和修订日志 |
| 终稿审查模块 | `quality-gates.md` | 多脚本组合 | 检查证据链、学术诚信、图表引用和排版风险 |

`SKILL.md` 不塞全部细节，只告诉 AI 什么时候读哪个 reference、什么时候跑哪个 script。模板和规范放在 `assets/`，这样新项目可以一键初始化。

## 安装

### 方法一：从 GitHub 安装

```powershell
git clone https://github.com/xiaou61/thesis-skills.git
cd thesis-skills
$dest = Join-Path $env:USERPROFILE ".codex\skills\thesis-standardizer"
Remove-Item -Recurse -Force $dest -ErrorAction SilentlyContinue
Copy-Item -Recurse .\thesis-standardizer $dest
```

重新打开 Codex 会话后调用：

```text
Use $thesis-standardizer，根据我的程序源码和学校模板，先生成论文资料包，再规划本科论文目录。
```

### 方法二：更新已有安装

```powershell
cd thesis-skills
git pull
$dest = Join-Path $env:USERPROFILE ".codex\skills\thesis-standardizer"
Remove-Item -Recurse -Force $dest -ErrorAction SilentlyContinue
Copy-Item -Recurse .\thesis-standardizer $dest
```

## 快速初始化论文项目

在论文项目目录运行：

```powershell
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\init_thesis_workspace.py .
```

会生成：

```text
thesis-ai-standard/
  README.md
  01-本科论文标准化最佳实践.md
  02-公开标准与高校规范来源.md
  templates/
    standard-profile.yaml
    thesis-ai-spec.yaml
    figure-registry.yaml
    literature-review-matrix.yaml
    citation-crossref-register.yaml
    aigc-style-review.yaml
    chapter-section-template.md
    ai-prompts.md
    ai-review-rubric.json
  drawio/
    system-architecture-template.drawio
    backend-layered-architecture-template.drawio
    business-flow-template.drawio
    er-diagram-template.drawio
    algorithm-workflow-template.drawio
    sequence-diagram-template.drawio
paper-context/
  workflow/
    workflow-status.md
    step-plan.md
    progress-log.md
    material-inventory.md
    evidence-gaps.md
    chapter-progress.md
    revision-log.md
```

这些 Markdown 文件就是这个 skill 的“项目记忆”。用户下次继续修改论文时，AI 应先读取 `workflow-status.md` 和 `step-plan.md`，知道论文执行到哪一步，再继续工作。

## 推荐工作流

### 1. 先生成论文资料包

把学校模板、任务书、开题报告、源码、数据库结构、接口文档、截图、测试报告、PDF 文献放到项目目录后，让 AI 先做资料包：

```text
Use $thesis-standardizer，先初始化 thesis-ai-standard，然后根据我的学校模板、源码、截图、测试材料和 PDF 文献生成论文证据包。先不要写正文，先输出标准优先级、真实事实、缺失材料、图表计划和章节目录。
```

AI 会优先生成和维护：

```text
paper-context/workflow/workflow-status.md      # 当前执行到哪一步
paper-context/workflow/step-plan.md            # 分步骤任务板
paper-context/workflow/progress-log.md         # 每次会话做了什么
paper-context/workflow/material-inventory.md   # 已上传/缺失材料
paper-context/workflow/evidence-gaps.md        # 哪些论点缺证据
paper-context/workflow/chapter-progress.md     # 各章节进度
paper-context/workflow/revision-log.md         # 所有修改记录
```

### 2. 扫描程序证据

对系统实现类项目，先生成源码证据索引：

```powershell
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\build_project_evidence.py . --out .\paper-context\evidence
```

然后让 AI 读取：

```text
Use $thesis-standardizer，读取 paper-context/evidence，把真实技术栈、模块边界、数据库/API 线索、测试证据整理进 thesis-ai-spec.yaml 和 figure-registry.yaml。
```

### 3. 填写标准和论文事实

重点填这 3 个文件：

```text
thesis-ai-standard/templates/standard-profile.yaml
thesis-ai-standard/templates/thesis-ai-spec.yaml
thesis-ai-standard/templates/figure-registry.yaml
```

规则：

- 学校模板和导师要求优先。
- 国家标准只作为学校未细化时的参考。
- 论文事实必须来自源码、截图、测试、数据、文献或用户确认。
- 证据不足时先列缺失材料，不要硬写。

### 4. 写正文

让 AI 按章节写，不要一次性整篇乱写：

```text
Use $thesis-standardizer，请基于 standard-profile.yaml、thesis-ai-spec.yaml、figure-registry.yaml 和 paper-context/evidence 写第4章。先列本章证据，再写正文；证据不足的地方标注 needs_evidence。
```

推荐顺序：

1. 相关技术或理论基础
2. 需求分析/研究设计
3. 总体设计/实验过程
4. 详细实现/结果分析
5. 测试/讨论
6. 绪论和结论最后写

## PDF 文献交叉引用

把 PDF 文献放到 `papers/` 后运行：

```powershell
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\extract_pdf_references.py .\papers --out .\paper-context\literature
```

生成：

```text
paper-context/literature/reference-extraction.json
paper-context/literature/reference-extraction.md
```

如果已有章节主题或论文提纲，例如 `paper-context/topics.md`：

```powershell
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\build_literature_crossrefs.py .\paper-context\literature\reference-extraction.json --topics .\paper-context\topics.md --out .\paper-context\literature\citation-crossrefs.md --json-out .\paper-context\literature\citation-crossrefs.json
```

然后让 AI 做引用闭环：

```text
Use $thesis-standardizer，读取 reference-extraction.json、citation-crossrefs.md 和 citation-crossref-register.yaml，整理“正文论点 ↔ 候选文献 ↔ PDF 来源 ↔ 文末参考文献”的交叉引用闭环。候选文献未经核验不得进入最终参考文献。
```

注意：PDF 抽取结果只是候选证据，最终作者、年份、题名、期刊、DOI、引用格式必须核验。

## AIGC 风格治理

这个模块参考了 `Yezery/aigc-down-skill` 的“先报告、后定向修改”思路，但本仓库的边界是学术写作质量治理，不承诺规避任何检测器。

### 1. 生成风格风险报告

把章节草稿保存为 `chapter-draft.md`，运行：

```powershell
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\analyze_aigc_style.py .\chapter-draft.md --out .\paper-context\aigc\aigc-style-report.md --json-out .\paper-context\aigc\aigc-style-report.json
```

报告会检查：

- 理论起笔过多
- “由此可见/综上所述”等段末套句
- “首先/其次/再次”过度枚举
- “该设计体现了/该方法基于”等被动分析套话
- “研究表明/专家认为”但没有具体来源
- “具有重要意义/前景广阔”等空泛结论
- 高频学术套话和段落节奏重复

### 2. 基于报告定向改写

```text
Use $thesis-standardizer，读取 paper-context/aigc/aigc-style-report.md 和 thesis-ai-standard/templates/aigc-style-review.yaml，只修改 high/medium 风险段落。保留事实、引用和数据边界；模糊归因标注 needs_source；证据不足标注 needs_evidence。
```

输出应该包含：

- 修改后的正文
- 关键改动说明
- 保留的事实和引用
- 仍需补来源或补证据的位置
- 剩余风格风险

### 3. AIGC 模块红线

- 不编造参考文献、DOI、实验数据和项目事实。
- 不承诺“AI 率一定降低到某个数”。
- 不用错别字、乱标点、刻意口语化来伪装。
- 不把外部检测报告当成绝对真相。
- 最终目标是论文更自然、更具体、更有证据，而不是欺骗检测器。

## Word 批注读取与自动修订

如果导师在 Word 论文里写了批注，可以先抽取批注：

```powershell
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\extract_docx_comments.py .\draft.docx --out .\paper-context\word-comments
```

生成：

```text
paper-context/word-comments/
  word-comments.json
  word-comment-todos.md
  docx-revision-log.md
```

然后让 AI 按批注修改：

```text
Use $thesis-standardizer，读取 paper-context/word-comments/word-comment-todos.md，按导师 Word 批注逐条修改 draft.docx。能直接修改的就改；需要新增数据、来源或截图的地方标注 needs_evidence / needs_source；每条批注的处理结果写入 docx-revision-log.md 和 workflow/revision-log.md。
```

推荐处理规则：

- 内容批注：按论文事实和证据修改，不编造。
- 结构批注：先更新章节计划，再改正文。
- 引用批注：必须走文献交叉引用闭环。
- 格式批注：学校模板优先，必要时用 `thesis-docx` 做 Word/PDF 复核。
- 定稿或二次修改：不要默认把 Markdown/Pandoc 正文回灌到原始 `.docx`。这会扰动目录、分页、图表锚点、页眉页脚和局部版式。优先复制原稿后做原位定点替换，只改必要段落文本。
- 不明确或冲突批注：标记 `blocked`，说明原因。

## 自检与终稿

修改或初始化模板后可以运行：

```powershell
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\check_thesis_workspace.py .\thesis-ai-standard
```

它会检查核心模板是否存在、YAML/JSON/draw.io 是否能解析、论文题目和参考文献版本等关键字段是否仍是占位内容。

终稿前推荐让 AI 执行：

```text
Use $thesis-standardizer，按 quality-gates.md 和 ai-review-rubric.json 做终稿审查，输出 critical / major / minor 问题。重点检查学校规则、证据链、参考文献闭环、图表编号、AIGC 风格报告和 Word/PDF 复核风险。
```

## 常用命令速查

```powershell
# 初始化论文模板包
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\init_thesis_workspace.py .

# 只生成/补齐论文工作台 Markdown 日志
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\init_workflow_logs.py .

# 扫描源码证据
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\build_project_evidence.py . --out .\paper-context\evidence

# 抽取 PDF 参考文献候选
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\extract_pdf_references.py .\papers --out .\paper-context\literature

# 建立文献交叉引用
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\build_literature_crossrefs.py .\paper-context\literature\reference-extraction.json --topics .\paper-context\topics.md --out .\paper-context\literature\citation-crossrefs.md --json-out .\paper-context\literature\citation-crossrefs.json

# 生成 AIGC 风格风险报告
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\analyze_aigc_style.py .\chapter-draft.md --out .\paper-context\aigc\aigc-style-report.md --json-out .\paper-context\aigc\aigc-style-report.json

# 抽取 Word 批注为待办清单
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\extract_docx_comments.py .\draft.docx --out .\paper-context\word-comments

# 检查 thesis-ai-standard 模板包
python $env:USERPROFILE\.codex\skills\thesis-standardizer\scripts\check_thesis_workspace.py .\thesis-ai-standard
```

## 规则

- 学校/学院正式模板优先。
- 导师、任务书和开题要求优先。
- 教育部抽检、学术规范和学位论文作假处理要求是底线。
- 国家标准作为学校未细化时的参考。
- 本仓库默认规则只作为可替换默认值。
- AI 不得编造功能、字段、接口、实验数据、测试结果、参考文献和 DOI。
- AI 不得在论文正文中写“根据用户提供材料”“通过分析代码”“让 AI 生成”等工作流痕迹。
- 每张图、表、公式、截图都必须有来源、编号、标题和正文引用位置。
- 每次改变论文状态或正文内容，都应更新 `paper-context/workflow/` 中对应 Markdown。
- Word 批注修改必须保留批注处理日志，不能静默改动。
- AIGC 风格治理必须以提升论文质量为目标，不以规避检测为目标。

## 仓库内容边界

本仓库只包含通用 skill、模板、脚本和说明文档。不包含任何具体学生论文、学校私有模板、源码项目、截图、PDF 文献或个人资料。
