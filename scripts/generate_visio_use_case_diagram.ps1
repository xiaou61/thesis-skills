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
    [double] $Size = 11,
    [int] $Bold = 0,
    [int] $HAlign = 1,
    [int] $VAlign = 1
  )
  Set-CellFormula -Shape $Shape -CellName "Char.Size" -Formula "$Size pt"
  Set-CellFormula -Shape $Shape -CellName "Char.Color" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Shape -CellName "Char.Style" -Formula "$Bold"
  Set-CellFormula -Shape $Shape -CellName "Para.HorzAlign" -Formula "$HAlign"
  Set-CellFormula -Shape $Shape -CellName "VerticalAlign" -Formula "$VAlign"
}

function Set-BlackWhiteLine {
  param([Parameter(Mandatory = $true)] $Shape, [double] $Weight = 0.75)
  Set-CellFormula -Shape $Shape -CellName "LineColor" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Shape -CellName "LineWeight" -Formula "$Weight pt"
}

function Set-Transparent {
  param([Parameter(Mandatory = $true)] $Shape)
  Set-CellFormula -Shape $Shape -CellName "LinePattern" -Formula "0"
  Set-CellFormula -Shape $Shape -CellName "FillPattern" -Formula "0"
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
  Set-Transparent -Shape $shape
  Set-TextStyle -Shape $shape -Size 13 -Bold 1
}

function Add-Label {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [string] $Text,
    [double] $X,
    [double] $Y,
    [double] $Width = 0.85,
    [double] $Height = 0.24,
    [double] $Size = 11,
    [int] $Bold = 0
  )
  if (-not $Text) {
    return $null
  }
  $label = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
  $label.Text = $Text
  Set-Transparent -Shape $label
  Set-TextStyle -Shape $label -Size $Size -Bold $Bold
  return $label
}

function Add-Actor {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [string] $Text,
    [double] $X,
    [double] $Y,
    [double] $Width = 0.72,
    [double] $Height = 1.25
  )
  $anchor = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
  Set-Transparent -Shape $anchor

  $headRadius = 0.12
  $headY = $Y + ($Height * 0.28)
  $head = $Page.DrawOval($X - $headRadius, $headY - $headRadius, $X + $headRadius, $headY + $headRadius)
  Set-CellFormula -Shape $head -CellName "FillPattern" -Formula "1"
  Set-CellFormula -Shape $head -CellName "FillForegnd" -Formula "RGB(255,255,255)"
  Set-BlackWhiteLine -Shape $head

  $bodyTop = $headY - $headRadius
  $bodyBottom = $Y - ($Height * 0.12)
  $body = $Page.DrawLine($X, $bodyTop, $X, $bodyBottom)
  $arms = $Page.DrawLine($X - ($Width * 0.34), $Y + ($Height * 0.04), $X + ($Width * 0.34), $Y + ($Height * 0.04))
  $leftLeg = $Page.DrawLine($X, $bodyBottom, $X - ($Width * 0.33), $Y - ($Height * 0.36))
  $rightLeg = $Page.DrawLine($X, $bodyBottom, $X + ($Width * 0.33), $Y - ($Height * 0.36))
  foreach ($part in @($body, $arms, $leftLeg, $rightLeg)) {
    Set-BlackWhiteLine -Shape $part
    Set-CellFormula -Shape $part -CellName "BeginArrow" -Formula "0"
    Set-CellFormula -Shape $part -CellName "EndArrow" -Formula "0"
  }

  Add-Label -Page $Page -Text $Text -X $X -Y ($Y - ($Height * 0.48)) -Width ($Width + 0.35) -Height 0.28 -Size 11 -Bold 1 | Out-Null
  return $anchor
}

function Add-UseCase {
  param(
    [Parameter(Mandatory = $true)] $Page,
    $EllipseMaster,
    [string] $Text,
    [double] $X,
    [double] $Y,
    [double] $Width = 1.65,
    [double] $Height = 0.48
  )
  if ($null -ne $EllipseMaster) {
    $shape = $Page.Drop($EllipseMaster, $X, $Y)
    Set-ShapeSize -Shape $shape -Width $Width -Height $Height
  } else {
    $shape = $Page.DrawOval($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
  }
  $shape.Text = $Text
  Set-CellFormula -Shape $shape -CellName "FillPattern" -Formula "1"
  Set-CellFormula -Shape $shape -CellName "FillForegnd" -Formula "RGB(255,255,255)"
  Set-BlackWhiteLine -Shape $shape -Weight 0.75
  Set-TextStyle -Shape $shape -Size 11 -Bold 1
  return $shape
}

function Add-Boundary {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [string] $Text,
    [double] $X,
    [double] $Y,
    [double] $Width,
    [double] $Height
  )
  $shape = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
  $shape.Text = $Text
  Set-CellFormula -Shape $shape -CellName "FillPattern" -Formula "0"
  Set-BlackWhiteLine -Shape $shape -Weight 0.75
  Set-TextStyle -Shape $shape -Size 10 -Bold 1 -HAlign 0 -VAlign 0
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

function Connect-Shapes {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $From,
    [Parameter(Mandatory = $true)] $To,
    [switch] $Dashed,
    [switch] $Arrow,
    [string] $Label = ""
  )
  $fromPoint = Get-GluePointToward -From $From -To $To
  $toPoint = Get-GluePointToward -From $To -To $From
  $line = $Page.DrawLine(0, 0, 1, 1)
  $line.CellsU("BeginX").GlueToPos($From, $fromPoint.X, $fromPoint.Y)
  $line.CellsU("EndX").GlueToPos($To, $toPoint.X, $toPoint.Y)
  $line.Text = $Label
  Set-BlackWhiteLine -Shape $line -Weight 0.75
  Set-CellFormula -Shape $line -CellName "BeginArrow" -Formula "0"
  if ($Arrow) {
    Set-CellFormula -Shape $line -CellName "EndArrow" -Formula "4"
  } else {
    Set-CellFormula -Shape $line -CellName "EndArrow" -Formula "0"
  }
  if ($Dashed) {
    Set-CellFormula -Shape $line -CellName "LinePattern" -Formula "2"
  }
  Set-TextStyle -Shape $line -Size 9 -Bold 0
  return $line
}

