# AIGC Style Governance

Use this module for:

- AIGC reduction
- AI-flavor cleanup
- paragraph-by-paragraph rewriting
- plain Chinese rewriting
- style-risk reports

This is a writing-quality workflow, not a detector-bypass workflow.

## Default Flow

1. Run `scripts/run_aigc_repair_loop.py <draft-file> --workspace <workspace>`.
2. Read:
   - `paper-context/aigc/aigc-repair-loop.md`
   - `paper-context/aigc/aigc-style-report.md`
   - `paper-context/aigc/aigc-revision-plan.md`
3. Round 1: revise only high-risk paragraphs.
4. Run the same loop again.
5. Round 2: revise only remaining high/medium-risk paragraphs.
6. If needed, use `paper-context/aigc/aigc-final-paragraph-pass.md`.
7. Record actual edits in `revision-log.md` / `revision-trace.jsonl`.

## Plain-Language Rule

If the user asks for `大白话`, explain like this:

- `这段像套话`
- `这段像功能清单`
- `这几句长得太整齐`
- `这句像总结腔`

Do not explain with abstract jargon if plain Chinese is enough.

## Final Paragraph Pass

Use this only when the user asks for:

- `AIGC final reduction version`
- `整篇最终降 AIGC`
- `逐段降低`

Required warning:

```text
AIGC 最终降低版会按论文文本分割后逐段处理。每段先修，再本地检测，再补一轮，最后再拼接全文，极度消耗 token。建议只在终稿或外部报告集中命中时使用。
```

Use `aigc-final-paragraph-pass.md` as the work order.

## What To Fix First

Round 1 first:

- vague attribution
- generic positive conclusions
- significance inflation
- heavy template phrases
- rigid list-like paragraphs

Round 2 first:

- paragraphs still high/medium risk after re-check
- paragraphs with stiff rhythm
- paragraphs still reading like summaries instead of explanation

## Hard Rules

- Do not fabricate citations, data, experiments, screenshots, APIs, or project facts.
- Do not present local AIGC estimates as official detector scores.
- Do not jump straight to full free rewriting before the script loop.
- Keep facts, citations, numbering, and chapter role stable.
- Mark unsupported claims as `needs_source` or `needs_evidence`.

## Output Shape

When reporting:

1. which paragraphs are worst
2. why they look AI-written
3. what to fix in round 1
4. what remains for round 2

When rewriting:

1. revised paragraph
2. plain-language change note
3. preserved facts
4. `needs_source` / `needs_evidence`

## Related Files

- `vendor/aigc-reduce/SKILL.md`
- `vendor/aigc-reduce/references/ai-patterns.md`
- `vendor/aigc-reduce/references/replacement-tables.md`
