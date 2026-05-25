param(
    [switch]$SkipInstaller,
    [string]$PythonCommand = "",
    [string]$InnoSetupCompiler = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "PDF Converter 배포 빌드를 시작합니다."

$exeArgs = @()
if ($PythonCommand) {
    $exeArgs += @("-PythonCommand", $PythonCommand)
}

powershell -ExecutionPolicy Bypass -File (Join-Path $projectRoot "build_exe.ps1") @exeArgs
if ($LASTEXITCODE -ne 0) {
    throw "EXE 빌드에 실패했습니다."
}

if ($SkipInstaller) {
    Write-Host "설치 파일 빌드는 건너뛰었습니다."
    exit 0
}

$installerArgs = @()
if ($InnoSetupCompiler) {
    $installerArgs += @("-InnoSetupCompiler", $InnoSetupCompiler)
}

powershell -ExecutionPolicy Bypass -File (Join-Path $projectRoot "build_installer.ps1") @installerArgs
if ($LASTEXITCODE -ne 0) {
    throw "설치 파일 빌드에 실패했습니다."
}

Write-Host "배포 빌드가 완료되었습니다. release 폴더를 확인해 주세요."
