$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

Write-Host "== Building single-file exe =="
python -m PyInstaller --noconfirm --clean --onefile --windowed --name StandaloneKeypadStudio --paths app app/main.py
if (-not $?) { exit 1 }

Write-Host "== Building fast onedir version =="
python -m PyInstaller --noconfirm --clean --windowed --onedir --name StandaloneKeypadStudio_onedir --paths app app/main.py
if (-not $?) { exit 1 }

Write-Host ""
Write-Host "Done:"
Write-Host "  dist\StandaloneKeypadStudio.exe        (single file, slower first start)"
Write-Host "  dist\StandaloneKeypadStudio_onedir\    (folder build, fastest start)"
