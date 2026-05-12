# 本科论文通用 AI 标准化套件

本套件用于把任意本科毕业论文或毕业设计整理成 AI 能稳定读取、生成、检查和迭代的资料结构。它不绑定某一个学校、专业、项目或技术栈。

适用场景包括：

- 软件系统、网站、小程序、管理系统、物联网平台等设计与实现类论文。
- 实验、调查、数据分析、案例研究等研究类论文。
- 工程设计、产品设计、方案设计等毕业设计说明书。
- 已有 Word 论文的结构审查、图表规范化、证据链整理和终稿自检。

## 推荐使用顺序

1. 先读 `01-本科论文标准化最佳实践.md`，确定学校要求、论文类型和最低通用规则。
2. 再读 `02-公开标准与高校规范来源.md`，了解哪些规则来自国家标准、教育部文件或高校共性规范。
3. 填写 `templates/standard-profile.yaml`，把学校模板、导师要求、参考文献版本和格式默认值配置清楚。
4. 填写 `templates/thesis-ai-spec.yaml`，记录题目、专业、论文类型、章节、研究对象、证据材料和风险项。
5. 使用 `templates/chapter-section-template.md` 逐章生成、改写或检查正文。
6. 使用 `templates/figure-registry.yaml` 管理全部图、表、公式、截图、源文件和正文引用位置。
7. 系统实现类论文先运行 `build_project_evidence.py` 生成 `paper-context/evidence/`。
8. 如果想一次完成“初始化资料包 + workflow 日志 + 项目证据首轮扫描 + 模板检查”，可以直接运行 `bootstrap_thesis_project.py`。
9. 如果已经有学校模板提取结果和论文 `.docx` 草稿，终稿阶段优先运行 `finalize_thesis_delivery.py`，统一完成资料包检查、模板格式比对、保守修复和修复后二次比对。
10. 使用 `drawio/` 下的 `.drawio` 模板重画结构性图。
11. 文献综述或相关工作较多时，先运行 `generate_literature_search_config.py`、`run_keyword_harvest_no_dedup.py`、`continue_download_and_dedup.py`、`verify_select_literature.py`，再抽取 PDF 参考文献并建立正文-文末引用闭环。
12. 正文写完或已有草稿时，先用 `aigc-detection-report.yaml` 和检测脚本估计 AIGC 风险，再用 `aigc-style-review.yaml` 做风格治理；终稿需要时可启用逐段处理的 AIGC 最终降低版。
13. 每次修改正文、引用、图表、格式或 AIGC 段落后，都要写入 `paper-context/workflow/revision-log.md` 和 `revision-trace.jsonl`，方便追溯。
14. 最后用 `templates/ai-review-rubric.json` 做终稿审查，再进入 Word/PDF 视觉检查。

## 文件结构

```text
thesis-ai-standard/
  README.md
  01-本科论文标准化最佳实践.md
  02-公开标准与高校规范来源.md
  templates/
    standard-profile.yaml
    thesis-ai-spec.yaml
    chapter-section-template.md
    figure-registry.yaml
    literature-review-matrix.yaml
    citation-crossref-register.yaml
    aigc-detection-report.yaml
    aigc-style-review.yaml
    ai-review-rubric.json
    ai-prompts.md
  drawio/
    system-architecture-template.drawio
    backend-layered-architecture-template.drawio
    business-flow-template.drawio
    er-diagram-template.drawio
    algorithm-workflow-template.drawio
    sequence-diagram-template.drawio
```

## 标准依据优先级

实际使用时按以下顺序执行：

1. 学校或学院正式发布的毕业论文模板、撰写规范、任务书、答辩要求。
2. 导师或课题组明确要求。
3. 教育部本科毕业论文抽检、学术规范、学位论文作假处理等相关文件。
4. 现行国家标准，例如 `GB/T 7713.1-2025`、学校指定的 `GB/T 7714-2015` 或 `GB/T 7714-2025`。
5. 本套件提供的通用默认规则。

说明：截至 2026-05-01，`GB/T 7713.1-2025` 已实施；`GB/T 7714-2025` 已发布，实施日期为 2026-07-01。参考文献格式仍以学校当前通知为准。

## 给 AI 的总原则

