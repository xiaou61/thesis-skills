param(
  [Parameter(Mandatory = $true)]
  [string]$Docx,
  [string]$Out,
  [switch]$RequireContinuationCaption
)

$ErrorActionPreference = 'Stop'

function Get-PlainText {
  param([AllowNull()]$Text)
  if ($null -eq $Text) { return '' }
  return (($Text.ToString()) -replace "[`r`a]", '').Trim()
}

function Get-PreviousParagraphText {
  param($Range)
  $probe = $Range.Duplicate
  $probe.Collapse(1) | Out-Null
  $previous = $probe.Previous(4, 1)
  if ($null -eq $previous) { return '' }
  return Get-PlainText $previous.Text
}

function Get-ContinuationCaption {
  param([string]$Caption)
  if ($Caption -match '表\s*([0-9]+[.\-][0-9]+)') {
    return "续表 $($matches[1].Replace('-', '.'))"
  }
  if ($Caption -match '表([0-9]+[.\-][0-9]+)') {
    return "续表 $($matches[1].Replace('-', '.'))"
  }
  return '续表'
}

function Test-ContinuationCaption {
  param([string]$Text)
  return $Text -match '续表|（续）|\(续\)'
}

function Normalize-TablePagination {
  param($Table)
  for ($rowIndex = 1; $rowIndex -le $Table.Rows.Count; $rowIndex++) {
    $row = $Table.Rows.Item($rowIndex)
    $row.AllowBreakAcrossPages = $false
    if ($rowIndex -eq 1) {
      $row.HeadingFormat = $true
    }
  }
}

function Get-TableInfo {
  param($Table)
  $startRange = $Table.Range.Duplicate
  $startRange.Collapse(1) | Out-Null
  $endRange = $Table.Range.Duplicate
  $endRange.Collapse(0) | Out-Null
  [pscustomobject]@{
    startPage = [int]$startRange.Information(3)
    endPage = [int]$endRange.Information(3)
  }
}

function Find-SplitRow {
  param($Table, [int]$StartPage)
  for ($rowIndex = 2; $rowIndex -le $Table.Rows.Count; $rowIndex++) {
    $rowRange = $Table.Rows.Item($rowIndex).Range.Duplicate
    $rowRange.Collapse(1) | Out-Null
    $rowPage = [int]$rowRange.Information(3)
    if ($rowPage -gt $StartPage) {
      return $rowIndex
    }
  }
  return $null
}

function Insert-PageBreakBeforeTableBlock {
  param($Document, $Table)
  $range = $Table.Range.Duplicate
  $range.Collapse(1) | Out-Null
  $previous = $range.Previous(4, 1)
  if ($null -ne $previous) {
    $previous.Collapse(1) | Out-Null
    $previous.InsertBreak(7) | Out-Null
    return $true
  }
  $range.InsertBreak(7) | Out-Null
  return $true
}

$source = (Resolve-Path -LiteralPath $Docx).Path
if ([string]::IsNullOrWhiteSpace($Out)) {
  $target = $source
}
else {
  $target = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Out)
  Copy-Item -LiteralPath $source -Destination $target -Force
}

$word = $null
$doc = $null
$actions = @()

try {
  try {
    $word = New-Object -ComObject Word.Application
  }
  catch {
    Write-Error "Microsoft Word COM automation is required to repair page-level table continuations. Run this repair in an interactive Windows session with desktop Word available. Original error: $($_.Exception.Message)"
    exit 2
  }
  $word.Visible = $false
  $doc = $word.Documents.Open($target, $false, $false)
  $doc.Repaginate()

  $passes = 0
  while ($passes -lt 6) {
    $passes += 1
    $changed = $false

    for ($tableIndex = $doc.Tables.Count; $tableIndex -ge 1; $tableIndex--) {
      $table = $doc.Tables.Item($tableIndex)
      Normalize-TablePagination -Table $table

      if (-not $RequireContinuationCaption) {
        $actions += [pscustomobject]@{ table = $tableIndex; action = 'repeat_header_only'; splitRow = $null; caption = ''; pass = $passes }
        continue
      }

      $doc.Repaginate()
      $info = Get-TableInfo -Table $table
      if ($info.endPage -le $info.startPage) {
        $actions += [pscustomobject]@{ table = $tableIndex; action = 'single_page'; splitRow = $null; caption = ''; pass = $passes }
        continue
      }

      $captionText = Get-PreviousParagraphText $table.Range
      if (-not (Test-ContinuationCaption $captionText)) {
        Insert-PageBreakBeforeTableBlock -Document $doc -Table $table | Out-Null
        $doc.Repaginate()
        $table = $doc.Tables.Item($tableIndex)
        Normalize-TablePagination -Table $table
        $info = Get-TableInfo -Table $table
        $actions += [pscustomobject]@{ table = $tableIndex; action = 'page_break_before_table'; splitRow = $null; caption = $captionText; pass = $passes }
        $changed = $true
        if ($info.endPage -le $info.startPage) {
          continue
        }
      }

      $splitRow = Find-SplitRow -Table $table -StartPage $info.startPage
      if ($null -eq $splitRow -or $splitRow -le 2) {
        $actions += [pscustomobject]@{ table = $tableIndex; action = 'unable_to_split_safely'; splitRow = $splitRow; caption = ''; pass = $passes }
        continue
      }

      $continuationCaption = Get-ContinuationCaption $captionText
      $table.Rows.Item($splitRow).Select()
      $word.Selection.SplitTable()
      $word.Selection.TypeText($continuationCaption)
      $word.Selection.TypeParagraph()

      $firstPart = $doc.Tables.Item($tableIndex)
      $secondPart = $doc.Tables.Item($tableIndex + 1)
      Normalize-TablePagination -Table $firstPart
      Normalize-TablePagination -Table $secondPart
      $changed = $true
      $actions += [pscustomobject]@{ table = $tableIndex; action = 'split_with_caption'; splitRow = $splitRow; caption = $continuationCaption; pass = $passes }
    }
    if (-not $changed) { break }
  }

  $doc.Save()
}
finally {
  if ($null -ne $doc) { $doc.Close($true) | Out-Null }
  if ($null -ne $word) { $word.Quit() | Out-Null }
}

[pscustomobject]@{
  docx = $target
  requireContinuationCaption = [bool]$RequireContinuationCaption
  actions = $actions
} | ConvertTo-Json -Depth 6
