$pythonExe = ".\.venv\Scripts\python.exe"
$pyInstallerExe = ".\.venv\Scripts\pyinstaller.exe"
$releaseDir = ".\release"
$buildToken = Get-Date -Format "yyyyMMdd_HHmmss"
$distPath = Join-Path $env:TEMP "pdf_converter_dist_$buildToken"
$workPath = Join-Path $env:TEMP "pdf_converter_build_$buildToken"
$specPath = Join-Path $env:TEMP "pdf_converter_spec_$buildToken"
$finalExePath = Join-Path $releaseDir "PDFConverter.exe"
$iconPath = Resolve-Path ".\assets\app_icon.ico" -ErrorAction SilentlyContinue

& $pythonExe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $pythonExe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $pythonExe -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$iconArgs = @()
if ($iconPath) {
    $iconArgs = @("--icon", $iconPath.Path)
}

if (-not (Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

if (Test-Path $finalExePath) {
    Remove-Item -Force $finalExePath
}

& $pyInstallerExe --noconfirm --clean --onefile --windowed --distpath $distPath --workpath $workPath --specpath $specPath --name PDFConverter @iconArgs app.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Copy-Item -Path (Join-Path $distPath "PDFConverter.exe") -Destination $finalExePath -Force