- 不编造研究对象、系统功能、实验数据、数据库字段、接口路径、测试结果和参考文献。
- 文献默认以用户当前年份为准取近 6 年；学校、导师、任务书或用户指定年份范围时优先。
- 默认中文文献 12-15 篇、英文文献 3-5 篇，且必须真实可核验。
- 每个正文引用点最多 2 篇参考文献，不得在同一句或同一观点后堆叠 3 篇及以上文献。
- 先读取 `standard-profile.yaml`，再读取 `thesis-ai-spec.yaml`，最后读取章节证据材料。
- 学校没有明确规定的格式，只使用保守默认值，并标记为“可替换”。
- 每张图、表、公式、截图都必须能追溯到正文位置和证据来源。
- 论文正文不得出现“根据用户提供材料”“通过分析代码”“让 AI 生成”等工作流痕迹。

## 迁移方式

新论文不要直接改通用规则文件；应复制或填写 `templates/` 中的空白模板。

通用化迁移时，主要替换四类内容：

- 学校规范：写入 `standard-profile.yaml`。
- 论文事实：写入 `thesis-ai-spec.yaml`。
- 图表清单：写入 `figure-registry.yaml`。
- 专属图形：复制 `drawio/` 模板后按论文对象改节点。

## 证据层建议

系统实现类项目建议建立：

```text
paper-context/
  evidence/
    project-evidence.json
    code-structure.md
    tech-stack.md
    api-list.md
    database-schema.md
    test-results.md
  literature/
    reference-extraction.json
    reference-extraction.md
    citation-crossrefs.md
    citation-crossrefs.json
    citation-crossref-register.yaml
  aigc/
    aigc-detection-report.md
    aigc-detection-report.json
    aigc-style-report.md
    aigc-style-report.json
  workflow/
    revision-log.md
    revision-trace.jsonl
```

这些文件是论文事实依据，不是正文。AI 写作时必须把证据转化为论文语体，不能把扫描过程写进正文。

## AIGC 风格治理建议

本套件的 AIGC 模块分为“检测估计”和“风格治理”两层，不是“绕过检测器”，而是帮助论文减少模板化表达、空泛评价、模糊归因和证据不足的问题。

如果说得再直白一点，这套流程默认就是：

1. 先看哪几段最像 AI。
2. 只改问题最大的段落，不急着整篇重写。
3. 一段一段修，先把套话、总结腔、功能清单感压下去。
4. 第一轮修完后，马上做一次本地检测或本地风格复查。
5. 看复查结果，再补第二轮。
6. 最后再看全文是不是接得顺。

推荐流程：

1. 先生成 `paper-context/aigc/aigc-detection-report.md`，得到基于 `aigc-reduce` 的本地启发式 AIGC 率估计和扫描维度结果。
2. 再生成 `paper-context/aigc/aigc-style-report.md`，按 `aigc-reduce` 的 10 种深度 AI 痕迹定位具体套话、模糊归因和证据缺口。
3. 如需逐段动作清单，再生成 `paper-context/aigc/aigc-revision-plan.md`，把三轮协议拆成可执行的 paragraph plan。
4. 根据报告先做第一轮逐段修复。
5. 第一轮结束后，重新生成检测报告或风格报告做本地复查。
6. 只对复查后还明显偏高风险的段落做第二轮补修。
7. 改写时保留事实、引用和数据边界。
8. 把未核验的来源、数据或项目事实标为 `needs_source` 或 `needs_evidence`。
9. 最终只比较前后趋势，不把估计值当成学校官方检测分数。

如果需要“整篇最终降低版”，可以让 AI 按正文自然段生成 `paper-context/aigc/aigc-final-paragraph-pass.md`，先逐段修第一轮，再本地复查，再补一轮，最后拼接全文。该模式极度消耗 token，建议只在终稿或外部报告集中命中时使用。

如果你想让 AI 说人话一点，可以直接在提示词里加这些话：

- `尽量大白话`
- `一段一段修`
- `修完先本地测一次`
- `检测完再补一轮`
- `少讲术语，直接说哪里像 AI`

## 修改追溯要求

论文正文、AIGC 段落、引用、图表、格式和导师批注处理只要发生实质性修改，都必须记录到：

- `paper-context/workflow/revision-log.md`
- `paper-context/workflow/revision-trace.jsonl`

每条记录至少说明：修改位置、修改前摘要、修改后摘要、改了什么、为什么改、依据来自哪里、涉及哪些文件、是否仍有 `needs_source` 或 `needs_evidence`。高/中风险 AIGC 段落改写必须能对应到段落编号和报告项。
