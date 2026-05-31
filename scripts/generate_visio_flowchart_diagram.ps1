param(
  [Parameter(Mandatory = $true)]
  [string] $InputJson,

  [Parameter(Mandatory = $true)]
  [string] $OutputVsdx,

  [string] $OutputPng = "",

  [switch] $Visible,

  [switch] $KeepOpen
)

$ErrorActionPreference = "Stop"

function Get-FullPath {
  param([Parameter(Mandatory = $true)] [string] $Path)
  if ([System.IO.Path]::IsPathRooted($Path)) {
    return [System.IO.Path]::GetFullPath($Path)
  }
  return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $Path))
}

function Ensure-ParentDirectory {
  param([Parameter(Mandatory = $true)] [string] $Path)
  $parent = Split-Path -Parent $Path
  if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent | Out-Null
  }
}

function Invariant-Inch {
  param([Parameter(Mandatory = $true)] [double] $Value)
  return ([string]::Format([System.Globalization.CultureInfo]::InvariantCulture, "{0:0.###} in", $Value))
}

function Get-Prop {
  param(
    [object] $Object,
    [Parameter(Mandatory = $true)] [string] $Name,
    [object] $Default = $null
  )
  if ($null -eq $Object) {
    return $Default
  }
  $prop = $Object.PSObject.Properties[$Name]
  if ($null -eq $prop -or $null -eq $prop.Value) {
    return $Default
  }
  return $prop.Value
}

function As-Array {
  param([object] $Value)
  if ($null -eq $Value) {
    return @()
  }
  if ($Value -is [System.Array]) {
    return @($Value)
  }
  return @($Value)
}

function As-Text {
  param([object] $Value, [string] $Default = "")
  if ($null -eq $Value) {
    return $Default
  }
  $text = [string] $Value
  if ([string]::IsNullOrWhiteSpace($text)) {
    return $Default
  }
  return $text.Trim()
}

function New-VisioApplication {
  param([switch] $Show)
  if ($Show) {
    $app = New-Object -ComObject Visio.Application
    $app.Visible = $true
    return $app
  }
  return New-Object -ComObject Visio.InvisibleApp
}

function Open-FirstStencil {
  param(
    [Parameter(Mandatory = $true)] $Visio,
    [Parameter(Mandatory = $true)] [string[]] $Names
  )
  foreach ($name in $Names) {
    try {
      return $Visio.Documents.OpenEx($name, 66)
    } catch {
      Write-Verbose "Stencil not available: $name"
    }
  }
  return $null
}

function Get-FirstMaster {
  param(
    $Stencil,
    [Parameter(Mandatory = $true)] [string[]] $Names
  )
  if ($null -eq $Stencil) {
    return $null
  }
  foreach ($name in $Names) {
    try {
      return $Stencil.Masters.ItemU($name)
    } catch {
      try {
        return $Stencil.Masters.Item($name)
      } catch {
        Write-Verbose "Master not available: $name"
      }
    }
  }
  return $null
}

function Set-CellFormula {
  param(
    [Parameter(Mandatory = $true)] $Shape,
    [Parameter(Mandatory = $true)] [string] $CellName,
    [Parameter(Mandatory = $true)] [string] $Formula
  )
  try {
    if ($Shape.CellExistsU($CellName, 0) -ne 0) {
      $Shape.CellsU($CellName).FormulaU = $Formula
    }
  } catch {
    Write-Verbose "Could not set $CellName"
  }
}

function Set-ShapeSize {
  param(
    [Parameter(Mandatory = $true)] $Shape,
    [Parameter(Mandatory = $true)] [double] $Width,
    [Parameter(Mandatory = $true)] [double] $Height
  )
  Set-CellFormula -Shape $Shape -CellName "Width" -Formula (Invariant-Inch $Width)
  Set-CellFormula -Shape $Shape -CellName "Height" -Formula (Invariant-Inch $Height)
}

function Set-TextStyle {
  param(
    [Parameter(Mandatory = $true)] $Shape,
    [double] $Size = 10.5,
    [int] $Bold = 0
  )
  Set-CellFormula -Shape $Shape -CellName "Char.Size" -Formula "$Size pt"
  Set-CellFormula -Shape $Shape -CellName "Char.Color" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Shape -CellName "Char.Style" -Formula "$Bold"
  Set-CellFormula -Shape $Shape -CellName "Para.HorzAlign" -Formula "1"
  Set-CellFormula -Shape $Shape -CellName "VerticalAlign" -Formula "1"
}

