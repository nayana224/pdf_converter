param(
    [switch]$SkipInstaller,
    [string]$PythonCommand = "",
    [string]$InnoSetupCompiler = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "Starting PDF Converter release build..."

$exeArgs = @()
if ($PythonCommand) {
    $exeArgs += @("-PythonCommand", $PythonCommand)
}

powershell -ExecutionPolicy Bypass -File (Join-Path $projectRoot "build_exe.ps1") @exeArgs
if ($LASTEXITCODE -ne 0) {
    throw "EXE build failed."
}

if ($SkipInstaller) {
    Write-Host "Installer build skipped."
    exit 0
}

$installerArgs = @()
if ($InnoSetupCompiler) {
    $installerArgs += @("-InnoSetupCompiler", $InnoSetupCompiler)
}

powershell -ExecutionPolicy Bypass -File (Join-Path $projectRoot "build_installer.ps1") @installerArgs
if ($LASTEXITCODE -ne 0) {
    throw "Installer build failed."
}

Write-Host "Release build complete. Check the release folder."
