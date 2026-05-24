# Thesis Standardizer

一个面向本科毕业论文 / 毕业设计的实战型论文标准化工具包。

它的目标不是“帮你生成一篇看起来像论文的东西”，而是把学校模板、项目事实、测试证据、文献材料、AIGC 风格治理、Word 终稿格式检查串成一条可执行的工作流。

最适合这几类场景：

| 场景 | 这个项目帮你做什么 |
| --- | --- |
| 已有项目源码 | 抽证据、整理技术事实、搭论文资料包 |
| 已有论文初稿 | 延续修改，不从 0 重写 |
| 已拿到学校 `.docx` 模板 | 提模板规则、做格式比对和保守修复 |
| 已接近终稿 | 统一检查页边距、页码、目录边界、参考文献节、附录节 |

## 整体流程图

![ChatGPT Image 2026年5月11日 15_15_33](https://eduplan-1305448902.cos.ap-guangzhou.myqcloud.com/imgs/202605111515700.png)

# 成果展示

AIGC降低 突破**维普**4.30新模型

![image-20260512123453145](https://eduplan-1305448902.cos.ap-guangzhou.myqcloud.com/imgs/202605121235353.png)

**知网5.0**:等待突破中。。

## 5 分钟起步

如果你不想先看完整 README，直接照这个表做就行：

| 步骤 | 先做什么 | 输出 / 结果 |
| --- | --- | --- |
| 1 | 初始化工作区，并把学校模板一起纳入上下文 | `thesis-ai-standard/`、`paper-context/` |
| 2 | 从项目源码和材料里构建证据包 | `paper-context/evidence/` |
| 3 | 检查标准层文件是否缺失或未补全 | 缺口清单、下一步建议 |
| 4 | 补三个核心模板 | `standard-profile.yaml`、`thesis-ai-spec.yaml`、`figure-registry.yaml` |

如果你已经有论文 `.docx` 初稿，可以把第 4 步换成“先跑一次终稿格式检查”。

## 最佳实战路线

如果你是第一次用，推荐直接走这一条，不容易绕路。

| 步骤 | 核心动作 | 重点看什么 |
| --- | --- | --- |
| 1 | 初始化工作区 | 模板提取产物 |
| 2 | 补标准和事实 | 三个核心模板 |
| 3 | 从项目里抽证据 | `paper-context/evidence/` |
| 4 | 补文献 | 检索、去重、核验结果 |
| 5 | 写或改章节 | 先证据后正文 |
| 6 | 做 AIGC 风格治理 | 检测报告、风格报告、改写计划 |
| 7 | 做终稿格式收尾 | 模板比对、修复、复检 |

### 第 1 步：初始化工作区

在你的论文项目根目录，让 AI 帮你初始化工作区。

如果你已经有学校的 `.docx` 模板，就在一开始一起交给 AI。

这一步会帮你做三件事：

- 初始化 `thesis-ai-standard/` 资料包
- 初始化 `paper-context/` 工作目录
- 如果提供了学校模板，就自动做模板提取

模板提取完成后，重点看这三个文件：

- `paper-context/template-extract/template-profile.json`
- `paper-context/template-extract/template-profile.md`
- `paper-context/template-extract/template-rule-overrides.yaml`

### 第 2 步：把标准和事实补完整

初始化完成后，不要急着写正文，先把下面三个文件补起来：

- `thesis-ai-standard/templates/standard-profile.yaml`
- `thesis-ai-standard/templates/thesis-ai-spec.yaml`
- `thesis-ai-standard/templates/figure-registry.yaml`

推荐顺序：

1. 先把学校要求、导师要求、参考文献规范写进 `standard-profile.yaml`
2. 再把项目真实技术栈、功能点、数据库、接口、测试事实写进 `thesis-ai-spec.yaml`
3. 最后把要出现在论文里的图、表、截图、公式计划写进 `figure-registry.yaml`

补完后先做一次工作区检查：

- 让 AI 检查 `thesis-ai-standard/` 是否缺关键标准文件
- 让 AI 输出当前缺口和下一步建议

### 第 3 步：从项目里抽证据

如果你是系统类 / 软件类毕业设计，下一步建议先抽证据，再写正文。

重点看这些输出：

- `paper-context/evidence/project-evidence.json`
- `paper-context/evidence/tech-stack.md`
- `paper-context/evidence/api-list.md`
- `paper-context/evidence/database-schema.md`
- `paper-context/evidence/test-results.md`

这些文件的用途不是直接粘进论文，而是帮你确认：

- 哪些功能真的存在
- 哪些数据库字段 / 接口路径真的存在
- 哪些测试结果真的有证据
- 哪些地方还缺截图、缺日志、缺实验结果

### 第 4 步：补文献

如果你还没有整理好的文献，推荐让 AI 先自动生成检索方案，再抓取、续传下载、去重、核验和筛选。

这里最重要的原则只有一个：

- 不编参考文献，宁可报缺口，也不要伪造 DOI、年份、作者、期刊

### 第 5 步：开始写或改章节

到这一步再开始正文，会稳很多。

推荐顺序：

1. 相关技术 / 理论基础
2. 需求分析
3. 总体设计
4. 详细设计与实现
5. 测试
6. 引言和结论最后写

写作或改稿时，建议始终遵守这两个原则：

- 先证据后正文
- 先改最确定的段落，再改最容易虚的总结性段落

### 第 6 步：做 AIGC 风格治理

如果老师会看 AIGC 风格，或者你自己觉得论文太像套话，建议先出报告，再出改写计划，再定向修改。

| 阶段 | 命令 / 动作 | 产物 |
| --- | --- | --- |
| 检测 | `detect_aigc_rate.py` | `aigc-detection-report.md/json` |
| 风格定位 | `analyze_aigc_style.py` | `aigc-style-report.md/json` |
| 确定性改写计划 | `build_aigc_revision_plan.py` | `aigc-revision-plan.md/json` |
| 逐段终稿版 | `analyze_aigc_style.py --final-paragraph-pass-out ...` | `aigc-final-paragraph-pass.md` |

推荐原则：

- 只优先改 `high` / `medium` 风险段落
- 不为了降风格去牺牲事实和证据
- 改完同步写 `revision-log.md`

### 第 7 步：做终稿格式收尾

到了终稿阶段，不建议再东一块西一块地手动检查，直接让 AI 按统一终稿流程执行。

这个入口会固定跑：

- 交付前预检
- 工作区检查
- 模板格式比对
- 保守自动修复
- 修复后二次比对
- 修复日志回写

目前重点覆盖的格式检查包括：

- 页边距、纸张方向、页眉页脚
- 标题样式、正文样式、参考文献样式、题注样式
- 正文起始节是否正确
- 目录节边界是否和模板一致
- 前置部分页码策略是否正确
- Roman / Arabic 页码切换是否正确
- 正文后是否出现异常重启页码
- `参考文献 / 附录` 这类 back matter 是否延续了模板的页码策略

终稿统一入口现在会先额外生成一份 `paper-context/template-compare/delivery-preflight.md`，在真正开始比对 / 修复前先看几件事：

- 终稿 `.docx` 本身是不是可读的 Word 包
- `thesis-ai-standard/templates/` 三个核心模板是不是都在并且能解析
- `paper-context/template-extract/` 的模板提取产物是不是齐
- `figure-registry.yaml` 里已经标成 `checked / inserted` 的图表条目，是否还在引用明显缺失的本地源文件或导出文件
- 修订追踪日志是否已经存在

如果你只想单独检查图表资产链路，也可以直接跑：

```powershell
python .\thesis-standardizer\scripts\check_figure_assets.py --workspace . --out .\paper-context\template-compare\figure-assets-report.md --json-out .\paper-context\template-compare\figure-assets-report.json
```

如果要生成论文常用的可编辑 Visio E-R 图，可以准备 `single_entity` 或 `overview` 类型的 `er-model.json`，再跑：

```powershell
python .\thesis-standardizer\scripts\layout_er_diagram.py .\paper-context\evidence\er-model.json --out .\paper-context\evidence\er-model.positioned.json
powershell -ExecutionPolicy Bypass -File .\thesis-standardizer\scripts\generate_visio_er_diagram.ps1 -InputJson .\paper-context\evidence\er-model.positioned.json -OutputVsdx .\thesis-ai-standard\visio\er-diagram.vsdx -OutputPng .\thesis-ai-standard\exports\er-diagram.png
```

`overview` 总图默认会限量展示核心内容：最多 8 个实体、每个实体最多 4 个代表属性、最多 8 条关系；被省略的实体、属性和关系会写入 `layoutNotes`，方便再生成单实体 E-R 图或数据库表设计。
临时预览更清爽版本时，可以给布局脚本追加 `--max-entities`、`--max-attributes-per-entity` 或 `--max-relationships`。

这一步会重点检查：

- `checked / inserted` 图表是否真的有可编辑源文件
- `inserted` 图表是否真的有导出图片文件
- 导出图片是否小得可疑
- 图表、表格、公式的证据路径是否还能对上本地材料

## DOCX 工作基线

如果你这次工作的重点就是 Word 终稿，而不是正文内容重写，建议把下面这套基线当成默认规则：

1. 先模板，后改稿
2. 先提取 OOXML 事实，再做格式判断
3. 能局部修就不要整篇 round-trip
4. 修完一定复检，不要凭感觉说“格式已经稳了”

这套仓库当前对 `.docx` 的推荐路径是：

1. 学校模板提取：`extract_docx_template_profile.py`
2. 模板规则归一化：`generate_template_rule_overrides.py`
3. 终稿统一检查：`finalize_thesis_delivery.py`
4. 批注提取续改：`extract_docx_comments.py`

真正落到 Word 内容生成或底层 `.docx` 编辑时，再切到内置的 `thesis-standardizer/vendor/docx-editor-cn/`：

1. 新建中文论文版式文档：`vendor/docx-editor-cn/scripts/new_doc.js`
2. Markdown 转 Word：`vendor/docx-editor-cn/scripts/convert_paper.js`
3. 三线表 / 公式插入：`vendor/docx-editor-cn/scripts/table.py`、`formula.py`
4. OOXML 解包 / 回包 / 校验：`vendor/docx-editor-cn/scripts/office/unpack.py`、`pack.py`、`validate.py`

几个很重要的约束：

- 不要因为文件后缀是 `.docx` 就默认它可用，首先它必须是真正可读的 Word OOXML 包
- 对已经稳定的终稿，不要默认走 markdown / pandoc 整体回灌
- 页码、目录域、交叉引用、题注锚点这类问题，脚本检查后仍然需要手工 Word/PDF 复核
- 中文论文常见默认值只能作为 fallback，学校模板和导师规则优先级更高

如果学校没有给出更强规则，这个项目现在采用的中文论文 fallback 心智模型是：

- A4 纸张
- 四边 2.5cm 页边距
- 正文字体优先按模板，否则默认按宋体 / 小四理解
- 标题样式优先按模板，否则常见黑体层级作为弱默认

## 三个常见起手式

### 场景 1：我只有项目源码和学校模板

直接让 AI 按这 4 步推进：

1. 初始化工作区
2. 提取学校模板
3. 构建项目证据包
4. 检查标准文件缺口

然后补：

- `standard-profile.yaml`
- `thesis-ai-spec.yaml`
- `figure-registry.yaml`

这是最稳的起手式。

### 场景 2：我已经有论文初稿，只想继续改

建议这样做：

1. 先提学校模板
2. 再对当前 `.docx` 做终稿格式检查
3. 再按报告定向修正文稿

### 场景 3：我已经快交稿了，只想把格式做稳

直接让 AI 对终稿 `.docx` 执行统一终稿格式检查。

如果你不想走统一入口，也可以单独拆开：

1. 先做模板比对
2. 再做保守自动修复
3. 最后做修复后二次比对

## 推荐你重点看的输出目录

### `thesis-ai-standard/`

这是论文标准和规划层。

你最常改的通常是：

- `templates/standard-profile.yaml`
- `templates/thesis-ai-spec.yaml`
- `templates/figure-registry.yaml`

### `paper-context/template-extract/`

这是模板提取和模板规则层。

核心文件：

- `template-profile.json`
- `template-profile.md`
- `template-rule-overrides.yaml`

### `paper-context/evidence/`

这是项目事实和测试证据层。

核心文件：

- `project-evidence.json`
- `tech-stack.md`
- `api-list.md`
- `database-schema.md`
- `test-results.md`

### `paper-context/template-compare/`

这是终稿格式检查层。

你最常看的通常是：

- `template-compare-before.json`
- `template-repair-report.json`
- `template-compare-after.json`
- `template-finalization-summary.md`

### `paper-context/workflow/`

这是过程追踪层。

核心文件：

- `revision-log.md`
- `revision-trace.jsonl`
- `workflow-status.md`
- `progress-log.md`

## 一套最实用的终稿检查标准

如果你只想记住最重要的检查点，建议盯这几个：

1. 学校模板提取是否已经完成
2. `standard-profile.yaml` 是否补全
3. 论文里的功能、数据、测试结论是否都能回到证据
4. 终稿 `.docx` 是否已经跑过统一终稿格式检查
5. `template-compare-after.json` 里是否还存在 `major`
6. `revision-log.md` 是否能说明你改了什么、为什么改

## 可直接复制的提示词

下面这些提示词是按真实使用场景拆开的，可以直接复制给 Claude Code、Codex 或其他能在本地跑脚本、读文件的 AI 工具。

建议用法：

- 一次只做一类任务，不要把“补文献、改正文、调格式、降 AIGC”混在一句话里
- 如果你已经有学校模板或初稿，记得在提示词里明确说“不要从 0 重写”
- 如果你最在意格式，就反复强调“以 `.docx` 终稿格式一致性为最高优先级”

## 生产环境 SOP 提示词

如果你希望 AI 的执行风格更像正式 SOP，而不是随手帮忙式对话，优先用这一组。

使用建议：

- `短版`：适合你已经很熟这套流程，只想快速开工
- `标准版`：适合大多数正常推进场景
- `强约束版`：适合终稿、格式高风险、导师催得紧、不能跑偏的时候

### SOP 1：项目冷启动

#### 短版

```text
按 thesis-standardizer 的最佳实战 SOP 启动这个论文项目。先初始化工作区、提取模板、构建证据包，再告诉我下一步该补哪些标准文件和材料。
```

#### 标准版

```text
请按 thesis-standardizer 的标准 SOP 启动这个毕业论文项目，执行顺序固定为：
1. 初始化工作区
2. 如果存在学校 .docx 模板，就立即提取模板
3. 构建项目证据包
4. 检查 thesis-ai-standard 是否缺关键内容
5. 输出当前阶段的事实清单、缺口清单、下一步动作

要求：
- 先证据后正文
- 不要开始整章写作
- 先把 standard-profile、thesis-ai-spec、figure-registry 的待补项列出来
```

#### 强约束版

```text
现在按 thesis-standardizer 的生产环境 SOP 冷启动这个论文项目。你必须严格按下面顺序执行，不要跳步，不要提前写正文：
1. 初始化工作区
2. 检查是否存在学校模板；有则立即提取模板
3. 构建项目证据包
4. 审核 standard-profile、thesis-ai-spec、figure-registry 的缺失项
5. 输出事实清单、风险清单、缺失材料清单、建议优先级

硬性要求：
- 不要编造学校要求、项目功能、数据库字段、接口、测试结果、文献
- 不要从 0 重写论文
- 缺证据的地方必须明确标出
- 在没有完成标准层和证据层之前，不允许进入正文写作
```

### SOP 2：已有初稿继续修改

#### 短版

```text
按 thesis-standardizer SOP 接着处理我现有论文初稿，不要重写。先做模板比对，再分清格式问题、内容问题和证据问题。
```

#### 标准版

```text
请按 thesis-standardizer 的初稿续改 SOP 处理我现有的论文初稿，执行顺序固定为：
1. 读取当前论文初稿
2. 读取并提取学校模板
3. 对当前 .docx 做模板比对
4. 输出格式问题、内容问题、证据问题三类清单
5. 优先修最确定、最安全的问题

要求：
- 不要整篇重写
- 保留现有结构
- 能局部改的就局部改
- 格式硬伤优先于措辞润色
```

#### 强约束版

```text
现在按 thesis-standardizer 的生产环境续改 SOP 处理我现有论文初稿。你必须以“保留现有文稿结构、最小化改动风险”为原则，严格执行：
1. 读取现有初稿
2. 读取学校模板并提取规则
3. 对当前 .docx 做模板比对
4. 将问题分成格式问题、内容问题、证据问题
5. 只优先改可以直接验证的项

硬性要求：
- 不要从 0 重写
- 不要擅自重排整篇结构
- 不要为了润色去改掉已经成立的事实
- 未验证的问题只能列清单，不能假装修完
```

### SOP 3：终稿格式检查

#### 短版

```text
按 thesis-standardizer 终稿 SOP 检查这份 .docx，优先盯模板一致性和 remaining major findings。
```

#### 标准版

```text
请按 thesis-standardizer 的终稿格式 SOP 处理这份论文 .docx，执行顺序固定为：
1. 工作区检查
2. 模板比对
3. 保守自动修复
4. 修复后二次比对
5. 输出 remaining major / minor findings

重点检查：
- 页边距
- 页眉页脚
- 标题样式
- 正文起始节
- 目录边界
- 页码策略
- 参考文献 / 附录策略
```

#### 强约束版

```text
现在按 thesis-standardizer 的生产环境终稿 SOP 处理这份论文 .docx。以终稿格式一致性为最高优先级，严格执行：
1. 工作区检查
2. 模板比对
3. 保守自动修复
4. 修复后二次比对
5. 按 critical / major / minor 输出结论

硬性要求：
- 只要还有 major，就不要说已完成
- 不要把内容润色混进格式收尾阶段
- 所有判断都优先依据模板提取结果
- 页码、目录边界、正文起始节、back matter 策略必须单独复核
```

### SOP 4：证据包与事实核对

#### 短版

```text
按 thesis-standardizer SOP 先帮我抽证据，不急着写正文。把真实功能、接口、数据库、测试和缺口整理出来。
```

#### 标准版

```text
请按 thesis-standardizer 的证据核对 SOP 处理当前项目，执行顺序固定为：
1. 构建项目证据包
2. 提取技术栈、模块、数据库、接口、测试信息
3. 输出哪些事实可以直接写进论文
4. 输出哪些点还缺材料

要求：
- 每个结论尽量回到源码、日志、截图、测试报告或数据文件
- 不要把脚本索引当最终事实
```

#### 强约束版

```text
现在按 thesis-standardizer 的生产环境证据 SOP 执行，不要写正文，只做事实核对和证据梳理：
1. 构建项目证据包
2. 提取并核对技术栈、功能点、数据库、接口、测试信息
3. 将“可直接写入论文的事实”和“仍缺证据的点”严格分开

硬性要求：
- 不允许编造任何功能、接口、测试结果、数据库字段
- 缺证据的点必须明确标记
- 没有来源的内容不能进入 thesis-ai-spec
```

### SOP 5：文献检索与核验

#### 短版

```text
按 thesis-standardizer SOP 帮我补文献，先检索，再核验，再输出可用文献和缺口。
```

#### 标准版

```text
请按 thesis-standardizer 的文献 SOP 处理文献工作，执行顺序固定为：
1. 生成检索配置
2. 抓取候选文献
3. 续传下载和去重
4. 核验并筛选
5. 输出正式可用文献和缺口

要求：
- 优先近 6 年
- 中文和英文都要覆盖
- 不能核验的文献不要直接当正式引用
```

#### 强约束版

```text
现在按 thesis-standardizer 的生产环境文献 SOP 执行。你必须严格按“检索 -> 下载 -> 去重 -> 核验 -> 输出结果”的顺序推进。

硬性要求：
- 不得编造作者、题名、年份、期刊、DOI、链接
- 不能核验的文献只能留在候选池，不能直接写入正式参考文献
- 对每条最终保留文献，尽量给出可追溯来源
- 如果文献数量不够，直接报缺口，不要拿低质量结果硬凑
```

### SOP 6：AIGC 风格治理

#### 短版

```text
按 thesis-standardizer SOP 先出 AIGC 检测和风格报告，再只改高风险段落，不要把事实改没。
```

#### 标准版

```text
请按 thesis-standardizer 的 AIGC 风格治理 SOP 处理当前草稿，执行顺序固定为：
1. 生成 AIGC 检测报告
2. 生成 AIGC 风格风险报告
3. 只修改 high / medium 风险段落
4. 同步更新 revision-log

要求：
- 不改动已成立的事实、数据、测试结论
- 来源模糊的地方标 needs_source
- 证据不足的地方标 needs_evidence
```

#### 强约束版

```text
现在按 thesis-standardizer 的生产环境 AIGC 风格治理 SOP 执行。你必须把这项任务当作“学术写作质量治理”，而不是“绕过检测器”。

执行顺序固定为：
1. 生成检测报告
2. 生成风格风险报告
3. 仅处理 high / medium 风险段落
4. 为每一类实质性修改补 revision-log

硬性要求：
- 不允许为降风格而改掉事实
- 不允许无依据扩写
- 每个高风险改动都应当可追溯
- 未核实内容不得写成肯定句
```

### SOP 7：导师批注处理

#### 短版

```text
按 thesis-standardizer SOP 读取导师 Word 批注，分成格式、内容、证据三类，再优先改最稳的部分。
```

#### 标准版

```text
请按 thesis-standardizer 的导师批注处理 SOP 处理我这份带批注的论文，执行顺序固定为：
1. 读取导师批注
2. 将批注分类为格式问题、内容问题、证据问题、待补材料问题
3. 优先处理可直接修改的项
4. 输出仍需我补材料的项
5. 同步记录 revision-log
```

#### 强约束版

```text
现在按 thesis-standardizer 的生产环境导师批注 SOP 执行。你必须先把导师批注变成任务清单，再开始修改，不要边看边乱改。

硬性要求：
- 每条批注都要有处理结果
- 可直接改的项优先改
- 需要补证据或来源的项必须单独列出来
- 所有修改都要进 revision-log
```

### SOP 8：最终交付前审查

#### 短版

```text
按 thesis-standardizer SOP 做交付前总审查，不要先说完成，先给我 critical / major / minor 清单。
```

#### 标准版

```text
请按 thesis-standardizer 的交付前审查 SOP 处理当前论文，执行顺序固定为：
1. 检查学校模板格式
2. 检查章节结构
3. 检查证据链
4. 检查文献闭环
5. 检查图表编号
6. 检查 AIGC 风格风险
7. 检查 revision-log 完整性
8. 输出 critical / major / minor 结论
```

#### 强约束版

```text
现在按 thesis-standardizer 的生产环境交付前审查 SOP 执行，不要在检查前就默认项目可交付。

硬性要求：
- 任何未验证项都不能写成“已完成”
- 任何 remaining major 都必须明确列出来
- 格式、证据、引用、日志四条线都要单独过一遍
- 最后只输出：已验证项、未通过项、仍需人工确认项
```

### 1. 我只有源码和学校模板

```text
用 thesis-standardizer 按最佳实战流程推进这个毕业设计论文。先不要写正文，先做这些事：
1. 初始化工作区
2. 提取学校 .docx 模板
3. 构建项目证据包
4. 帮我整理 standard-profile、thesis-ai-spec、figure-registry 的待补信息
5. 列出还缺哪些材料

要求：
- 不要编造功能、接口、数据、测试结果
- 先证据后正文
- 先给我一个当前项目可写论文的事实清单
```

### 2. 我只有源码，没有学校模板

```text
用 thesis-standardizer 先把这个项目整理成论文资料包。现在没有学校模板，不要假设学校格式细节，先用默认资料包初始化，再帮我：
- 抽取项目证据
- 识别技术栈、模块、数据库、接口、测试信息
- 补一个可写论文的章节建议
- 明确标出哪些地方以后必须等学校模板再定

要求：
- 格式规则不明确的地方统一标记为 needs_review
- 不要开始写完整正文
```

### 3. 我已经有论文初稿，不要从 0 重写

```text
用 thesis-standardizer 接着处理我现有的论文初稿，不要从 0 重写。请先做这些事：
1. 读取当前论文初稿
2. 读取学校模板并提取规则
3. 对当前 .docx 做模板比对
4. 按问题清单告诉我哪些是格式问题，哪些是内容问题，哪些是证据问题
5. 先改最确定、最安全的部分

要求：
- 保留现有结构和大部分内容
- 不要整篇重写
- 优先修格式硬伤和证据硬伤
```

### 4. 我现在最关心终稿格式

```text
用 thesis-standardizer 直接进入终稿格式检查模式。请以 .docx 终稿格式一致性为最高优先级，执行：
1. 工作区检查
2. 模板比对
3. 保守自动修复
4. 修复后二次比对
5. 输出 remaining major findings

重点帮我盯这些问题：
- 页边距
- 页眉页脚
- 标题样式
- 正文起始节
- 目录边界
- 页码策略
- 参考文献节和附录节的页码策略

如果还有 major，就不要说已经完成。
```

### 5. 我只想做模板提取

```text
用 thesis-standardizer 只处理学校论文模板提取，不写正文。请帮我：
1. 提取 .docx 模板结构
2. 生成 template-profile.json、template-profile.md、template-rule-overrides.yaml
3. 总结模板里的关键格式规则
4. 标出哪些规则能自动判断，哪些还需要人工确认

我最关注：
- 页边距
- 标题样式
- 正文起始节
- 目录节
- 页码格式和起始位置
- 参考文献/附录策略
```

### 6. 我想让 AI 先帮我补标准文件

```text
用 thesis-standardizer 帮我补标准层文件，但先不要写正文。请读取当前 workspace 后，重点帮我整理：
- thesis-ai-standard/templates/standard-profile.yaml
- thesis-ai-standard/templates/thesis-ai-spec.yaml
- thesis-ai-standard/templates/figure-registry.yaml

要求：
- 能确认的事实直接填
- 不能确认的地方列成待补项
- 不要编造学校要求和项目事实
```

### 7. 我想先补证据，不急着写

```text
用 thesis-standardizer 先帮我补项目证据，不急着写论文正文。请基于源码和现有材料输出：
- 项目真实功能点
- 技术栈
- 数据库信息
- 接口信息
- 测试与验证证据
- 论文里可以写、但目前还缺材料的点

要求：
- 每个结论尽量能回到文件、截图、日志或测试
- 缺证据的地方明确写出来
```

### 8. 我想自动补文献

```text
用 thesis-standardizer 帮我自动规划文献检索和筛选。请按我的题目、摘要和项目方向：
1. 生成文献检索配置
2. 抓取候选文献
3. 继续下载和去重
4. 进行核验和筛选
5. 输出可用文献和缺口

要求：
- 优先近 6 年
- 中文和英文都要有
- 不编造参考文献
- 不能核验的文献不要直接当正式引用
```

### 9. 我已经有文献清单，只想做核验和映射

```text
用 thesis-standardizer 读取我现有的参考文献清单，不要重新乱找。请帮我：
- 核验作者、年份、题名、期刊、DOI 或链接
- 标出明显有问题的条目
- 建议哪些文献适合放到绪论、相关工作、系统设计、测试分析里
- 帮我建立正文引用和文末参考文献的对应关系
```

### 10. 我想开始写某一章

```text
用 thesis-standardizer 只处理第 X 章，不要改其他章节。请按这个顺序做：
1. 先列出本章已有证据
2. 再列出本章还缺的证据
3. 最后再写或改本章正文

要求：
- 只使用已有源码、截图、数据、测试、文献
- 不补造实验
- 不补造引用
- 本章里引用不要一口气堆很多篇
```

### 11. 我想降低 AIGC 风格，但不要把事实改没了

```text
用 thesis-standardizer 先做 AIGC 风格分析，再做定向修改。请按这个顺序：
1. 生成本地 AIGC 检测报告
2. 生成 AIGC 风格风险报告
3. 只修改 high 和 medium 风险段落
4. 修改后同步写 revision-log

要求：
- 不要把真实功能、数据、测试结论改没
- 不要为了降风格乱改术语
- 证据不足的地方标 needs_evidence
- 来源模糊的地方标 needs_source
```

### 12. 我想做整篇最终降风格版

```text
用 thesis-standardizer 对整篇论文做 AIGC 最终降低版。开始前先提醒我这个流程会极度消耗 token，然后再执行：
1. 按段切分
2. 逐段处理
3. 逐段复查
4. 拼接全文
5. 检查段间衔接

要求：
- 不要把它描述成绕过检测器
- 要按学术写作风格治理来处理
- 每个高风险段落都要留下可追溯修改记录
```

### 13. 我有导师 Word 批注

```text
用 thesis-standardizer 读取导师在 Word 里的批注，按批注生成修改任务。请帮我：
- 分类哪些是格式问题
- 哪些是内容问题
- 哪些是证据问题
- 哪些需要我补材料

然后优先改可以直接改的项，并把每一条处理写进 revision-log。
```

### 14. 我只想补 revision log

```text
用 thesis-standardizer 为我最近这轮论文修改补 revision log。请根据当前 workspace 和最近改动，记录：
- 改了哪里
- 修改前后大意
- 为什么改
- 依据是什么
- 涉及哪些文件
- 还有没有未解决的证据或来源缺口
```

### 15. 我只想做最后一次交付前审查

```text
用 thesis-standardizer 做终稿交付前审查，但先不要直接宣布完成。请重点检查：
- 学校模板格式
- 章节结构
- 证据链
- 文献闭环
- 图表编号
- AIGC 风格风险
- revision-log 是否完整
- Word 终稿格式风险

最后按 critical / major / minor 给我一个清单，没有验证过的地方不要说已完成。
```

## 更强一点的提示词写法

如果你发现 AI 容易跑偏，可以在上面的提示词后面追加这些约束句。

### 强调不要重写

```text
不要从 0 重写，只在现有材料和现有文稿基础上继续推进。
```

### 强调格式优先

```text
以 .docx 终稿格式一致性为最高优先级，内容优化排在格式硬伤之后。
```

### 强调证据优先

```text
先证据后正文，无法确认的事实不要写进论文主体。
```

### 强调不要编造

```text
不要编造功能、接口、测试结果、文献、DOI、年份、截图来源或学校要求。
```

### 强调留下日志

```text
所有实质性修改都要同步写入 revision-log 和 revision-trace。
```

### 强调只改最稳的部分

```text
先改最确定、最容易验证的部分，遇到高风险改动先列清单，不要直接大改。
```

## 什么时候不要急着写正文

下面这些情况，建议先停一下，先补材料：

- 没有学校模板，但已经进入终稿排版阶段
- 没有数据库 / 接口 / 测试事实，却要写实现和测试章节
- 没有参考文献清单，却要大面积补引用
- 导师已经给了 Word 批注，但还没整理成修改清单
- 终稿 `.docx` 还没做过模板比对，就想直接导 PDF

## 使用原则

- 学校模板和导师要求永远优先
- 不编造功能、接口、测试结果、数据、文献、DOI
- 脚本输出是索引，不是最终事实本身
- AIGC 检测结果只是本地启发式估计，不是官方检测分数
- 每次实质性修改都应该留下日志
- 终稿格式问题优先在 `.docx` 里收尾，不要轻易把稳定文档整篇 round-trip

## 最后一条建议

最佳实践不是“先写一篇，再慢慢修”，而是：

先把模板、标准、证据、文献、日志框架搭起来，再开始正文。

这样最后收尾的时候，格式、事实、引用、AIGC 风格这几条线会轻松很多。

## 一句话开始

如果你想直接开工，对 AI 说这一句就够了：

> 用 `thesis-standardizer` 帮我按最佳实战流程推进。先初始化工作区和模板提取，再补标准、证据和文献，最后再做正文和终稿格式收尾。
