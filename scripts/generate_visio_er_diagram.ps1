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

function Get-AttributeName {
  param([object] $Attribute)
  if ($Attribute -is [string]) {
    return $Attribute.Trim()
  }
  return As-Text (Get-Prop $Attribute "name")
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
    [int] $Bold = 0
  )
  Set-CellFormula -Shape $Shape -CellName "Char.Size" -Formula "$Size pt"
  Set-CellFormula -Shape $Shape -CellName "Char.Color" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Shape -CellName "Char.Style" -Formula "$Bold"
  Set-CellFormula -Shape $Shape -CellName "Para.HorzAlign" -Formula "1"
  Set-CellFormula -Shape $Shape -CellName "VerticalAlign" -Formula "1"
}

function Set-BlackWhiteShapeStyle {
  param(
    [Parameter(Mandatory = $true)] $Shape,
    [double] $LineWeight = 0.85,
    [int] $Bold = 0
  )
  Set-CellFormula -Shape $Shape -CellName "FillPattern" -Formula "1"
  Set-CellFormula -Shape $Shape -CellName "FillForegnd" -Formula "RGB(255,255,255)"
  Set-CellFormula -Shape $Shape -CellName "LineColor" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $Shape -CellName "LineWeight" -Formula "$LineWeight pt"
  Set-TextStyle -Shape $Shape -Size 11 -Bold $Bold
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
  $shape = $Page.DrawRectangle(0.35, $PageHeight - 0.42, $PageWidth - 0.35, $PageHeight - 0.08)
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
    [double] $Width = 0.28,
    [double] $Height = 0.18
  )
  if (-not $Text) {
    return $null
  }
  $label = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
  $label.Text = $Text
  Set-CellFormula -Shape $label -CellName "LinePattern" -Formula "0"
  Set-CellFormula -Shape $label -CellName "FillPattern" -Formula "0"
  Set-TextStyle -Shape $label -Size 9 -Bold 0
  return $label
}

function Add-CardinalityLabel {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [string] $Text,
    [double] $EntityX,
    [double] $EntityY,
    [double] $RelationX,
    [double] $RelationY,
    [double] $Side = 1.0
  )
  if (-not $Text) {
    return $null
  }
  $dx = $RelationX - $EntityX
  $dy = $RelationY - $EntityY
  $length = [Math]::Sqrt(($dx * $dx) + ($dy * $dy))
  if ($length -lt 0.001) {
    return Add-Label -Page $Page -Text $Text -X $EntityX -Y $EntityY
  }
  $ux = $dx / $length
  $uy = $dy / $length
  $px = -$uy
  $py = $ux
  $distance = [Math]::Min([Math]::Max($length * 0.50, 0.72), [Math]::Max(0.10, $length - 0.52))
  $x = $EntityX + ($ux * $distance) + ($px * 0.18 * $Side)
  $y = $EntityY + ($uy * $distance) + ($py * 0.18 * $Side)
  return Add-Label -Page $Page -Text $Text -X $x -Y $y
}

function New-RectShape {
  param(
    [Parameter(Mandatory = $true)] $Page,
    $Master,
    [double] $X,
    [double] $Y,
    [double] $Width,
    [double] $Height,
    [string] $Text,
    [int] $Bold = 0
  )
  if ($null -ne $Master) {
    $shape = $Page.Drop($Master, $X, $Y)
    Set-ShapeSize -Shape $shape -Width $Width -Height $Height
  } else {
    $shape = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
  }
  $shape.Text = $Text
  Set-BlackWhiteShapeStyle -Shape $shape -Bold $Bold
  return $shape
}

