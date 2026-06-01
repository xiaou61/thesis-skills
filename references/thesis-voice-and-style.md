# Thesis Voice And Style

Use this before generating, rewriting, or expanding thesis prose.

## Goal

The final thesis body must read like a student thesis, not an assistant work log,
source-code audit, or delivery report.

Internal workspace files may record source evidence, missing materials, and
verification notes. The thesis body should present the system, design,
implementation, and test result directly.

## Preferred Voice

Use neutral academic wording:

- `本文设计并实现了……`
- `本系统采用……`
- `该模块主要完成……`
- `为了保证……，系统……`
- `测试结果表明……`
- `综上所述……`

## Forbidden In Thesis Body

Do not leak the drafting process, prompt process, source-feeding process, or
quality-audit process into the final paper.

Forbidden examples:

- `根据现有代码……`
- `根据项目源码……`
- `根据 README 和 PRD……`
- `当前材料只提供……`
- `当前可读取项目……`
- `从代码证据看……`
- `本文不编造……`
- `待补真实程序截图`
- `占位图`
- local file paths such as `D:\...`
- source file names such as `init.sql`, `pom.xml`, or `application.yml` in normal prose

## Rewrite Pattern

Bad:

`根据项目源码和 SQL 脚本可知，系统已经完成主要后端接口。`

Good:

`系统已完成主要后端接口和数据库设计，能够为校园事务管理提供基础业务支撑。`

Bad:

`当前材料未提供前端截图，因此第五章保留截图占位。`

Good:

`系统运行截图用于展示主要功能在页面端的实际效果。本文按照登录、首页、请假申请、报修处理和活动报名五个场景安排运行效果图。`

Bad:

`从代码证据看，多个接口进行了角色判断。`

Good:

`权限控制不能只依赖前端隐藏按钮，还需要在后端接口和业务服务中读取当前用户角色并进行判断。`

## Final Gate

Run:

```powershell
python .\scripts\check_docx_thesis_voice.py .\path\to\final-paper.docx
```

The aggregate final gate also runs this check.
