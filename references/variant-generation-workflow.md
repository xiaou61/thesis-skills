# 三版论文生成与对比工作流

该工作流用于在不改动大生成器内部逻辑的前提下，把同一论文任务拆成三个独立候选版，并用相同的最终 gate 与对比报告收敛主线程决策。

## 三版矩阵

| 版本 | 目标 | 优先优化 | 主要风险 |
| --- | --- | --- | --- |
| 模板优先版 | 最大限度复现学校 Word 模板 | 组件顺序、标题层级、页边距、题注、三线表、模板差异报告 | 正文和图表扩展可能偏保守 |
| 图表增强版 | 最大限度补齐第3-6章图表闭环 | 图表计划、Visio 源文件、PNG 预览、OLE 嵌入、图表登记 | 图多后更容易触发 OLE、宽高比或正文引用 gate |
| 正文叙事增强版 | 最大限度改善本科论文正文质量 | 章节连贯、论证密度、引用集中、证据边界和论文语气 | 格式和图表数量可能不如前两版 |

## 推荐命令

只创建三版 workspace、brief 和 manifest，不实际生成：

```powershell
python .\scripts\generate_thesis_variants.py
```

调用现有 campus affairs demo 生成器生成三版独立草稿：

```powershell
python .\scripts\generate_thesis_variants.py --run --apply-profile
```

生成后运行最终 DOCX gate：

```powershell
python .\scripts\generate_thesis_variants.py --run --apply-profile --check --expected-visio-ole 8
```

模板优先版需要模板 profile 时：

```powershell
python .\scripts\generate_thesis_variants.py --run --apply-profile --check `
  --template-profile .\paper-context\template-extract\template-profile.json `
  --expected-visio-ole 8
```

如果主线程已有可靠的 PDF 导出命令，可通过模板传入：

```powershell
python .\scripts\generate_thesis_variants.py --run `
  --export-pdf-command "powershell -ExecutionPolicy Bypass -File .\scripts\export_docx_to_pdf.ps1 -Docx '{docx}' -Pdf '{pdf}'"
```

生成或检查后对比三版：

```powershell
python .\scripts\compare_thesis_variants.py .\paper-context\thesis-variants
```

## 输出结构

```text
paper-context/thesis-variants/
  variant-matrix.json
  variant-generation-summary.json
  variant-comparison.md
  variant-comparison.json
  01-template-first/
    variant-brief.md
    variant-manifest.json
    reports/gate-report.txt
  02-figure-enhanced/
    variant-brief.md
    variant-manifest.json
    reports/gate-report.txt
  03-narrative-enhanced/
    variant-brief.md
    variant-manifest.json
    reports/gate-report.txt
```

每个版本必须使用独立 workspace。当前最小脚本通过 `CAMPUS_AFFAIRS_DEMO_WORKSPACE` 调用 `generate_campus_affairs_demo.py`，因此不会覆盖另一个版本的产物。

## 主线程评审顺序

1. 先看 `variant-generation-summary.json`，确认三个版本是否都生成或是否有失败版本。
2. 再看每个版本的 `reports/gate-report.txt`，不要只看 Word 视觉效果。
3. 打开 `variant-comparison.md`，比较 CJK 字数、内容单位、表格数、图片数、VSDX/PNG 数和 gate 失败项。
4. 选择一个主版本作为基线，只从其他版本摘取明确更好的章节、图表或格式修复。
5. 合并后的最终 `.docx` 必须重新运行 `scripts/check_final_thesis_docx.ps1`，旧版本 gate 不能作为合并后交付证据。

## 风险控制

- 三版脚本只负责隔离运行、记录意图、调用现有生成器和检查器，不替代人工/主线程的论文内容判断。
- 如果现有生成器不支持某个优化开关，先用 `--apply-profile` 对生成后的 DOCX 施加保守的版本侧重点：模板优先版强化章节边界，图表增强版强化图表解释，正文叙事增强版强化章节衔接。不要为了三版流程大改生成器内部逻辑。
- PDF 导出不是本仓库当前 gate 的固定入口，只有主线程提供稳定导出命令时才启用。
- `--check` 会调用聚合 gate。若 `.docx` 不存在，脚本会把该版本标记为 `missing_docx_for_gate`，不会伪造通过结果。