function New-EllipseShape {
  param(
    [Parameter(Mandatory = $true)] $Page,
    $Master,
    [double] $X,
    [double] $Y,
    [double] $Width,
    [double] $Height,
    [string] $Text,
    [int] $Bold = 0
  )
  if ($null -ne $Master) {
    $shape = $Page.Drop($Master, $X, $Y)
    Set-ShapeSize -Shape $shape -Width $Width -Height $Height
  } else {
    $shape = $Page.DrawOval($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
  }
  $shape.Text = $Text
  Set-BlackWhiteShapeStyle -Shape $shape -Bold $Bold
  return $shape
}

function New-DiamondShape {
  param(
    [Parameter(Mandatory = $true)] $Page,
    $Master,
    [double] $X,
    [double] $Y,
    [double] $Width,
    [double] $Height,
    [string] $Text
  )
  if ($null -ne $Master) {
    $shape = $Page.Drop($Master, $X, $Y)
    Set-ShapeSize -Shape $shape -Width $Width -Height $Height
  } else {
    $shape = $Page.DrawRectangle($X - ($Width / 2), $Y - ($Height / 2), $X + ($Width / 2), $Y + ($Height / 2))
    Set-CellFormula -Shape $shape -CellName "Angle" -Formula "45 deg"
  }
  $shape.Text = $Text
  Set-BlackWhiteShapeStyle -Shape $shape -Bold 1
  return $shape
}

function Connect-Shapes {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $From,
    [Parameter(Mandatory = $true)] $To,
    [double] $FromX = 0.5,
    [double] $FromY = 0.5,
    [double] $ToX = 0.5,
    [double] $ToY = 0.5
  )
  $line = $Page.DrawLine(0, 0, 1, 1)
  $line.CellsU("BeginX").GlueToPos($From, $FromX, $FromY)
  $line.CellsU("EndX").GlueToPos($To, $ToX, $ToY)
  Set-CellFormula -Shape $line -CellName "LineColor" -Formula "RGB(0,0,0)"
  Set-CellFormula -Shape $line -CellName "LineWeight" -Formula "0.75 pt"
  Set-CellFormula -Shape $line -CellName "BeginArrow" -Formula "0"
  Set-CellFormula -Shape $line -CellName "EndArrow" -Formula "0"
  return $line
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

function Connect-Toward {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $From,
    [Parameter(Mandatory = $true)] $To
  )
  $fromPoint = Get-GluePointToward -From $From -To $To
  $toPoint = Get-GluePointToward -From $To -To $From
  return Connect-Shapes -Page $Page -From $From -To $To -FromX $fromPoint.X -FromY $fromPoint.Y -ToX $toPoint.X -ToY $toPoint.Y
}

function Get-DefaultAttributeOffset {
  param(
    [int] $Index,
    [int] $Count,
    [double] $RadiusX = 1.9,
    [double] $RadiusY = 1.45,
    [double] $StartAngle = 205.0,
    [double] $EndAngle = -25.0
  )
  if ($Count -le 1) {
    return @{ Dx = 0.0; Dy = -$RadiusY }
  }
  $angle = $StartAngle + (($EndAngle - $StartAngle) * $Index / [Math]::Max(1, $Count - 1))
  $radians = $angle * [Math]::PI / 180.0
  return @{ Dx = [Math]::Cos($radians) * $RadiusX; Dy = [Math]::Sin($radians) * $RadiusY }
}

function Add-Attributes {
  param(
    [Parameter(Mandatory = $true)] $Page,
    $EllipseMaster,
    [Parameter(Mandatory = $true)] $EntityShape,
    [Parameter(Mandatory = $true)] [object[]] $Attributes,
    [double] $DefaultRadiusX = 1.8,
    [double] $DefaultRadiusY = 1.25,
    [double] $StartAngle = 205.0,
    [double] $EndAngle = -25.0
  )
  $created = New-Object System.Collections.Generic.List[object]
  $entityX = [double] $EntityShape.CellsU("PinX").ResultIU
  $entityY = [double] $EntityShape.CellsU("PinY").ResultIU
  for ($i = 0; $i -lt $Attributes.Count; $i++) {
    $attr = $Attributes[$i]
    $name = Get-AttributeName $attr
    if (-not $name) {
      continue
    }
    $offset = Get-DefaultAttributeOffset -Index $i -Count $Attributes.Count -RadiusX $DefaultRadiusX -RadiusY $DefaultRadiusY -StartAngle $StartAngle -EndAngle $EndAngle
    if ($attr -isnot [string]) {
      $dxValue = Get-Prop $attr "dx" $null
      $dyValue = Get-Prop $attr "dy" $null
      if ($null -ne $dxValue -and $null -ne $dyValue) {
        $offset = @{ Dx = [double] $dxValue; Dy = [double] $dyValue }
      }
    }
    $isKey = $false
    if ($attr -isnot [string]) {
      $keyValue = Get-Prop $attr "key" $false
      $isKey = [bool] $keyValue
    }
    $shape = New-EllipseShape -Page $Page -Master $EllipseMaster -X ($entityX + $offset.Dx) -Y ($entityY + $offset.Dy) -Width 1.05 -Height 0.42 -Text $name -Bold ([int] $isKey)
    Connect-Toward -Page $Page -From $EntityShape -To $shape | Out-Null
    $created.Add($shape)
  }
  return $created
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

function Render-SingleEntityDiagram {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $Diagram,
    $RectangleMaster,
    $EllipseMaster
  )
  $entity = Get-Prop $Diagram "entity"
  if ($null -eq $entity) {
    $entities = @(As-Array (Get-Prop $Diagram "entities"))
    if ($entities.Count -gt 0) {
      $entity = $entities[0]
    }
  }
  if ($null -eq $entity) {
    throw "single_entity diagram must contain 'entity' or at least one item in 'entities'."
  }
  $layout = Get-Prop $Diagram "layout"
  $pageWidth = [double] (Get-Prop $layout "pageWidth" 6.0)
  $pageHeight = [double] (Get-Prop $layout "pageHeight" 4.0)
  $entityX = [double] (Get-Prop $layout "entityX" ($pageWidth / 2))
  $entityY = [double] (Get-Prop $layout "entityY" ($pageHeight - 0.75))
  Set-PageSize -Page $Page -Width $pageWidth -Height $pageHeight

  if ([bool] (Get-Prop $layout "showTitle" $false)) {
    $title = As-Text (Get-Prop $Diagram "title")
    Add-Title -Page $Page -Title $title -PageWidth $pageWidth -PageHeight $pageHeight
  }

  $entityName = As-Text (Get-Prop $entity "name") "实体"
  $entityShape = New-RectShape -Page $Page -Master $RectangleMaster -X $entityX -Y $entityY -Width 1.35 -Height 0.48 -Text $entityName -Bold 0
  $attributes = @(As-Array (Get-Prop $entity "attributes"))
  Add-Attributes -Page $Page -EllipseMaster $EllipseMaster -EntityShape $entityShape -Attributes $attributes -DefaultRadiusX 2.0 -DefaultRadiusY 1.55 -StartAngle 205 -EndAngle 335 | Out-Null
  return [pscustomobject]@{ Entities = 1; Attributes = $attributes.Count; Relationships = 0 }
}