function Render-UseCaseDiagram {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $Diagram,
    $EllipseMaster
  )
  $layout = Get-Prop $Diagram "layout"
  $pageWidth = [double] (Get-Prop $layout "pageWidth" 7.2)
  $pageHeight = [double] (Get-Prop $layout "pageHeight" 4.2)
  Set-PageSize -Page $Page -Width $pageWidth -Height $pageHeight

  if ([bool] (Get-Prop $layout "showTitle" $false)) {
    Add-Title -Page $Page -Title (As-Text (Get-Prop $Diagram "title")) -PageWidth $pageWidth -PageHeight $pageHeight
  }

  $boundary = Get-Prop $layout "boundary"
  if ($null -ne $boundary) {
    $boundaryText = As-Text (Get-Prop $boundary "name")
    Add-Boundary -Page $Page -Text $boundaryText -X ([double] (Get-Prop $boundary "x")) -Y ([double] (Get-Prop $boundary "y")) -Width ([double] (Get-Prop $boundary "width")) -Height ([double] (Get-Prop $boundary "height")) | Out-Null
  }

  $actorShapes = @{}
  foreach ($actor in @(As-Array (Get-Prop $Diagram "actors"))) {
    $id = As-Text (Get-Prop $actor "id") (As-Text (Get-Prop $actor "name") "actor")
    $shape = Add-Actor -Page $Page -Text (As-Text (Get-Prop $actor "name") $id) -X ([double] (Get-Prop $actor "x")) -Y ([double] (Get-Prop $actor "y")) -Width ([double] (Get-Prop $actor "width" 0.72)) -Height ([double] (Get-Prop $actor "height" 1.25))
    $actorShapes[$id] = $shape
  }

  $useCaseShapes = @{}
  foreach ($case in @(As-Array (Get-Prop $Diagram "useCases"))) {
    $id = As-Text (Get-Prop $case "id") (As-Text (Get-Prop $case "name") "use_case")
    $shape = Add-UseCase -Page $Page -EllipseMaster $EllipseMaster -Text (As-Text (Get-Prop $case "name") $id) -X ([double] (Get-Prop $case "x")) -Y ([double] (Get-Prop $case "y")) -Width ([double] (Get-Prop $case "width" 1.65)) -Height ([double] (Get-Prop $case "height" 0.48))
    $useCaseShapes[$id] = $shape
  }

  $associations = @(As-Array (Get-Prop $Diagram "associations"))
  foreach ($assoc in $associations) {
    $actorId = As-Text (Get-Prop $assoc "actor")
    $caseId = As-Text (Get-Prop $assoc "useCase")
    if ($actorShapes.ContainsKey($actorId) -and $useCaseShapes.ContainsKey($caseId)) {
      Connect-Shapes -Page $Page -From $actorShapes[$actorId] -To $useCaseShapes[$caseId] -Arrow -Label (As-Text (Get-Prop $assoc "label")) | Out-Null
    } else {
      Write-Warning "Skipped association because it references unknown actor/use case: $actorId -> $caseId"
    }
  }

  $dependencies = @(As-Array (Get-Prop $Diagram "dependencies"))
  foreach ($dep in $dependencies) {
    $fromId = As-Text (Get-Prop $dep "from")
    $toId = As-Text (Get-Prop $dep "to")
    if ($useCaseShapes.ContainsKey($fromId) -and $useCaseShapes.ContainsKey($toId)) {
      $label = As-Text (Get-Prop $dep "label")
      if (-not $label) {
        $type = (As-Text (Get-Prop $dep "type") "dependency").ToLowerInvariant()
        if ($type -eq "include") {
          $label = "<<include>>"
        } elseif ($type -eq "extend") {
          $label = "<<extend>>"
        }
      }
      Connect-Shapes -Page $Page -From $useCaseShapes[$fromId] -To $useCaseShapes[$toId] -Dashed -Arrow -Label $label | Out-Null
    } else {
      Write-Warning "Skipped dependency because it references unknown use cases: $fromId -> $toId"
    }
  }

  return [pscustomobject]@{ Actors = $actorShapes.Count; UseCases = $useCaseShapes.Count; Associations = $associations.Count; Dependencies = $dependencies.Count }
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
$diagramType = (As-Text (Get-Prop $diagram "diagramType") "use_case").ToLowerInvariant()
if ($diagramType -notin @("use_case", "usecase", "uml_use_case")) {
  throw "Unsupported diagramType '$diagramType'. Use 'use_case'."
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
  $page.Name = "Use Case Diagram"

  $stencil = Open-FirstStencil -Visio $visio -Names @("BASIC_M.VSSX", "BASIC_U.VSSX")
  $ellipseMaster = Get-FirstMaster -Stencil $stencil -Names @("Ellipse", "椭圆形", "Circle")

  $counts = Render-UseCaseDiagram -Page $page -Diagram $diagram -EllipseMaster $ellipseMaster

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
    actors = $counts.Actors
    useCases = $counts.UseCases
    associations = $counts.Associations
    dependencies = $counts.Dependencies
    stencil = if ($null -ne $stencil) { $stencil.Name } else { "primitive-fallback" }
    ellipseMaster = if ($null -ne $ellipseMaster) { $ellipseMaster.NameU } else { "DrawOval" }
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
