# Visio Use-Case Diagram Workflow

Use this workflow when a thesis needs editable Visio `.vsdx` use-case diagrams.

The style follows common undergraduate thesis examples:

- actor: stick figure with actor name below
- use case: oval with bold text
- association: solid line with an arrow toward the use case, matching many local thesis samples
- system boundary: optional rectangle around system use cases
- dependency/include/extend: dashed arrow between use cases

## Single Actor Use-Case Input

```json
{
  "diagramType": "use_case",
  "title": "管理员用例图",
  "layout": {
    "mode": "single_actor_radial"
  },
  "actors": [
    {
      "id": "admin",
      "name": "管理员",
      "useCases": [
        "系统首页",
        "用户管理",
        "订单管理"
      ]
    }
  ]
}
```

Use `single_actor_left` when one actor should stay on the left and all use cases should be arranged on the right.
Use `single_actor_radial` when the actor should stay in the middle and use cases should be split left and right.

## System Boundary Input

```json
{
  "diagramType": "use_case",
  "title": "系统通用功能用例图",
  "system": {
    "name": "",
    "showBoundary": true
  },
  "layout": {
    "mode": "boundary"
  },
  "actors": [
    {
      "id": "admin",
      "name": "管理员",
      "useCases": [{"id": "login", "name": "登录"}]
    },
    {
      "id": "user",
      "name": "用户",
      "useCases": [{"id": "login", "name": "登录"}]
    }
  ],
  "useCases": [
    {"id": "login", "name": "登录", "primary": true},
    {"id": "admin_main", "name": "管理员主界面"},
    {"id": "user_main", "name": "用户主界面"}
  ],
  "dependencies": [
    {"from": "login", "to": "admin_main"},
    {"from": "login", "to": "user_main"}
  ]
}
```

When `system.name` is empty, the boundary is drawn without a label. Omit `system.name` to use the default label `系统`.

## Generate Editable Visio Output

Run from the repository root:

```powershell
python .\scripts\layout_use_case_diagram.py `
  .\paper-context\evidence\use-case-model.json `
  --out .\paper-context\evidence\use-case-model.positioned.json

python .\scripts\check_use_case_layout.py `
  .\paper-context\evidence\use-case-model.positioned.json

powershell -ExecutionPolicy Bypass -File .\scripts\generate_visio_use_case_diagram.ps1 `
  -InputJson .\paper-context\evidence\use-case-model.positioned.json `
  -OutputVsdx .\thesis-ai-standard\visio\use-case-diagram.vsdx `
  -OutputPng .\thesis-ai-standard\exports\use-case-diagram.png
```

The Visio script:

- opens Microsoft Visio through COM automation
- draws editable Visio primitives for actors, ovals, boundaries, and connectors
- uses the basic Visio ellipse master when available
- writes an editable `.vsdx`
- exports a `.png` preview for Word insertion
- prints a JSON summary with actor, use-case, association, and dependency counts

Use `-Visible -KeepOpen` to watch Visio draw and keep the file open for manual editing.

## Figure Registry

For generated Visio use-case diagrams, register the figure with:

```yaml
type: "use_case"
source_kind: "visio"
source_file: "thesis-ai-standard/visio/use-case-diagram.vsdx"
export_file: "thesis-ai-standard/exports/use-case-diagram.png"
```

The source `.vsdx` is the editable artifact. The exported `.png` is the figure image used in Word.
