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
8. 使用 `drawio/` 下的 `.drawio` 模板重画结构性图。
9. 文献综述或相关工作较多时，先自动生成检索配置和近 6 年文献候选，再用 skill 脚本抽取 PDF 参考文献，建立文献交叉引用索引，并用 `citation-crossref-register.yaml` 做正文引用与文末参考文献闭环。
10. 正文写完或已有草稿时，用 `aigc-style-review.yaml` 和本地报告脚本做 AIGC 风格治理。
11. 最后用 `templates/ai-review-rubric.json` 做终稿审查，再进入 Word/PDF 视觉检查。

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
    aigc-style-report.md
    aigc-style-report.json
```

这些文件是论文事实依据，不是正文。AI 写作时必须把证据转化为论文语体，不能把扫描过程写进正文。

## AIGC 风格治理建议

本套件的 AIGC 模块不是“绕过检测器”，而是帮助论文减少模板化表达、空泛评价、模糊归因和证据不足的问题。推荐流程：

1. 先生成 `paper-context/aigc/aigc-style-report.md`。
2. 用户或 AI 根据报告确认需要修改的段落。
3. 只对高风险段落做定向改写。
4. 改写时保留事实、引用和数据边界。
5. 把未核验的来源、数据或项目事实标为 `needs_source` 或 `needs_evidence`。
