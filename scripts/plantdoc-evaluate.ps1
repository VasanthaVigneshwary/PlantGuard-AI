param(
    [switch]$Prepare
)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
$datasetRoot = Join-Path $repoRoot 'datasets\plantdoc'
$archive = Join-Path $repoRoot 'datasets\plantdoc-source.zip'
$manifest = Join-Path $datasetRoot 'manifest.jsonl'
if (-not (Test-Path -LiteralPath $python)) { throw "Project Python environment not found: $python" }
if (-not (Test-Path -LiteralPath $manifest)) {
    if (-not (Test-Path -LiteralPath $archive)) {
        Invoke-WebRequest -Uri 'https://codeload.github.com/pratikkayal/PlantDoc-Dataset/zip/refs/heads/master' -OutFile $archive
    }
    & $python (Join-Path $repoRoot 'backend\plantdoc_dataset.py') prepare $archive $datasetRoot
    if ($LASTEXITCODE -ne 0) { throw 'PlantDoc archive preparation failed.' }
} elseif ($Prepare) {
    Write-Host 'The manifest already exists; keeping the prepared dataset unchanged.'
}
& $python (Join-Path $repoRoot 'backend\plantdoc_dataset.py') evaluate $datasetRoot
if ($LASTEXITCODE -ne 0) { throw 'PlantDoc inference evaluation failed.' }