function Set-BlackWhiteShape {
  param(
    [Parameter(Mandatory = $true)] $Shape,
    [double] $LineWeight = 0.75,
    [int] $Bold = 0
  )
  Set-CellFormula -Shape $Shape -CellName "FillPattern" -Formula "1"
  Set-CellFormula -Shape $Shape -CellName "FillForegnd" -Formula "RGB(255,255,255)"
  Set-CellFormula -Shape $Shape -CellName "LineColor" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Shape -CellName "LineWeight" -Formula "$LineWeight pt"
  Set-TextStyle -Shape $Shape -Bold $Bold
}

function Set-PageSize {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [double] $Width,
    [double] $Height
  )
  Set-CellFormula -Shape $Page.PageSheet -CellName "PageWidth" -Formula (Invariant-Inch $Width)
  Set-CellFormula -Shape $Page.PageSheet -CellName "PageHeight" -Formula (Invariant-Inch $Height)
}

function Add-Title {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [string] $Title,
    [double] $PageWidth,
    [double] $PageHeight
  )
  if (-not $Title) {
    return
  }
  $shape = $Page.DrawRectangle(0.35, $PageHeight - 0.4, $PageWidth - 0.35, $PageHeight - 0.06)
  $shape.Text = $Title
  Set-CellFormula -Shape $shape -CellName "LinePattern" -Formula "0"
  Set-CellFormula -Shape $shape -CellName "FillPattern" -Formula "0"
  Set-TextStyle -Shape $shape -Size 13 -Bold 1
}

function Add-Label {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [string] $Text,
    [double] $X,
    [double] $Y,
    [double] $Width = 0.34,
    [double] $Height = 0.2
  )
  if (-not $Text) {
    return $null
  }
  if ($PSBoundParameters.ContainsKey("Width") -eq $false) {
    $Width = [Math]::Max(0.34, [Math]::Min(0.9, 0.16 + ($Text.Length * 0.16)))
  }
  $label = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
  $label.Text = $Text
  Set-CellFormula -Shape $label -CellName "LinePattern" -Formula "0"
  Set-CellFormula -Shape $label -CellName "FillPattern" -Formula "0"
  Set-TextStyle -Shape $label -Size 9 -Bold 0
  return $label
}

function New-FlowShape {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [string] $Kind,
    [string] $Text,
    [double] $X,
    [double] $Y,
    [double] $Width,
    [double] $Height,
    $ProcessMaster,
    $DecisionMaster,
    $StartEndMaster,
    $DatabaseMaster,
    $DocumentMaster
  )
  $kindLower = $Kind.ToLowerInvariant()
  $master = $ProcessMaster
  if ($kindLower -in @("start", "end", "terminator")) {
    $master = $StartEndMaster
  } elseif ($kindLower -eq "decision") {
    $master = $DecisionMaster
  } elseif ($kindLower -eq "database") {
    $master = $DatabaseMaster
  } elseif ($kindLower -eq "document") {
    $master = $DocumentMaster
  }

  if ($null -ne $master) {
    $shape = $Page.Drop($master, $X, $Y)
    Set-ShapeSize -Shape $shape -Width $Width -Height $Height
  } else {
    if ($kindLower -eq "decision") {
      $shape = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
      Set-CellFormula -Shape $shape -CellName "Angle" -Formula "45 deg"
    } elseif ($kindLower -in @("start", "end", "terminator")) {
      $shape = $Page.DrawOval($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
    } else {
      $shape = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
    }
  }
  $shape.Text = $Text
  Set-BlackWhiteShape -Shape $shape -Bold 0
  return $shape
}

