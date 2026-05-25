param(
    [string]$InnoSetupCompiler = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-InnoSetupCompiler {
    param([string]$RequestedCompiler)

    if ($RequestedCompiler -and (Test-Path $RequestedCompiler)) {
        return (Resolve-Path $RequestedCompiler).Path
    }

    $candidates = @(
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    $pathCommand = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($pathCommand) {
        return $pathCommand.Source
    }

    throw "Inno Setup 6 was not found. Install it or pass -InnoSetupCompiler with the full path."
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$releaseDir = Join-Path $projectRoot "release"
$exePath = Join-Path $releaseDir "PDFToolkit.exe"
$finalSetupPath = Join-Path $releaseDir "PDFToolkit-Setup.exe"
$isccPath = Resolve-InnoSetupCompiler -RequestedCompiler $InnoSetupCompiler

if (-not (Test-Path $exePath)) {
    Write-Host "[1/3] EXE not found. Starting EXE build first..."
    powershell -ExecutionPolicy Bypass -File (Join-Path $projectRoot "build_exe.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "The prerequisite EXE build failed."
    }
}
else {
    Write-Host "[1/3] Reusing existing EXE build output..."
}

if (-not (Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

if (Test-Path $finalSetupPath) {
    Remove-Item -LiteralPath $finalSetupPath -Force
}

Write-Host "[2/3] Building installer..."
& $isccPath (Join-Path $projectRoot "installer\PDFToolkit.iss")
if ($LASTEXITCODE -ne 0) {
    throw "Installer build failed."
}

Write-Host "[3/3] Done"
Write-Host "Created file: $finalSetupPath"

