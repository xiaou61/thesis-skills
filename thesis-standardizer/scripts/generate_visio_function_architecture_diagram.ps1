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
    [double] $Size = 9.5,
    [int] $Bold = 0
  )
  Set-CellFormula -Shape $Shape -CellName "Char.Size" -Formula "$Size pt"
  Set-CellFormula -Shape $Shape -CellName "Char.Color" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Shape -CellName "Char.Style" -Formula "$Bold"
  Set-CellFormula -Shape $Shape -CellName "Para.HorzAlign" -Formula "1"
  Set-CellFormula -Shape $Shape -CellName "VerticalAlign" -Formula "1"
  Set-CellFormula -Shape $Shape -CellName "LeftMargin" -Formula "0.02 in"
  Set-CellFormula -Shape $Shape -CellName "RightMargin" -Formula "0.02 in"
  Set-CellFormula -Shape $Shape -CellName "TopMargin" -Formula "0.02 in"
  Set-CellFormula -Shape $Shape -CellName "BottomMargin" -Formula "0.02 in"
}

function Set-BlackWhiteShape {
  param(
    [Parameter(Mandatory = $true)] $Shape,
    [double] $LineWeight = 0.75,
    [double] $FontSize = 9.5,
    [int] $Bold = 0
  )
  Set-CellFormula -Shape $Shape -CellName "FillPattern" -Formula "1"
  Set-CellFormula -Shape $Shape -CellName "FillForegnd" -Formula "RGB(255,255,255)"
  Set-CellFormula -Shape $Shape -CellName "LineColor" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Shape -CellName "LineWeight" -Formula "$LineWeight pt"
  Set-TextStyle -Shape $Shape -Size $FontSize -Bold $Bold
}

function Set-TreeLineStyle {
  param([Parameter(Mandatory = $true)] $Line)
  Set-CellFormula -Shape $Line -CellName "LineColor" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Line -CellName "LineWeight" -Formula "0.75 pt"
  Set-CellFormula -Shape $Line -CellName "BeginArrow" -Formula "0"
  Set-CellFormula -Shape $Line -CellName "EndArrow" -Formula "0"
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

function New-FunctionNode {
  param(
    [Parameter(Mandatory = $true)] $Page,
    $RectangleMaster,
    [string] $Text,
    [string] $Kind,
    [double] $X,
    [double] $Y,
    [double] $Width,
    [double] $Height
  )
  if ($null -ne $RectangleMaster) {
    $shape = $Page.Drop($RectangleMaster, $X, $Y)
    Set-ShapeSize -Shape $shape -Width $Width -Height $Height
  } else {
    $shape = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
  }
  $shape.Text = $Text

  $kindLower = $Kind.ToLowerInvariant()
  if ($kindLower -eq "root") {
    Set-BlackWhiteShape -Shape $shape -LineWeight 0.9 -FontSize 10.5 -Bold 1
  } elseif ($kindLower -eq "leaf") {
    Set-BlackWhiteShape -Shape $shape -LineWeight 0.75 -FontSize 8.2 -Bold 0
  } else {
    Set-BlackWhiteShape -Shape $shape -LineWeight 0.75 -FontSize 9.5 -Bold 0
  }
  return $shape
}

function Render-FunctionArchitectureDiagram {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $Diagram,
    $RectangleMaster
  )
  $layout = Get-Prop $Diagram "layout"
  $pageWidth = [double] (Get-Prop $layout "pageWidth" 8.0)
  $pageHeight = [double] (Get-Prop $layout "pageHeight" 5.5)
  Set-PageSize -Page $Page -Width $pageWidth -Height $pageHeight

  $lineCount = 0
  foreach ($segment in @(As-Array (Get-Prop $Diagram "segments"))) {
    $line = $Page.DrawLine(
      [double] (Get-Prop $segment "x1"),
      [double] (Get-Prop $segment "y1"),
      [double] (Get-Prop $segment "x2"),
      [double] (Get-Prop $segment "y2")
    )
    Set-TreeLineStyle -Line $line
    $lineCount += 1
  }

  $nodeCount = 0
  foreach ($node in @(As-Array (Get-Prop $Diagram "nodes"))) {
    $text = As-Text (Get-Prop $node "displayName") (As-Text (Get-Prop $node "name") (As-Text (Get-Prop $node "id")))
    New-FunctionNode `
      -Page $Page `
      -RectangleMaster $RectangleMaster `
      -Text $text `
      -Kind (As-Text (Get-Prop $node "kind") "node") `
      -X ([double] (Get-Prop $node "x")) `
      -Y ([double] (Get-Prop $node "y")) `
      -Width ([double] (Get-Prop $node "width" 1.0)) `
      -Height ([double] (Get-Prop $node "height" 0.4)) | Out-Null
    $nodeCount += 1
  }

  return [pscustomobject]@{ Nodes = $nodeCount; Lines = $lineCount }
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
$diagramType = (As-Text (Get-Prop $diagram "diagramType") "function_architecture").ToLowerInvariant()
if ($diagramType -notin @("function_architecture", "function_structure", "module_architecture", "architecture")) {
  throw "Unsupported diagramType '$diagramType'. Use 'function_architecture'."
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
  $page.Name = "FunctionArchitecture"

  $stencil = Open-FirstStencil -Visio $visio -Names @("BASIC_M.VSSX", "BASIC_U.VSSX")
  $rectangleMaster = Get-FirstMaster -Stencil $stencil -Names @("Rectangle")

  $counts = Render-FunctionArchitectureDiagram -Page $page -Diagram $diagram -RectangleMaster $rectangleMaster

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
    lines = $counts.Lines
    stencil = if ($null -ne $stencil) { $stencil.Name } else { "primitive-fallback" }
    rectangleMaster = if ($null -ne $rectangleMaster) { $rectangleMaster.NameU } else { "DrawRectangle" }
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