function Get-GluePointToward {
  param(
    [Parameter(Mandatory = $true)] $From,
    [Parameter(Mandatory = $true)] $To
  )
  try {
    $fromX = [double] $From.CellsU("PinX").ResultIU
    $fromY = [double] $From.CellsU("PinY").ResultIU
    $toX = [double] $To.CellsU("PinX").ResultIU
    $toY = [double] $To.CellsU("PinY").ResultIU
  } catch {
    return @{ X = 0.5; Y = 0.5 }
  }
  $dx = $toX - $fromX
  $dy = $toY - $fromY
  if ([Math]::Abs($dx) -ge [Math]::Abs($dy)) {
    if ($dx -ge 0) {
      return @{ X = 1.0; Y = 0.5 }
    }
    return @{ X = 0.0; Y = 0.5 }
  }
  if ($dy -ge 0) {
    return @{ X = 0.5; Y = 1.0 }
  }
  return @{ X = 0.5; Y = 0.0 }
}

function Connect-FlowShapes {
  param(
    [Parameter(Mandatory = $true)] $Page,
    $ConnectorMaster,
    [Parameter(Mandatory = $true)] $From,
    [Parameter(Mandatory = $true)] $To,
    [string] $Label = "",
    [switch] $Dashed
  )
  $fromPoint = Get-GluePointToward -From $From -To $To
  $toPoint = Get-GluePointToward -From $To -To $From
  if ($null -ne $ConnectorMaster) {
    $line = $Page.Drop($ConnectorMaster, 0, 0)
  } else {
    $line = $Page.DrawLine(0, 0, 1, 1)
  }
  $line.CellsU("BeginX").GlueToPos($From, $fromPoint.X, $fromPoint.Y)
  $line.CellsU("EndX").GlueToPos($To, $toPoint.X, $toPoint.Y)
  $line.Text = $Label
  Set-CellFormula -Shape $line -CellName "LineColor" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $line -CellName "LineWeight" -Formula "0.75 pt"
  Set-CellFormula -Shape $line -CellName "BeginArrow" -Formula "0"
  Set-CellFormula -Shape $line -CellName "EndArrow" -Formula "4"
  Set-CellFormula -Shape $line -CellName "ShapeRouteStyle" -Formula "2"
  Set-CellFormula -Shape $line -CellName "ConLineRouteExt" -Formula "1"
  if ($Dashed) {
    Set-CellFormula -Shape $line -CellName "LinePattern" -Formula "2"
  }
  Set-TextStyle -Shape $line -Size 9 -Bold 0
  return $line
}

function Set-FlowLineStyle {
  param(
    [Parameter(Mandatory = $true)] $Line,
    [switch] $Arrow,
    [switch] $Dashed
  )
  Set-CellFormula -Shape $Line -CellName "LineColor" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Line -CellName "LineWeight" -Formula "0.75 pt"
  Set-CellFormula -Shape $Line -CellName "BeginArrow" -Formula "0"
  if ($Arrow) {
    Set-CellFormula -Shape $Line -CellName "EndArrow" -Formula "4"
  } else {
    Set-CellFormula -Shape $Line -CellName "EndArrow" -Formula "0"
  }
  if ($Dashed) {
    Set-CellFormula -Shape $Line -CellName "LinePattern" -Formula "2"
  }
}

function Get-PointValue {
  param(
    [Parameter(Mandatory = $true)] $Point,
    [Parameter(Mandatory = $true)] [string] $Name
  )
  $value = Get-Prop $Point $Name $null
  if ($null -eq $value) {
    throw "Route point is missing '$Name'."
  }
  return [double] $value
}

function Get-RoutePoints {
  param([object] $Edge)
  $points = @()
  foreach ($point in @(As-Array (Get-Prop $Edge "points"))) {
    try {
      $points += [pscustomobject]@{
        X = Get-PointValue -Point $point -Name "x"
        Y = Get-PointValue -Point $point -Name "y"
      }
    } catch {
      Write-Verbose "Skipped invalid route point: $_"
    }
  }
  return @($points)
}

function Clamp-Unit {
  param([double] $Value)
  if ($Value -lt 0.0) { return 0.0 }
  if ($Value -gt 1.0) { return 1.0 }
  return $Value
}

