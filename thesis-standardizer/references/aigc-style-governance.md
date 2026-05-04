# AIGC Style Governance Module

Use this module when the user asks for AIGC reduction, AI-flavor cleanup, Chinese academic humanizing, paragraph-level rewriting, style reports, or thesis prose polishing.

This module follows the working idea of `humanizer-zh-academic`: detect formulaic Chinese academic prose, rewrite under strict evidence constraints, and keep a revision trail. It is an academic writing quality module, not a detector-bypass tool.

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
4. Revise by paragraph priority: high -> medium -> low.
5. Preserve facts, citations, terminology, chapter role, and school-style requirements.
6. Mark unsupported claims as `needs_source` or `needs_evidence`.
7. Return revised text plus a revision log and remaining risks.
8. Append every changed high/medium-risk paragraph to `paper-context/workflow/revision-log.md` and `revision-trace.jsonl`.

If the user provides an external AIGC report, treat it as one signal, not truth. Extract highlighted passages, compare them with the actual prose, then produce a local report.

## Final Paragraph Pass

When the user asks for the "AIGC final reduction version", "整篇最终降 AIGC", "逐段降低", or similar wording, use paragraph-by-paragraph final pass mode.

Command:

```powershell
python .\thesis-standardizer\scripts\analyze_aigc_style.py .\chapter-draft.md --out .\paper-context\aigc\aigc-style-report.md --json-out .\paper-context\aigc\aigc-style-report.json --final-paragraph-pass-out .\paper-context\aigc\aigc-final-paragraph-pass.md
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

## Sixteen Risk Modes

Scan each paragraph for these modes:

1. Macro opening: "随着/近年来/当前/在...背景下" before the real topic appears.
2. Theory-first opening: "基于/依据/根据...理论/框架" as a repetitive first sentence.
3. Summary tail: "综上所述/由此可见/可以看出" without a concrete inference.
4. Case tail: "案例表明/该案例体现" without naming the actual variable or result.
5. Rigid sequence: "首先/其次/再次/最后" used as a mechanical scaffold.
6. Passive analysis shell: "该设计体现了/该方法反映了" instead of direct reasoning.
7. Core-problem shell: "核心问题在于/关键问题是如何" without object, condition, and consequence.
8. Vague attribution: "研究表明/专家认为/相关研究指出" without a verified source.
9. Filler phrase: "值得注意的是/需要指出的是/总体而言" when no information is added.
10. Generic positive conclusion: "具有重要意义/前景广阔/提供新思路" without evidence.
11. Abstract role shell: "扮演重要角色/起到重要作用/作为重要载体".
12. Effect claim without boundary: "提升效率/优化体验/增强能力" without metric, object, or condition.
13. Method shell: "通过采用某方法实现优化" without input, process, and output.
14. Parallel triad: repeated "规范性、科学性、有效性" style lists.
15. Balanced double clause: "不仅...而且..." used to create symmetrical AI-like rhythm.
16. Absolute claim: "显著提升/全面解决/根本解决/完全满足" without evidence.

Also scan:

- excessive bold text in thesis body
- adjacent paragraphs with identical sentence starts
- paragraphs longer than about 520 Chinese characters
- too many clauses with equal length and equal importance

## Revision Moves

Use these moves in order:

1. Start with the actual research object, system module, data source, method condition, or chapter task.
2. Move theory names from the first sentence into the explanation where they are needed.
3. Replace generic summary endings with a concrete inference, limitation, or transition.
4. Break equal-weight enumeration; let the strongest reason carry more space.
5. Replace passive shells with a concrete design, experiment, source, or data reason.
6. Delete filler phrases that do not carry information.
7. Replace vague attribution with a verified citation or mark `needs_source`.
8. Add precise boundaries: sample, data source, project path, method condition, limitation.
9. Use direct predicates instead of "扮演角色/起到作用".
10. Keep academic register; do not make thesis prose chatty or deliberately flawed.

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

- `redbaronyyyyy-eng/humanizer-zh-academic`: Chinese academic humanizer skill with mode-based rewriting, hard constraints, and thesis-oriented output discipline.
- `Yezery/aigc-down-skill`: report-first AIGC style-risk workflow and Chinese academic formulaic-pattern categories.
- OpenAI's public note that AI-text classifiers have reliability limits and should not be treated as a sole decision tool.
- Turnitin's guidance that AI indicators support educator judgment rather than automatically determining misconduct.
- Purdue OWL academic writing guidance on concision, nominalizations, and direct expression.
