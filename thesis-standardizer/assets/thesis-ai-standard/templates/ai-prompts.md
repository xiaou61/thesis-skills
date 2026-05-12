# AI 协作提示词模板

所有提示词默认先读取：

1. `standard-profile.yaml`
2. `thesis-ai-spec.yaml`
3. `figure-registry.yaml`
4. `paper-context/evidence/` 中的证据索引
5. 当前章节正文和证据材料

如果学校模板与本套件默认规则冲突，必须以学校模板为准。

## 1. 论文结构检查

```text
请读取 standard-profile.yaml、thesis-ai-spec.yaml 和当前论文目录，检查章节层级是否符合该论文类型。

输出：
1. 学校模板中必须保留的结构
2. 缺失章节
3. 章节顺序问题
4. 小节命名不一致问题
5. 需要新增、合并或删除的章节
6. 需要新增或调整的图表、公式、表格

要求：
- 只基于已提供材料，不要编造学校要求。
- 如果论文类型不明确，先列出可判断依据和需要确认的信息。
```

## 1.5 程序证据抽取

```text
请先检查项目中是否已有 paper-context/evidence/。
如果没有，请运行 thesis-standardizer 的 build_project_evidence.py。

然后读取：
- project-evidence.json
- code-structure.md
- tech-stack.md
- api-list.md
- database-schema.md
- test-results.md

输出：
1. 可用于论文的真实技术栈
2. 可用于架构图的模块边界
3. 可用于数据库设计的表/实体线索
4. 可用于接口说明的 API 线索
5. 可用于测试章节的证据
6. 仍需人工确认的源码事实

要求：脚本扫描结果只是索引，重要结论必须回看源码或用户材料确认。
```

## 2. 标准配置检查

```text
请读取 standard-profile.yaml，检查论文规范来源是否完整。

重点检查：
1. 是否填写学校模板来源
2. 是否填写参考文献标准版本
3. 是否明确学校规则优先于通用默认规则
4. 是否存在“未确认却被当成硬规则”的项目
5. 是否存在可能影响 Word/PDF 排版的高风险项

输出：
- 已确认规则
- 待确认规则
- 可用默认规则
- 不应自动修改的格式项
```

## 3. 图表规范检查

```text
请读取 figure-registry.yaml，检查每张图、表、公式是否满足：
1. 编号连续
2. 标题明确
3. 有正文引用位置
4. 有源文件、截图来源或数据来源
5. 类型正确
6. 与章节内容匹配
7. 不含隐私、调试脏数据或无关截图内容

输出可执行修改建议，并按 critical / major / minor 分级。
```

## 4. 单章改写

```text
请基于以下材料改写第X章：
- standard-profile.yaml
- thesis-ai-spec.yaml
- chapter-section-template.md
- 本章已有正文
- 本章相关图表、公式、表格
- 本章证据材料

要求：
1. 保留真实事实。
2. 改善论文语体和逻辑衔接。
3. 不新增无证据结论。
4. 不改变学校格式要求。
5. 图表必须先解释再出现。
6. 不出现“根据用户提供材料”“通过分析代码”等 AI 工作流表述。

输出：
- 改写正文
- 修改说明
- 证据不足清单
- 需要人工确认的问题
```

## 5. 图表生成说明

```text
请根据以下输入生成可编辑图：
- 图编号：
- 图题：
- 图类型：
- 参与角色、模块、实体、变量或步骤：
- 节点关系：
- 数据流、业务流、调用顺序或研究流程：
- 所属章节：
- 证据来源：

要求：
1. 使用简洁中文标签。
2. 架构图、流程图、时序图、ER 图、模型图必须可编辑。
3. 不使用装饰性图标、复杂渐变和长段落节点。
4. 图中术语必须与正文一致。
5. 输出 draw.io XML 或 Mermaid 初稿，并说明每个节点的证据来源。
6. 证据不足时先列缺失材料，不要补造节点。
```

## 6. 终稿审查

```text
请按 ai-review-rubric.json 对论文进行终稿审查。

重点检查：
1. 学校规则优先级
2. 结构完整性
3. 章节逻辑
4. 图表与公式规范
5. 证据链
6. 参考文献闭环
7. 测试、实验或分析结果可信度
8. 学术诚信风险
9. 是否出现 AI 工作流痕迹
10. 是否存在单个正文引用点超过 2 篇参考文献或 3 篇及以上扎堆引用

输出：
- 总体评分
- critical 问题
- major 问题
- minor 问题
- 建议修改顺序
- 必须人工复核的 Word/PDF 排版项
```

## 7. 文献交叉引用闭环