function Get-GluePointFromCoordinate {
  param(
    [Parameter(Mandatory = $true)] $Shape,
    [double] $X,
    [double] $Y
  )
  $pinX = [double] $Shape.CellsU("PinX").ResultIU
  $pinY = [double] $Shape.CellsU("PinY").ResultIU
  $width = [double] $Shape.CellsU("Width").ResultIU
  $height = [double] $Shape.CellsU("Height").ResultIU
  if ($width -le 0 -or $height -le 0) {
    return @{ X = 0.5; Y = 0.5 }
  }
  return @{
    X = Clamp-Unit (($X - ($pinX - ($width / 2))) / $width)
    Y = Clamp-Unit (($Y - ($pinY - ($height / 2))) / $height)
  }
}

function Add-RouteLabel {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [string] $Text,
    [Parameter(Mandatory = $true)] [object[]] $Points
  )
  if (-not $Text -or $Points.Count -lt 2) {
    return
  }
  $segmentCount = $Points.Count - 1
  $index = [Math]::Max(0, [Math]::Min($segmentCount - 1, [int] [Math]::Floor($segmentCount / 2)))
  $a = $Points[$index]
  $b = $Points[$index + 1]
  Add-Label -Page $Page -Text $Text -X (($a.X + $b.X) / 2) -Y (($a.Y + $b.Y) / 2) | Out-Null
}

function Connect-RoutedEdge {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $From,
    [Parameter(Mandatory = $true)] $To,
    [Parameter(Mandatory = $true)] [object[]] $Points,
    [string] $Label = "",
    [switch] $Dashed
  )
  if ($Points.Count -lt 2) {
    return @()
  }
  $segments = @()
  for ($idx = 0; $idx -lt ($Points.Count - 1); $idx += 1) {
    $a = $Points[$idx]
    $b = $Points[$idx + 1]
    if ([Math]::Abs($a.X - $b.X) -lt 0.001 -and [Math]::Abs($a.Y - $b.Y) -lt 0.001) {
      continue
    }
    $line = $Page.DrawLine($a.X, $a.Y, $b.X, $b.Y)
    Set-FlowLineStyle -Line $line -Arrow:($idx -eq ($Points.Count - 2)) -Dashed:$Dashed
    if ($idx -eq 0) {
      $fromPoint = Get-GluePointFromCoordinate -Shape $From -X $a.X -Y $a.Y
      try { $line.CellsU("BeginX").GlueToPos($From, $fromPoint.X, $fromPoint.Y) } catch {}
    }
    if ($idx -eq ($Points.Count - 2)) {
      $toPoint = Get-GluePointFromCoordinate -Shape $To -X $b.X -Y $b.Y
      try { $line.CellsU("EndX").GlueToPos($To, $toPoint.X, $toPoint.Y) } catch {}
    }
    $segments += $line
  }
  Add-RouteLabel -Page $Page -Text $Label -Points $Points
  return @($segments)
}

function Connect-BackEdge {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $From,
    [Parameter(Mandatory = $true)] $To,
    [string] $Side = "right",
    [string] $Label = "",
    [switch] $Dashed
  )
  $fromX = [double] $From.CellsU("PinX").ResultIU
  $fromY = [double] $From.CellsU("PinY").ResultIU
  $fromW = [double] $From.CellsU("Width").ResultIU
  $toX = [double] $To.CellsU("PinX").ResultIU
  $toY = [double] $To.CellsU("PinY").ResultIU
  $toW = [double] $To.CellsU("Width").ResultIU
  $sideSign = 1.0
  if ($Side.ToLowerInvariant() -eq "left") {
    $sideSign = -1.0
  }
  $fromEdgeX = $fromX + ($sideSign * $fromW / 2)
  $toEdgeX = $toX + ($sideSign * $toW / 2)
  if ($sideSign -gt 0) {
    $outerX = [Math]::Max($fromEdgeX, $toEdgeX) + 0.38
  } else {
    $outerX = [Math]::Min($fromEdgeX, $toEdgeX) - 0.38
  }
  $seg1 = $Page.DrawLine($fromEdgeX, $fromY, $outerX, $fromY)
  $seg2 = $Page.DrawLine($outerX, $fromY, $outerX, $toY)
  $seg3 = $Page.DrawLine($outerX, $toY, $toEdgeX, $toY)
  Set-FlowLineStyle -Line $seg1 -Dashed:$Dashed
  Set-FlowLineStyle -Line $seg2 -Dashed:$Dashed
  Set-FlowLineStyle -Line $seg3 -Arrow -Dashed:$Dashed
  Add-Label -Page $Page -Text $Label -X $outerX -Y (($fromY + $toY) / 2) | Out-Null
  return @($seg1, $seg2, $seg3)
}

