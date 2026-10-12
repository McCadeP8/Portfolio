$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$quarto = Join-Path $projectRoot ".tools\quarto\bin\quarto.cmd"
$report = Join-Path $projectRoot "reports\data_audit.qmd"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Project Python environment not found at $python"
}
if (-not (Test-Path -LiteralPath $quarto)) {
    throw "Project Quarto executable not found at $quarto"
}

Push-Location $projectRoot
try {
    Write-Host "Building every analytical output..." -ForegroundColor Cyan
    & $python -m fantasy_basketball.cli build-all
    if ($LASTEXITCODE -ne 0) { throw "Analytical build failed." }

    Write-Host "Running the regression suite..." -ForegroundColor Cyan
    & $python -m pytest -q -p no:cacheprovider --basetemp=".pytest-tmp\build-everything"
    if ($LASTEXITCODE -ne 0) { throw "Tests failed." }

    Write-Host "Rendering the self-contained Quarto report..." -ForegroundColor Cyan
    $env:QUARTO_PYTHON = (Resolve-Path -LiteralPath $python).Path
    & $quarto render $report --no-cache
    if ($LASTEXITCODE -ne 0) { throw "Quarto render failed." }

    Write-Host "Everything built successfully: reports\data_audit.html" -ForegroundColor Green
}
finally {
    Pop-Location
}
