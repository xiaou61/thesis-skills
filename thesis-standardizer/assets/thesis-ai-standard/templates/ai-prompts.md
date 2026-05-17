# AI Prompt Templates

Default reads:

1. `standard-profile.yaml`
2. `thesis-ai-spec.yaml`
3. `figure-registry.yaml`
4. `paper-context/evidence/`
5. current chapter text

School rules override this template.

## 1. Structure Check

```text
检查论文结构是否符合论文类型和学校模板。

输出：
1. 必保留结构
2. 缺失章节
3. 顺序问题
4. 命名不一致
5. 需要增删合并的章节
```

## 2. Evidence Check

```text
先检查 `paper-context/evidence/`。
如果没有，运行 `build_project_evidence.py`。

输出：
1. 可写进论文的真实技术栈
2. 模块边界
3. 数据库/接口/测试证据
4. 仍需人工确认的事实
```

## 3. Chapter Rewrite

```text
只基于现有材料改写本章。

要求：
1. 保留真实事实
2. 不补造结论
3. 不改学校格式要求
4. 图表先解释再出现

输出：
- 改写正文
- 修改说明
- 证据不足清单
```

## 4. Final Review

```text
按 `ai-review-rubric.json` 做终稿审查。

输出：
- 总体评分
- critical
- major
- minor
- 建议修改顺序
```

## 5. AIGC Detection

```text
先别改正文。
请跑本地 AIGC 检测，告诉我：
1. 哪几段问题最大
2. 每段主要卡在哪里
3. 先改哪几段最划算

说人话一点。
```

## 6. AIGC Style Report

```text
先不要直接重写。
请出一个 AIGC 风格问题单，按段落说清楚：
1. 哪段最像 AI
2. 像在哪里
3. 是套话、总结腔、功能清单感，还是句子太整齐
4. 哪些地方缺来源、缺证据

尽量大白话。
```

## 7. AIGC Plan

```text
先别直接改正文。
先给我一个逐段修改计划：
1. 先改哪几段
2. 第一轮怎么压 AI 味
3. 本地复查后第二轮怎么补
4. 哪些地方只能挂 `needs_source` / `needs_evidence`
```

## 8. AIGC Round 1

```text
只改高风险段落。

要求：
1. 一段一段修
2. 优先压套话、总结腔、功能清单感
3. 保留事实、数据、引用
4. 改完后立刻做一次本地复查

输出：
- 已修改段落
- 每段修改说明
- 复查后仍高风险的段落
```

## 9. AIGC Round 2

```text
根据本地复查结果，再补第二轮。

要求：
1. 只盯着还高/中风险的段落
2. 不要重写已经改顺的段落
3. 继续用大白话压套话感和清单感

输出：
- 二轮改后段落
- 二轮主要改动
- 剩余风险
```

## 10. AIGC Final Pass

```text
对整篇论文做最终逐段降 AIGC。

顺序：
1. 先分段
2. 第一轮逐段修
3. 做一次本地检测
4. 只补还高风险的段落
5. 最后顺全文

开始前必须提示：
AIGC 最终降低版会按论文文本分割后逐段处理。每段先修，再本地检测，再补一轮，最后再拼接全文，极度消耗 token。建议只在终稿或外部报告集中命中时使用。
```

## 11. Revision Log

```text
把刚才的修改写入：
1. `paper-context/workflow/revision-log.md`
2. `paper-context/workflow/revision-trace.jsonl`

每条记录包含：
- location
- before
- after
- change
- reason
- evidence
- files
- status
```
