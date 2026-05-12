# AIGC Style Governance Module

Use this module when the user asks for AIGC reduction, AI-flavor cleanup, Chinese academic humanizing, paragraph-level rewriting, style reports, or thesis prose polishing.

This module now follows `xiaofenggan01/aigc-reduce`: first strip AI-like surface patterns, then inject controlled human features, and finally run an Anti-AI audit against deep pattern categories. It is an academic writing quality module, not a detector-bypass tool.

Local mirror path:

- `thesis-standardizer/vendor/aigc-reduce/SKILL.md`
- `thesis-standardizer/vendor/aigc-reduce/references/ai-patterns.md`
- `thesis-standardizer/vendor/aigc-reduce/references/replacement-tables.md`

## Boundary

The safe target is:

- clearer argumentation
- higher information density
- fewer formulaic academic cliches
- stronger paragraph-level causality and transitions
- specific citations, data, samples, project facts, and evidence boundaries
- transparent revision notes
- thesis voice without AI workflow leakage

Never promise a guaranteed AIGC score. AI-writing detectors are imperfect and institution-specific. The deliverable is a cleaner academic version plus a record of what changed.

Do not fabricate citations, author names, DOI values, data, interviews, experiments, screenshots, system functions, database fields, or project facts to make prose look more human.

## Required Workflow

Default workflow:

1. Intake the draft, chapter, full paper, or external AIGC report.
2. If a text file is available, run `scripts/analyze_aigc_style.py`.
3. Output a style-risk report first, unless the user explicitly says "directly revise".
4. If the user wants an execution worksheet, run `scripts/build_aigc_revision_plan.py`.
5. Revise by paragraph priority: high -> medium -> low.
6. Preserve facts, citations, terminology, chapter role, and school-style requirements.
7. Mark unsupported claims as `needs_source` or `needs_evidence`.
8. Return revised text plus a revision log and remaining risks.
9. Append every changed high/medium-risk paragraph to `paper-context/workflow/revision-log.md` and `revision-trace.jsonl`.

If the user provides an external AIGC report, treat it as one signal, not truth. Extract highlighted passages, compare them with the actual prose, then produce a local report.

## Final Paragraph Pass

When the user asks for the "AIGC final reduction version", "整篇最终降 AIGC", "逐段降低", or similar wording, use paragraph-by-paragraph final pass mode.

Command:

```powershell
python .\thesis-standardizer\scripts\analyze_aigc_style.py .\chapter-draft.md --out .\paper-context\aigc\aigc-style-report.md --json-out .\paper-context\aigc\aigc-style-report.json --final-paragraph-pass-out .\paper-context\aigc\aigc-final-paragraph-pass.md
```

Deterministic revision-plan command:

```powershell
python .\thesis-standardizer\scripts\build_aigc_revision_plan.py .\chapter-draft.md --out .\paper-context\aigc\aigc-revision-plan.md --json-out .\paper-context\aigc\aigc-revision-plan.json
```

Required warning to show the user:

```text
AIGC 最终降低版会按论文文本分割后逐段处理、逐段复查、再拼接全文，极度消耗 token。建议只在终稿或外部报告集中命中时使用。
```

Final-pass rules:

1. Split the thesis into stable paragraphs; do not merge sections blindly.
2. Rewrite one paragraph at a time.
3. For each paragraph, output `revised_paragraph`, `changes`, `preserved_facts`, `needs_source`, and `needs_evidence`.
4. After all paragraphs are revised, run a whole-text cohesion pass.
5. Fix paragraph-to-paragraph transitions without reintroducing formulaic connectors.
6. Re-run the local style report and compare high/medium risk counts.
7. Keep the original and final paragraph IDs aligned for auditability.
8. Create a revision-trace entry for each rewritten paragraph, using the paragraph ID as `location`.

This mode is token-expensive because every paragraph is read, diagnosed, rewritten, checked against constraints, and reassembled.

## Ten Deep Risk Modes

Scan each paragraph for these modes:

