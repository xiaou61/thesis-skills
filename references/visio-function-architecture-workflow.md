# Visio Function Architecture Workflow

Use this workflow when a thesis needs an editable Visio `.vsdx` function architecture or function structure tree, such as `图4-1 系统功能结构图`.

This diagram is different from a technical architecture diagram. It should show:

- one system root box
- optional upper/front-end role group and function leaves
- optional lower/back-end module group
- one or more role/module boxes below the back-end group
- narrow vertical function leaves under each role/module
- black orthogonal tree lines, white fills, compact thesis style

## Basic Input

```json
{
  "diagramType": "function_architecture",
  "systemName": "安徽扶贫惠农公益网站",
  "topGroups": [
    {
      "id": "frontend_user",
      "name": "前台用户",
      "children": ["系统首页", "农产品助销", "扶贫政策", "扶贫成果", "个人中心"]
    }
  ],
  "backendName": "后台模块",
  "bottomGroups": [
    {
      "id": "admin",
      "name": "管理员",
      "children": ["登录", "个人中心", "用户管理", "订单管理", "系统管理"]
    },
    {
      "id": "farmer",
      "name": "贫困农户",
      "children": ["登录", "个人中心", "农产品管理", "订单管理"]
    }
  ]
}
```

Accepted aliases:

- `diagramType`: `function_architecture`, `function_structure`, `module_architecture`, or `architecture`
- upper groups: `topGroups` or `frontendGroups`
- lower groups: `bottomGroups`, `backendGroups`, or `modules`
- group children: `children`, `items`, or `functions`

## Layout Hints

The layout script is optimized for the common undergraduate thesis template style:

- root system box in the center
- top/front-end functions above the root
- back-end group and role/module branches below the root
- narrow function leaves with stacked Chinese characters

Keep each leaf label short. If there are too many bottom functions, split the figure by role or module instead of forcing everything into one figure.

## Thesis Display Guardrails

Function architecture diagrams easily become flat when too many modules are placed in one row. Treat that as a source-layout problem, not a Word scaling problem.

- If a role/module has many leaves, split it into a role/module subfigure.
- If there are many peer modules, create one overview figure plus several module detail figures.
- Do not rely on a universal `14cm x 8cm` OLE display size. Preserve preview aspect ratio when embedding and inspect the fitted dimensions.
- After exporting PNG previews, run:

```powershell
python .\scripts\check_figure_preview_aspects.py .\paper-context\visio-ole-figure-map.json
```

Warnings for very wide/flat previews mean the figure should be split or arranged into more vertical layers before Word production.

## Generate Editable Visio Output

Run from the repository root:

```powershell
python .\scripts\layout_function_architecture_diagram.py `
  .\paper-context\evidence\function-architecture-model.json `
  --out .\paper-context\evidence\function-architecture-model.positioned.json

python .\scripts\check_function_architecture_layout.py `
  .\paper-context\evidence\function-architecture-model.positioned.json

powershell -ExecutionPolicy Bypass -File .\scripts\generate_visio_function_architecture_diagram.ps1 `
  -InputJson .\paper-context\evidence\function-architecture-model.positioned.json `
  -OutputVsdx .\thesis-ai-standard\visio\function-architecture-diagram.vsdx `
  -OutputPng .\thesis-ai-standard\exports\function-architecture-diagram.png
```

The Visio script:

- opens Microsoft Visio through COM automation
- uses `BASIC_M.VSSX` or `BASIC_U.VSSX` rectangle masters when available
- draws tree connectors as editable one-dimensional Visio line shapes
- writes an editable `.vsdx`
- exports a `.png` preview for Word insertion
- prints a JSON summary with node and line counts

Use `-Visible -KeepOpen` to watch Visio draw and keep the file open for manual editing.

## Figure Registry

For generated Visio function architecture diagrams, register the figure with:

```yaml
type: "architecture"
source_kind: "visio"
source_file: "thesis-ai-standard/visio/function-architecture-diagram.vsdx"
export_file: "thesis-ai-standard/exports/function-architecture-diagram.png"
risk_notes: "功能结构图应保留可编辑 Visio 源文件；模块过多时拆分为角色/模块子图"
```

The source `.vsdx` is the editable artifact. The exported `.png` is the figure image used in Word.