function Render-FlowchartDiagram {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $Diagram,
    $ProcessMaster,
    $DecisionMaster,
    $StartEndMaster,
    $DatabaseMaster,
    $DocumentMaster,
    $ConnectorMaster
  )
  $layout = Get-Prop $Diagram "layout"
  $pageWidth = [double] (Get-Prop $layout "pageWidth" 4.2)
  $pageHeight = [double] (Get-Prop $layout "pageHeight" 5.2)
  Set-PageSize -Page $Page -Width $pageWidth -Height $pageHeight

  if ([bool] (Get-Prop $layout "showTitle" $false)) {
    Add-Title -Page $Page -Title (As-Text (Get-Prop $Diagram "title")) -PageWidth $pageWidth -PageHeight $pageHeight
  }

  $nodeShapes = @{}
  foreach ($node in @(As-Array (Get-Prop $Diagram "nodes"))) {
    $id = As-Text (Get-Prop $node "id")
    if (-not $id) {
      continue
    }
    $shape = New-FlowShape -Page $Page -Kind (As-Text (Get-Prop $node "type") "process") -Text (As-Text (Get-Prop $node "text") $id) -X ([double] (Get-Prop $node "x")) -Y ([double] (Get-Prop $node "y")) -Width ([double] (Get-Prop $node "width" 1.35)) -Height ([double] (Get-Prop $node "height" 0.46)) -ProcessMaster $ProcessMaster -DecisionMaster $DecisionMaster -StartEndMaster $StartEndMaster -DatabaseMaster $DatabaseMaster -DocumentMaster $DocumentMaster
    $nodeShapes[$id] = $shape
  }

  $edgeCount = 0
  $backEdgeIndex = 0
  foreach ($edge in @(As-Array (Get-Prop $Diagram "edges"))) {
    $fromId = As-Text (Get-Prop $edge "from")
    $toId = As-Text (Get-Prop $edge "to")
    if ($nodeShapes.ContainsKey($fromId) -and $nodeShapes.ContainsKey($toId)) {
      $dashed = [bool] (Get-Prop $edge "dashed" $false)
      $route = (As-Text (Get-Prop $edge "route")).ToLowerInvariant()
      $points = Get-RoutePoints -Edge $edge
      if ($points.Count -ge 2) {
        Connect-RoutedEdge -Page $Page -From $nodeShapes[$fromId] -To $nodeShapes[$toId] -Points $points -Label (As-Text (Get-Prop $edge "label")) -Dashed:$dashed | Out-Null
      } else {
        $fromY = [double] $nodeShapes[$fromId].CellsU("PinY").ResultIU
        $toY = [double] $nodeShapes[$toId].CellsU("PinY").ResultIU
        $isBackEdge = $route -in @("back", "loop", "return") -or ($toY -gt ($fromY + 0.05))
        if ($isBackEdge) {
        $side = (As-Text (Get-Prop $edge "side"))
        if (-not $side) {
          $side = if (($backEdgeIndex % 2) -eq 0) { "right" } else { "left" }
        }
        Connect-BackEdge -Page $Page -From $nodeShapes[$fromId] -To $nodeShapes[$toId] -Side $side -Label (As-Text (Get-Prop $edge "label")) -Dashed:$dashed | Out-Null
        $backEdgeIndex += 1
        } else {
          Connect-FlowShapes -Page $Page -ConnectorMaster $ConnectorMaster -From $nodeShapes[$fromId] -To $nodeShapes[$toId] -Label (As-Text (Get-Prop $edge "label")) -Dashed:$dashed | Out-Null
        }
      }
      $edgeCount += 1
    } else {
      Write-Warning "Skipped edge because it references unknown nodes: $fromId -> $toId"
    }
  }

  return [pscustomobject]@{ Nodes = $nodeShapes.Keys.Count; Edges = $edgeCount }
}

