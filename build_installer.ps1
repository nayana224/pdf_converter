param(
    [string]$InnoSetupCompiler = "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
)

if (-not (Test-Path $InnoSetupCompiler)) {
    Write-Error "Inno Setup 6가 설치되어 있지 않습니다. 설치 후 다시 실행해 주세요: $InnoSetupCompiler"
    exit 1
}

if (-not (Test-Path ".\release\PDFConverter.exe")) {
    Write-Host "release\PDFConverter.exe가 없어 먼저 exe 빌드를 실행합니다."
    powershell -ExecutionPolicy Bypass -File ".\build_exe.ps1"
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$releaseDir = ".\release"
$outputToken = Get-Date -Format "yyyyMMdd_HHmmss"
$tempOutputDir = Join-Path $env:TEMP "pdf_converter_installer_$outputToken"
$finalSetupPath = Join-Path $releaseDir "PDFConverter-Setup.exe"

if (-not (Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

if (Test-Path $finalSetupPath) {
    Remove-Item -Force $finalSetupPath
}

& $InnoSetupCompiler "/O$tempOutputDir" ".\installer\PDFConverter.iss"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Copy-Item -Path (Join-Path $tempOutputDir "PDFConverter-Setup.exe") -Destination $finalSetupPath -Force
