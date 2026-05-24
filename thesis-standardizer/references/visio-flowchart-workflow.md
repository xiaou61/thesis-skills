# Visio Flowchart Workflow

Use this workflow when a thesis needs editable Visio `.vsdx` flowcharts.

The style follows common undergraduate thesis examples:

- start/end: terminator shape
- process/input/output: rectangle process shape
- decision: diamond shape
- normal flow: solid arrow connector
- return/error flow: orthogonal loop arrow with a short `是/否` label
- visual style: black line, white fill, compact thesis-friendly layout

## Basic Input

```json
{
  "diagramType": "flowchart",
  "title": "系统登录流程图",
  "layout": {
    "direction": "TB"
  },
  "nodes": [
    {"id": "start", "type": "start", "text": "开始"},
    {"id": "input", "type": "process", "text": "输入账号、密码"},
    {"id": "check_account", "type": "decision", "text": "判断账号是否正确"},
    {"id": "success", "type": "process", "text": "登录成功"},
    {"id": "end", "type": "end", "text": "结束"}
  ],
  "edges": [
    {"from": "start", "to": "input"},
    {"from": "input", "to": "check_account"},
    {"from": "check_account", "to": "success", "label": "是"},
    {"from": "check_account", "to": "input", "label": "否", "route": "back", "side": "right"},
    {"from": "success", "to": "end"}
  ]
}
```

## Layout Hints

The layout script can infer a compact vertical flow from the node order. For more complex business flows, set:

- `rank`: vertical layer for `TB` flow, or horizontal layer for `LR` flow
- `column`: horizontal offset for `TB` flow, or vertical offset for `LR` flow
- `x/y`: exact Visio coordinates when a school template needs manual control
- `route: "back"` with `side: "left"` or `side: "right"` for return arrows

Use `layout.direction: "TB"` for login/add/delete process diagrams and `layout.direction: "LR"` or explicit `rank/column` for broader business-flow diagrams.

## Generate Editable Visio Output

Run from the repository root:

```powershell
python .\thesis-standardizer\scripts\layout_flowchart_diagram.py `
  .\paper-context\evidence\flowchart-model.json `
  --out .\paper-context\evidence\flowchart-model.positioned.json

python .\thesis-standardizer\scripts\check_flowchart_layout.py `
  .\paper-context\evidence\flowchart-model.positioned.json

powershell -ExecutionPolicy Bypass -File .\thesis-standardizer\scripts\generate_visio_flowchart_diagram.ps1 `
  -InputJson .\paper-context\evidence\flowchart-model.positioned.json `
  -OutputVsdx .\thesis-ai-standard\visio\flowchart-diagram.vsdx `
  -OutputPng .\thesis-ai-standard\exports\flowchart-diagram.png
```

The Visio script:

- opens Microsoft Visio through COM automation
- uses `BASFLO_M.VSSX` or `BASFLO_U.VSSX` flowchart masters when available
- falls back to primitive Visio shapes if a master is missing
- writes an editable `.vsdx`
- exports a `.png` preview for Word insertion
- prints a JSON summary with node and edge counts

Use `-Visible -KeepOpen` to watch Visio draw and keep the file open for manual editing.

## Figure Registry

For generated Visio flowcharts, register the figure with:

```yaml
type: "flowchart"
source_kind: "visio"
source_file: "thesis-ai-standard/visio/flowchart-diagram.vsdx"
export_file: "thesis-ai-standard/exports/flowchart-diagram.png"
```

The source `.vsdx` is the editable artifact. The exported `.png` is the figure image used in Word.