1. Significance inflation: "至关重要 / 不可忽视 / 深远影响 / 具有重要价值".
2. Synonym cycling: the same object gets 3 or more names in one local context.
3. Rule of three: mechanical three-item bundles or triple-step rhetoric.
4. Copula avoidance: "体现了 / 扮演着…角色 / 起到了…作用" where direct `是` or a concrete verb would be clearer.
5. Vague attribution: "有研究表明 / 学界普遍认为 / 相关研究指出" without a verified source.
6. Formulaic challenge section: "尽管…但仍存在局限性 / 未来研究可以进一步探讨…".
7. Superficial floating analysis: chained `从而 / 进而 / 由此` clauses with little added information.
8. Generic positive conclusion: "具有良好的应用前景 / 提供理论和实验依据 / 现实意义重大".
9. Em dash overuse: multiple `——` in one paragraph.
10. False ranges: "从宏观到微观 / 从理论到实践 / 从基础研究到工程应用".

Also scan AI high-frequency academic fillers such as `此外 / 综上所述 / 值得注意的是 / 提升 / 优化 / 阐述 / 揭示`.

## Revision Moves

Use these moves in order:

1. First round, remove AI traces through deterministic replacements and structure adjustment.
2. Unify core terminology before adding new sentence rhythm.
3. Split long evenly shaped sentences to raise burstiness.
4. Replace vague attribution with verified citations or mark `needs_source`.
5. Replace generic positive endings with concrete claims, limits, or observed conditions.
6. Add at most 1-2 controlled human features per paragraph: observation detail, uncertainty, anomaly note, or limit statement.
7. Re-scan after revision and compare the paragraph risk changes.

## Hard Constraints

These are hard failures, not style preferences:

- vague attribution without a source
- fabricated or unverifiable citation
- fabricated experiment, interview, data, system function, API, table, or screenshot
- generic significance claim used to replace missing evidence
- external detector score presented as a verified fact
- "AI helped me" or workflow traces inside thesis body text
- deliberately adding typos, weird punctuation, slang, or false first-person experience

When a hard constraint appears, do not polish around it. Fix the source/evidence problem or mark it.

## Report Format

Return:

1. overall risk: clear / low / medium / high
2. paragraph findings with pattern labels
3. hard failures: fabricated source risk, vague attribution, generic conclusion, missing evidence
4. suggested revision order
5. whether direct rewriting is safe now
6. whether final paragraph pass is justified

## Rewrite Output Format

When rewriting, return:

1. revised text
2. key changes
3. facts preserved
4. `needs_source` or `needs_evidence` list
5. remaining style risks, if any
6. revision-log entries or a statement that the entries were appended to `paper-context/workflow/revision-log.md`

For final paragraph pass, return paragraph-aligned output:

```text
P001
revised_paragraph:
changes:
preserved_facts:
needs_source:
needs_evidence:
```

## Thesis-Specific Guardrails

- Use "本文" or neutral academic narration by default.
- Use "笔者" only when the school style allows it or the original text already uses it.
- Do not add personal experience, surprise, or uncertainty unless supported by real research notes, data, or project evidence.
- For system-design papers, concrete project facts are better than generic "important significance" claims.
- For literature reviews, style revision must not change author claims or source meanings.
- For full-paper rewriting, keep headings, figure/table references, citations, and numbering stable.
- For AIGC rewriting, every paragraph rewrite must remain traceable to the original paragraph ID, style report finding, and evidence boundary.

## Suggested Prompts

Report first:

```text
Use $thesis-standardizer. Read the chapter draft, run the AIGC style-governance module, and output only a style-risk report first. Do not rewrite yet.
```

Targeted revision:

```text
Use the style-risk report to revise only the high-risk paragraphs. Preserve facts, citations, and thesis voice. Mark unsupported claims as needs_source instead of inventing evidence.
```

Final paragraph pass:

```text
Use $thesis-standardizer，对整篇论文执行 AIGC 最终降低版。先按段落分割并生成 aigc-final-paragraph-pass.md；提示我该流程极度消耗 token；然后逐段改写、逐段记录 facts preserved / needs_source / needs_evidence，最后拼接全文并复查段间衔接。
```

## Source Notes

This module is informed by:

- `xiaofenggan01/aigc-reduce`: three-round reduction protocol, deep AI-pattern audit, and local scan dimensions.
- OpenAI's public note that AI-text classifiers have reliability limits and should not be treated as a sole decision tool.
- Turnitin's guidance that AI indicators support educator judgment rather than automatically determining misconduct.