function Render-OverviewDiagram {
  param(
    [Parameter(Mandatory = $true)] $Page,
    [Parameter(Mandatory = $true)] $Diagram,
    $RectangleMaster,
    $EllipseMaster,
    $DiamondMaster
  )
  $layout = Get-Prop $Diagram "layout"
  $pageWidth = [double] (Get-Prop $layout "pageWidth" 10.5)
  $pageHeight = [double] (Get-Prop $layout "pageHeight" 6.0)
  Set-PageSize -Page $Page -Width $pageWidth -Height $pageHeight

  if ([bool] (Get-Prop $layout "showTitle" $false)) {
    $title = As-Text (Get-Prop $Diagram "title")
    Add-Title -Page $Page -Title $title -PageWidth $pageWidth -PageHeight $pageHeight
  }

  $entities = @(As-Array (Get-Prop $Diagram "entities"))
  if ($entities.Count -eq 0) {
    throw "overview diagram must contain at least one entity in 'entities'."
  }

  $entityShapes = @{}
  $relationshipShapes = @{}
  $attributeCount = 0
  for ($i = 0; $i -lt $entities.Count; $i++) {
    $entity = $entities[$i]
    $id = As-Text (Get-Prop $entity "id") (As-Text (Get-Prop $entity "name") "entity_$i")
    $name = As-Text (Get-Prop $entity "name") $id
    $x = [double] (Get-Prop $entity "x" (1.2 + (($i % 3) * 3.7)))
    $y = [double] (Get-Prop $entity "y" ($pageHeight - 1.3 - ([Math]::Floor($i / 3) * 2.2)))
    $shape = New-RectShape -Page $Page -Master $RectangleMaster -X $x -Y $y -Width 1.15 -Height 0.55 -Text $name -Bold 1
    $entityShapes[$id] = $shape
    $attributes = @(As-Array (Get-Prop $entity "attributes"))
    $attributeCount += $attributes.Count
    Add-Attributes -Page $Page -EllipseMaster $EllipseMaster -EntityShape $shape -Attributes $attributes -DefaultRadiusX 1.55 -DefaultRadiusY 1.0 | Out-Null
  }

  $relationships = @(As-Array (Get-Prop $Diagram "relationships"))
  foreach ($rel in $relationships) {
    $id = As-Text (Get-Prop $rel "id")
    $name = As-Text (Get-Prop $rel "name") "关系"
    $fromId = As-Text (Get-Prop $rel "from")
    $toId = As-Text (Get-Prop $rel "to")
    if (-not $entityShapes.ContainsKey($fromId) -or -not $entityShapes.ContainsKey($toId)) {
      Write-Warning "Skipped relationship '$name' because it references unknown entities: $fromId -> $toId"
      continue
    }
    $fromShape = $entityShapes[$fromId]
    $toShape = $entityShapes[$toId]
    $fromX = [double] $fromShape.CellsU("PinX").ResultIU
    $fromY = [double] $fromShape.CellsU("PinY").ResultIU
    $toX = [double] $toShape.CellsU("PinX").ResultIU
    $toY = [double] $toShape.CellsU("PinY").ResultIU
    $relX = [double] (Get-Prop $rel "x" (($fromX + $toX) / 2))
    $relY = [double] (Get-Prop $rel "y" (($fromY + $toY) / 2))
    $diamond = New-DiamondShape -Page $Page -Master $DiamondMaster -X $relX -Y $relY -Width 0.95 -Height 0.58 -Text $name
    if ($id) {
      $relationshipShapes[$id] = $diamond
    }
    Connect-Toward -Page $Page -From $fromShape -To $diamond | Out-Null
    Connect-Toward -Page $Page -From $diamond -To $toShape | Out-Null
    $fromCardinality = As-Text (Get-Prop $rel "fromCardinality")
    $toCardinality = As-Text (Get-Prop $rel "toCardinality")
    if ($fromCardinality) {
      $fromLabelX = Get-Prop $rel "fromLabelX" $null
      $fromLabelY = Get-Prop $rel "fromLabelY" $null
      if ($null -ne $fromLabelX -and $null -ne $fromLabelY) {
        Add-Label -Page $Page -Text $fromCardinality -X ([double] $fromLabelX) -Y ([double] $fromLabelY) | Out-Null
      } else {
        Add-CardinalityLabel -Page $Page -Text $fromCardinality -EntityX $fromX -EntityY $fromY -RelationX $relX -RelationY $relY -Side 1 | Out-Null
      }
    }
    if ($toCardinality) {
      $toLabelX = Get-Prop $rel "toLabelX" $null
      $toLabelY = Get-Prop $rel "toLabelY" $null
      if ($null -ne $toLabelX -and $null -ne $toLabelY) {
        Add-Label -Page $Page -Text $toCardinality -X ([double] $toLabelX) -Y ([double] $toLabelY) | Out-Null
      } else {
        Add-CardinalityLabel -Page $Page -Text $toCardinality -EntityX $toX -EntityY $toY -RelationX $relX -RelationY $relY -Side -1 | Out-Null
      }
    }
  }

  return [pscustomobject]@{ Entities = $entities.Count; Attributes = $attributeCount; Relationships = $relationships.Count }
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
$diagramType = (As-Text (Get-Prop $diagram "diagramType") "overview").ToLowerInvariant()

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
  $page.Name = "ER Diagram"

  $stencil = Open-FirstStencil -Visio $visio -Names @("BASIC_M.VSSX", "BASIC_U.VSSX", "BASFLO_M.VSSX", "BASFLO_U.VSSX")
  $rectangleMaster = Get-FirstMaster -Stencil $stencil -Names @("Rectangle", "矩形")
  $ellipseMaster = Get-FirstMaster -Stencil $stencil -Names @("Ellipse", "椭圆形", "Circle")
  $diamondMaster = Get-FirstMaster -Stencil $stencil -Names @("Diamond", "菱形", "Decision")

  if ($diagramType -in @("single", "single_entity", "entity")) {
    $counts = Render-SingleEntityDiagram -Page $page -Diagram $diagram -RectangleMaster $rectangleMaster -EllipseMaster $ellipseMaster
  } elseif ($diagramType -in @("overview", "total", "general", "chen")) {
    $counts = Render-OverviewDiagram -Page $page -Diagram $diagram -RectangleMaster $rectangleMaster -EllipseMaster $ellipseMaster -DiamondMaster $diamondMaster
  } else {
    throw "Unsupported diagramType '$diagramType'. Use 'single_entity' or 'overview'."
  }

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
    entities = $counts.Entities
    attributes = $counts.Attributes
    relationships = $counts.Relationships
    stencil = if ($null -ne $stencil) { $stencil.Name } else { "primitive-fallback" }
    rectangleMaster = if ($null -ne $rectangleMaster) { $rectangleMaster.NameU } else { "DrawRectangle" }
    ellipseMaster = if ($null -ne $ellipseMaster) { $ellipseMaster.NameU } else { "DrawOval" }
    diamondMaster = if ($null -ne $diamondMaster) { $diamondMaster.NameU } else { "RotatedRectangle" }
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