$inputFullPath = Get-FullPath $InputJson
$outputVsdxFullPath = Get-FullPath $OutputVsdx
if (-not $OutputPng) {
  $OutputPng = [System.IO.Path]::ChangeExtension($outputVsdxFullPath, ".png")
}
$outputPngFullPath = Get-FullPath $OutputPng

if (-not (Test-Path -LiteralPath $inputFullPath)) {
  throw "Input JSON does not exist: $inputFullPath"
}

Ensure-ParentDirectory $outputVsdxFullPath
Ensure-ParentDirectory $outputPngFullPath

$diagram = Get-Content -LiteralPath $inputFullPath -Raw -Encoding UTF8 | ConvertFrom-Json
$diagramType = (As-Text (Get-Prop $diagram "diagramType") "flowchart").ToLowerInvariant()
if ($diagramType -notin @("flowchart", "workflow", "business_flow", "algorithm_flow")) {
  throw "Unsupported diagramType '$diagramType'. Use 'flowchart'."
}

$visio = $null
$doc = $null
$stencil = $null
try {
  $visio = New-VisioApplication -Show:$Visible
  try {
    $visio.AlertResponse = 7
  } catch {
    Write-Verbose "Could not set AlertResponse."
  }
  $doc = $visio.Documents.Add("")
  $page = $visio.ActivePage
  $page.Name = "Flowchart"

  $stencil = Open-FirstStencil -Visio $visio -Names @("BASFLO_M.VSSX", "BASFLO_U.VSSX", "BASIC_M.VSSX", "BASIC_U.VSSX")
  $processMaster = Get-FirstMaster -Stencil $stencil -Names @("Process", "流程", "Rectangle", "矩形")
  $decisionMaster = Get-FirstMaster -Stencil $stencil -Names @("Decision", "判定", "Diamond", "菱形")
  $startEndMaster = Get-FirstMaster -Stencil $stencil -Names @("Start/End", "开始/结束", "Terminator", "Ellipse", "椭圆形")
  $databaseMaster = Get-FirstMaster -Stencil $stencil -Names @("Database", "数据库", "Can")
  $documentMaster = Get-FirstMaster -Stencil $stencil -Names @("Document", "文档")
  $connectorMaster = Get-FirstMaster -Stencil $stencil -Names @("Dynamic connector", "动态连接线")

  $counts = Render-FlowchartDiagram -Page $page -Diagram $diagram -ProcessMaster $processMaster -DecisionMaster $decisionMaster -StartEndMaster $startEndMaster -DatabaseMaster $databaseMaster -DocumentMaster $documentMaster -ConnectorMaster $connectorMaster

  if (Test-Path -LiteralPath $outputVsdxFullPath) {
    Remove-Item -LiteralPath $outputVsdxFullPath -Force
  }
  if (Test-Path -LiteralPath $outputPngFullPath) {
    Remove-Item -LiteralPath $outputPngFullPath -Force
  }
  $doc.SaveAs($outputVsdxFullPath) | Out-Null
  $page.Export($outputPngFullPath) | Out-Null

  [pscustomobject]@{
    input = $inputFullPath
    vsdx = $outputVsdxFullPath
    png = $outputPngFullPath
    diagramType = $diagramType
    nodes = $counts.Nodes
    edges = $counts.Edges
    stencil = if ($null -ne $stencil) { $stencil.Name } else { "primitive-fallback" }
    processMaster = if ($null -ne $processMaster) { $processMaster.NameU } else { "DrawRectangle" }
    decisionMaster = if ($null -ne $decisionMaster) { $decisionMaster.NameU } else { "RotatedRectangle" }
    startEndMaster = if ($null -ne $startEndMaster) { $startEndMaster.NameU } else { "DrawOval" }
    connectorMaster = if ($null -ne $connectorMaster) { $connectorMaster.NameU } else { "DrawLine" }
  } | ConvertTo-Json -Depth 4
} finally {
  if ($null -ne $stencil) {
    try { $stencil.Close() | Out-Null } catch {}
  }
  if ($null -ne $doc -and -not ($Visible -and $KeepOpen)) {
    try { $doc.Close() | Out-Null } catch {}
  }
  if ($null -ne $visio -and -not ($Visible -and $KeepOpen)) {
    try { $visio.Quit() | Out-Null } catch {}
  }
}
