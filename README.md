# 论文标准化 Skill

这是一个面向本科系统设计类论文的 Codex skill。它的目标很简单：基于一个真实程序或项目，把代码、数据库、接口、截图、测试材料和学校模板整理成一篇证据链完整、格式可追溯的毕业论文。

当前主路径适合软件系统、网站、小程序、管理系统、物联网平台等“设计与实现”类题目。其它论文类型可以借用部分模板，但不是默认工作流。

## 核心原则

- 先证据，后正文：不要直接从空泛论文话术开始写。
- 不编造系统功能、数据库字段、接口路径、测试结果、截图来源、参考文献和学校规则。
- 学校 `.docx` 模板、导师要求和任务书优先于通用默认值。
- 图、表、公式、截图都要有来源文件、导出文件、正文首次引用位置和状态记录。
- 结构性图优先保留 Visio `.vsdx` 可编辑源文件。

## 推荐流程

1. 提取学校模板

   ```powershell
   python .\scripts\extract_docx_template_profile.py .\school-template.docx --out .\paper-context\template-extract
   python .\scripts\generate_template_rule_overrides.py .\paper-context\template-extract\template-profile.json --out .\paper-context\template-extract\template-rule-overrides.yaml
   ```

2. 初始化或检查论文工作区

   ```powershell
   python .\scripts\init_thesis_workspace.py .\thesis-ai-standard
   python .\scripts\check_thesis_workspace.py .\thesis-ai-standard
   ```

3. 扫描真实项目证据

   ```powershell
   python .\scripts\build_project_evidence.py <project-dir> --out .\paper-context\evidence
   ```

4. 填写三个核心文件

   - `thesis-ai-standard/templates/standard-profile.yaml`
   - `thesis-ai-standard/templates/thesis-ai-spec.yaml`
   - `thesis-ai-standard/templates/figure-registry.yaml`

5. 按章节生成正文、图表和检查报告。

## 章节模块

| 章节 | 重点 | 典型产物 |
| --- | --- | --- |
| 第1章 绪论 | 背景、意义、研究现状、研究内容、论文结构 | 引用密集段落、选题依据 |
| 第2章 相关技术 | 技术介绍及其在本系统中的应用 | 技术栈说明、引用 |
| 第3章 系统分析 | 可行性、角色、功能需求、非功能需求、用例分析 | Visio 用例图 |
| 第4章 系统设计与实现 | 功能结构、数据库概念设计、数据库表设计、关键模块实现 | 功能架构图、ER 总图、单实体 ER 图、数据库三线表 |
| 第5章 系统测试 | 测试环境、测试方法、测试用例、测试结果 | 测试用例表、截图或日志证据 |
| 第6章 结论与展望 | 完成内容、不足、未来工作 | 总结段落 |

第1章到第3章是主要引用聚集区。第4章优先写真实设计与实现，不把引用硬塞进代码或数据库说明里。

## 第四章数据库资产

第四章不能静默跳过数据库设计。如果存在实体类、SQL、迁移文件、数据库截图或用户提供的表结构，需要生成完整数据库资产：

- 总体 E-R 图
- 核心实体的单实体 E-R 图
- 每个论文范围内数据表的三线表
- 图表登记片段
- 数据库设计正文草稿片段

输入模型示例：

```yaml
entities:
  - id: user
    name: 用户
    table: user
    purpose: 存储系统用户账号、联系方式和状态
    fields:
      - {name: id, type: bigint, key: true, nullable: false, description: 用户编号}
      - {name: username, type: varchar(50), nullable: false, description: 用户账号}
relationships:
  - {name: 下单, from: user, to: order, fromCardinality: "1", toCardinality: "m"}
```

生成命令：

```powershell
python .\scripts\build_chapter4_database_assets.py .\paper-context\evidence\database-design-model.yaml --out .\paper-context\database-design
```

生成后继续对 ER JSON 做布局、碰撞检查和 Visio 导出：

```powershell
python .\scripts\layout_er_diagram.py .\paper-context\database-design\er\er-overview.json --out .\paper-context\database-design\er\er-overview.positioned.json
python .\scripts\check_er_layout.py .\paper-context\database-design\er\er-overview.positioned.json

powershell -ExecutionPolicy Bypass -File .\scripts\generate_visio_er_diagram.ps1 `
  -InputJson .\paper-context\database-design\er\er-overview.positioned.json `
  -OutputVsdx .\paper-context\figures\figure-4-2-er-overview.vsdx `
  -OutputPng .\paper-context\figures\figure-4-2-er-overview.png
```

总 E-R 图默认限制为 8 个实体、8 条关系、每个实体 3 个代表属性。完整字段放到单实体 E-R 图和数据库三线表中。

## Visio 图能力

本 skill 使用 Microsoft Visio COM 自动生成可编辑 `.vsdx`，并导出 `.png` 供 Word 插入。

| 图类型 | 参考流程 | 主要脚本 |
| --- | --- | --- |
| 用例图 | `references/visio-use-case-workflow.md` | `layout_use_case_diagram.py`, `generate_visio_use_case_diagram.ps1` |
| 功能架构图 | `references/visio-function-architecture-workflow.md` | `layout_function_architecture_diagram.py`, `generate_visio_function_architecture_diagram.ps1` |
| E-R 图 | `references/visio-diagram-workflow.md` | `layout_er_diagram.py`, `generate_visio_er_diagram.ps1` |
| 流程图 | `references/visio-flowchart-workflow.md` | `layout_flowchart_diagram.py`, `generate_visio_flowchart_diagram.ps1` |

每类图都有对应的 `check_*_layout.py`，导出前应先检查布局。

## 目录说明

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   └── thesis-ai-standard/
├── references/
│   ├── thesis-module-workflow.md
│   ├── chapter-4-database-workflow.md
│   ├── docx-production-rules.md
│   └── visio-*.md
└── scripts/
    ├── build_project_evidence.py
    ├── build_chapter4_database_assets.py
    ├── check_thesis_workspace.py
    ├── layout_*_diagram.py
    └── generate_visio_*_diagram.ps1
```

`tmp/` 是本地 demo 和临时产物目录，不应提交。

## 验证

提交前建议运行：

```powershell
python C:\Users\Lenovo\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
python .\scripts\check_thesis_workspace.py .\assets\thesis-ai-standard
git diff --check
```

模板目录里的 `paper.title still looks unfilled` 属于占位模板的预期 warning，不代表 skill 失败。