```text
请读取：
- paper-context/literature/reference-extraction.json
- paper-context/literature/citation-crossrefs.md
- thesis-ai-standard/templates/citation-crossref-register.yaml
- 当前正文引用位置
- 当前参考文献列表

输出：
1. 正文已有引用与文末条目的对应表
2. 文末条目但正文未引用的问题
3. 正文引用但文末缺条目的问题
4. PDF 抽取候选但尚未核验的文献
5. 与章节论点弱相关或不应引用的文献
6. 需要补充核验的作者、年份、题名、来源、DOI 或 URL
7. 超出默认近 6 年范围、年份缺失或与用户指定年份范围不符的文献
8. 单个正文引用点超过 2 篇参考文献或存在 3 篇及以上扎堆引用的问题

要求：候选文献不能直接当作最终参考文献；必须标注 verified / needs_check / rejected。每个正文引用点最多 2 篇参考文献，超过时应拆分到不同论点、句子或综述矩阵比较说明。
```

## 8. 论文资料包自检

```text
请运行 thesis-standardizer 的 check_thesis_workspace.py 检查 thesis-ai-standard。

然后根据报告输出：
1. 缺失文件
2. 解析失败文件
3. 仍是占位内容的关键字段
4. 可以继续写作的部分
5. 必须先补齐的材料
```

## 9. AIGC 率检测报告

```text
Use $thesis-standardizer，请读取当前章节草稿，运行 AIGC detection workflow。

要求：
1. 生成 paper-context/aigc/aigc-detection-report.md 和 json。
2. 检测口径必须对齐 xiaofenggan01/aigc-reduce。
3. 输出本地启发式 estimated_aigc_rate、overall_risk、triggered_dimensions。
4. 按扫描维度列出结果：模板句式密度、被动语态、句长突发性、段落对称性、嵌套编号、冒号并列、标点规律。
5. 按段落列出 triggered_metrics 和 high / medium / low 风险。
6. 明确说明：这个结果是本地启发式 AIGC 风格估计，不是学校或第三方平台的官方检测分数。
```

## 10. AIGC 风格风险报告

```text
Use $thesis-standardizer，请读取当前章节草稿，运行 AIGC style-governance 模块。

要求：
1. 先输出风格风险报告，不要直接改写。
2. 风格治理口径必须对齐 xiaofenggan01/aigc-reduce 的三轮协议。
3. 按段落列出命中的 10 类深层 AI 痕迹，例如重要性膨胀、同义词轮换、三板斧、系词回避、模糊归因、公式化挑战段、悬浮式分析、空洞结论、破折号过度使用、虚假范围。
4. 单独列出 AI 高频词、needs_source 和 needs_evidence。
5. 给出建议修改顺序，并说明应先做“减法”还是“加法”。

注意：目标是提升学术写作质量，不承诺规避任何检测器。
```

## 11. 基于报告定向改写

```text
请基于 aigc-style-report.md 和 aigc-style-review.yaml 只修改高风险段落。

要求：
1. 保留原有事实、数据、引用和论文观点。
2. 不新增未核验来源、实验、项目事实或 DOI。
3. 删除空泛评价句，改为具体结论、限制或后续工作。
4. 模糊归因必须补真实来源或标注 needs_source。
5. 输出改写正文、关键改动说明、仍需补证据清单。
```

## 11.5 AIGC 确定性改写计划

```text
Use $thesis-standardizer，请先生成 AIGC 确定性改写计划，而不是直接整段重写。

要求：
1. 运行 build_aigc_revision_plan.py，输出 aigc-revision-plan.md 和 json。
2. 对每个高风险段落按三轮协议列出：
   - round1_remove_ai_traces
   - round2_add_human_features
   - round3_anti_ai_audit
3. 所有动作必须优先引用 aigc-reduce 的 replacement-tables.md 思路。
4. 没有证据支持的增强动作只能写建议，不能直接补进正文。
```

## 12. AIGC 最终降低版（逐段，极度消耗 token）

```text
Use $thesis-standardizer，对整篇论文执行 AIGC 最终降低版。

请先运行 analyze_aigc_style.py，并额外生成：
paper-context/aigc/aigc-final-paragraph-pass.md

开始前必须提示：
AIGC 最终降低版会按论文文本分割后逐段处理、逐段复查、再拼接全文，极度消耗 token。建议只在终稿或外部报告集中命中时使用。

逐段处理要求：
1. 每次只处理一个自然段，保留原事实、数据、引用、章节功能和图表编号。
2. 严格按三轮协议组织：先去 AI 痕迹，再注入人类特征，最后做 Anti-AI 审计。
3. 必须结合 replacement-tables.md 的词级、句级、段落级替换表。
4. 对每段输出 revised_paragraph、deterministic_changes、human_features_added、preserved_facts、needs_source、needs_evidence。
5. 所有段落处理完后拼接全文，检查段间衔接，不要让每段都像孤立改写。
6. 复跑风格报告，比较 high/medium 风险段落变化。
```

## 13. 修改追溯日志

```text
Use $thesis-standardizer，请为刚才的论文修改补充追溯日志。

要求：
1. 写入 paper-context/workflow/revision-log.md。
2. 同步写入 paper-context/workflow/revision-trace.jsonl。
3. 每条记录包含：location、before、after、change、reason、evidence、files、status。
4. AIGC 高/中风险段落改写必须对应到段落编号和报告项。
5. 仍缺来源或证据的位置标注 needs_source / needs_evidence。
```
