# Thesis Standardizer

一个面向本科系统类毕业论文 / 毕业设计的工具包。

精简目标：基于一个真实程序，抽取证据，生成一篇能自圆其说的论文。

## 最短路径

对 AI 说：

```text
用 thesis-standardizer 基于这个程序生成论文。先抽取项目证据，再补 standard-profile、thesis-ai-spec、figure-registry，然后按第1到第6章生成正文。图表只生成第三章用例图、第四章功能架构图、E-R 图和数据库三线表。AIGC 降低先不要做，除非我单独要求。
```

## 默认流程

1. 有学校 `.docx` 模板就先提取模板字号、页边距、样式、题注和表格规则。
2. 扫描程序，生成 `paper-context/evidence/`。
3. 补三份核心文件：
   - `thesis-ai-standard/templates/standard-profile.yaml`
   - `thesis-ai-standard/templates/thesis-ai-spec.yaml`
   - `thesis-ai-standard/templates/figure-registry.yaml`
4. 按章节生成论文：
   - 第1章：绪论
   - 第2章：相关技术及其在本系统中的应用
   - 第3章：系统分析，用例图
   - 第4章：系统设计与实现，功能架构图、E-R 图、三线表
   - 第5章：测试
   - 第6章：结论
5. 检查证据链、图表清单、引用和 Word 格式风险。

AIGC 降低是独立流程，不默认参与论文生成。

## 核心命令

初始化工作区：

```powershell
python .\thesis-standardizer\scripts\init_thesis_workspace.py .
```

提取学校 Word 模板：

```powershell
python .\thesis-standardizer\scripts\extract_docx_template_profile.py .\school-template.docx --out .\paper-context\template-extract
```

从程序抽取证据：

```powershell
python .\thesis-standardizer\scripts\build_project_evidence.py . --out .\paper-context\evidence
```

检查工作区：

```powershell
python .\thesis-standardizer\scripts\check_thesis_workspace.py .
```

## 图表能力

第三章：

- 用例图：`layout_use_case_diagram.py` -> `check_use_case_layout.py` -> `generate_visio_use_case_diagram.ps1`

第四章：

- 功能架构图：`layout_function_architecture_diagram.py` -> `check_function_architecture_layout.py` -> `generate_visio_function_architecture_diagram.ps1`
- E-R 图：`layout_er_diagram.py` -> `check_er_layout.py` -> `generate_visio_er_diagram.ps1`
- 三线表：优先使用 `vendor/docx-editor-cn/scripts/table.py`

所有图表都应登记到 `figure-registry.yaml`，并保留可编辑源文件。

## 关键原则

- 先证据，后正文。
- 不编造功能、接口、数据库字段、测试结果、截图、参考文献或学校规则。
- 章节内容必须能回到代码、数据库、接口、测试、截图或文献。
- 学校模板和导师要求优先于通用默认值。
- 稳定 `.docx` 不要轻易整篇 markdown round-trip。

## 主要文件

```text
thesis-standardizer/
  SKILL.md
  references/
    thesis-module-workflow.md
    template-extraction-workflow.md
    visio-use-case-workflow.md
    visio-function-architecture-workflow.md
    visio-diagram-workflow.md
    docx-production-rules.md
  scripts/
    init_thesis_workspace.py
    build_project_evidence.py
    extract_docx_template_profile.py
    check_thesis_workspace.py
  assets/thesis-ai-standard/templates/
    standard-profile.yaml
    thesis-ai-spec.yaml
    figure-registry.yaml
```
