param(
  [Parameter(Mandatory = $true)]
  [string]$Docx,
  [string]$FigureMap,
  [int]$ExpectedVisioOle = 0,
  [int]$MinLevel2 = 1,
  [int]$MinLevel3 = 0,
  [int]$MinContentUnits = 0,
  [int]$MinCjkChars = 0,
  [string]$TemplateProfile,
  [switch]$RequireContinuationCaption,
  [switch]$SkipFigureAspectCheck,
  [switch]$SkipHardGateChecks,
  [switch]$SkipTemplateReplicationChecks
)

$ErrorActionPreference = 'Stop'
$utf8 = [System.Text.UTF8Encoding]::new()
$OutputEncoding = $utf8
try {
  [Console]::OutputEncoding = $utf8
}
catch {
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$docxPath = (Resolve-Path -LiteralPath $Docx).Path
$failed = @()

function Invoke-Gate {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Name,
    [Parameter(Mandatory = $true)]
    [scriptblock]$Command
  )

  Write-Output ""
  Write-Output "## $Name"
  & $Command
  if ($LASTEXITCODE -ne 0) {
    $script:failed += $Name
    Write-Output "[FAIL] $Name"
  }
  else {
    Write-Output "[PASS] $Name"
  }
}

Invoke-Gate 'three-line tables' {
  python (Join-Path $scriptDir 'check_docx_three_line_tables.py') $docxPath
}

Invoke-Gate 'table continuations' {
  if ($RequireContinuationCaption) {
    & (Join-Path $scriptDir 'check_docx_table_continuations.ps1') -Docx $docxPath -RequireContinuationCaption
  }
  else {
    & (Join-Path $scriptDir 'check_docx_table_continuations.ps1') -Docx $docxPath
  }
}

Invoke-Gate 'heading levels' {
  python (Join-Path $scriptDir 'check_docx_heading_levels.py') $docxPath --min-level2 $MinLevel2 --min-level3 $MinLevel3
}

if (-not $SkipHardGateChecks) {
  Invoke-Gate 'DOCX structural hygiene' {
    python (Join-Path $scriptDir 'check_docx_structural_hygiene.py') $docxPath
  }

  Invoke-Gate 'document components' {
    python (Join-Path $scriptDir 'check_docx_components.py') $docxPath
  }

  Invoke-Gate 'citation closure' {
    python (Join-Path $scriptDir 'check_docx_citation_closure.py') $docxPath
  }

  Invoke-Gate 'reference hyperlinks' {
    python (Join-Path $scriptDir 'check_docx_reference_hyperlinks.py') $docxPath
  }

  Invoke-Gate 'caption closure' {
    python (Join-Path $scriptDir 'check_docx_caption_closure.py') $docxPath
  }
}

if ($MinContentUnits -gt 0 -or $MinCjkChars -gt 0) {
  Invoke-Gate 'thesis content quality' {
    $qualityArgs = @($docxPath)
    if ($MinContentUnits -gt 0) {
      $qualityArgs += @('--min-content-units', $MinContentUnits)
    }
    if ($MinCjkChars -gt 0) {
      $qualityArgs += @('--min-cjk-chars', $MinCjkChars)
    }
    python (Join-Path $scriptDir 'check_docx_thesis_quality.py') @qualityArgs
  }
}

Invoke-Gate 'thesis voice' {
  python (Join-Path $scriptDir 'check_docx_thesis_voice.py') $docxPath
}

if ($ExpectedVisioOle -gt 0) {
  Invoke-Gate 'Visio OLE objects' {
    python (Join-Path $scriptDir 'check_docx_visio_ole.py') $docxPath --min-visio-ole $ExpectedVisioOle --require-before-caption
  }
}

if (-not [string]::IsNullOrWhiteSpace($FigureMap)) {
  $figureMapPath = (Resolve-Path -LiteralPath $FigureMap).Path
  Invoke-Gate 'duplicate figure previews' {
    python (Join-Path $scriptDir 'check_docx_duplicate_figure_previews.py') $docxPath --figure-map $figureMapPath
  }
  if (-not $SkipFigureAspectCheck) {
    Invoke-Gate 'figure preview aspects' {
      python (Join-Path $scriptDir 'check_figure_preview_aspects.py') $figureMapPath --fail-on-warning
    }
  }
}

if (-not $SkipTemplateReplicationChecks -and -not [string]::IsNullOrWhiteSpace($TemplateProfile)) {
  $templateProfilePath = (Resolve-Path -LiteralPath $TemplateProfile).Path
  $templateReportPath = Join-Path (Split-Path -Parent $templateProfilePath) 'template-replication-diff.md'
  Invoke-Gate 'template style profile' {
    python (Join-Path $scriptDir 'check_docx_style_profile.py') $docxPath --template-profile $templateProfilePath
  }
  Invoke-Gate 'template page model' {
    python (Join-Path $scriptDir 'check_docx_page_model.py') $docxPath --template-profile $templateProfilePath
  }
  Invoke-Gate 'template replication diff' {
    python (Join-Path $scriptDir 'report_template_replication_diff.py') $docxPath --template-profile $templateProfilePath --out $templateReportPath
  }
}

Write-Output ""
Write-Output "# Final Thesis DOCX Gate"
Write-Output "- File: ``$docxPath``"
Write-Output "- Failed gates: ``$($failed.Count)``"
if ($failed.Count -gt 0) {
  Write-Output "- Failed: ``$($failed -join ', ')``"
  exit 1
}

Write-Output "- Status: ``pass``"
exit 0
