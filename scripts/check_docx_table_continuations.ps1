param(
  [Parameter(Mandatory = $true)]
  [string]$Docx,
  [switch]$RequireContinuationCaption,
  [switch]$Json
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

function Get-NextParagraphText {
  param($Range)
  $probe = $Range.Duplicate
  $probe.Collapse(0) | Out-Null
  $next = $probe.Next(4, 1)
  if ($null -eq $next) { return '' }
  return Get-PlainText $next.Text
}

$path = (Resolve-Path -LiteralPath $Docx).Path
$word = $null
$doc = $null
$findings = @()

try {
  try {
    $word = New-Object -ComObject Word.Application
  }
  catch {
    Write-Error "Microsoft Word COM automation is required for page-level table continuation checks. Run this gate in an interactive Windows session with desktop Word available. Original error: $($_.Exception.Message)"
    exit 2
  }
  $word.Visible = $false
  $doc = $word.Documents.Open($path, $false, $true)
  $doc.Repaginate()

  for ($tableIndex = 1; $tableIndex -le $doc.Tables.Count; $tableIndex++) {
    $table = $doc.Tables.Item($tableIndex)
    $startRange = $table.Range.Duplicate
    $startRange.Collapse(1) | Out-Null
    $endRange = $table.Range.Duplicate
    $endRange.Collapse(0) | Out-Null
    $startPage = [int]$startRange.Information(3)
    $endPage = [int]$endRange.Information(3)
    $crossesPage = $endPage -gt $startPage

    $headerRepeat = [int]$table.Rows.Item(1).HeadingFormat
    $allowBreakErrors = @()
    for ($rowIndex = 1; $rowIndex -le $table.Rows.Count; $rowIndex++) {
      if ([int]$table.Rows.Item($rowIndex).AllowBreakAcrossPages -ne 0) {
        $allowBreakErrors += $rowIndex
      }
    }

    $captionBefore = Get-PreviousParagraphText $table.Range
    $captionAfter = Get-NextParagraphText $table.Range
    $hasContinuationCaption = ($captionBefore -match '续表|（续）|\(续\)' -or $captionAfter -match '续表|（续）|\(续\)')

    $messages = @()
    if ($crossesPage -and $headerRepeat -eq 0) {
      $messages += 'cross-page table does not repeat header row'
    }
    if ($crossesPage -and $allowBreakErrors.Count -gt 0) {
      $messages += ('cross-page table allows row breaks across pages: ' + ($allowBreakErrors -join ','))
    }
    if ($crossesPage -and $RequireContinuationCaption -and -not $hasContinuationCaption) {
      $messages += 'cross-page table is missing continuation caption'
    }

    $findings += [pscustomobject]@{
      table = $tableIndex
      rows = [int]$table.Rows.Count
      startPage = $startPage
      endPage = $endPage
      crossesPage = $crossesPage
      headerRepeat = ($headerRepeat -ne 0)
      allowBreakRows = $allowBreakErrors
      captionBefore = $captionBefore
      captionAfter = $captionAfter
      hasContinuationCaption = $hasContinuationCaption
      status = if ($messages.Count -eq 0) { 'ok' } else { 'error' }
      message = if ($messages.Count -eq 0) { 'table pagination rules satisfied' } else { $messages -join '; ' }
    }
  }
}
finally {
  if ($null -ne $doc) { $doc.Close($false) | Out-Null }
  if ($null -ne $word) { $word.Quit() | Out-Null }
}

$errors = @($findings | Where-Object { $_.status -eq 'error' })
$report = [pscustomobject]@{
  docx = $path
  tables = $findings.Count
  errors = $errors.Count
  requireContinuationCaption = [bool]$RequireContinuationCaption
  findings = $findings
}

if ($Json) {
  $report | ConvertTo-Json -Depth 8
}
else {
  Write-Output '# DOCX Table Continuation Check'
  Write-Output ''
  Write-Output "- File: ``$path``"
  Write-Output "- Tables: ``$($findings.Count)``"
  Write-Output "- Errors: ``$($errors.Count)``"
  Write-Output ''
  Write-Output '| Table | Pages | Crosses | Header repeat | Continuation caption | Status | Message |'
  Write-Output '| --- | --- | --- | --- | --- | --- | --- |'
  foreach ($finding in $findings) {
    Write-Output "| $($finding.table) | $($finding.startPage)-$($finding.endPage) | $($finding.crossesPage) | $($finding.headerRepeat) | $($finding.hasContinuationCaption) | $($finding.status) | $($finding.message) |"
  }
}

if ($errors.Count -gt 0) { exit 1 }
exit 0
