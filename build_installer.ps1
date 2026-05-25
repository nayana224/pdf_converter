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

    throw "Inno Setup 6를 찾지 못했습니다. 설치 후 다시 시도하거나 -InnoSetupCompiler 경로를 직접 지정해 주세요."
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$releaseDir = Join-Path $projectRoot "release"
$exePath = Join-Path $releaseDir "PDFConverter.exe"
$finalSetupPath = Join-Path $releaseDir "PDFConverter-Setup.exe"
$isccPath = Resolve-InnoSetupCompiler -RequestedCompiler $InnoSetupCompiler

if (-not (Test-Path $exePath)) {
    Write-Host "[1/3] 실행 파일이 없어 먼저 EXE 빌드를 시작합니다..."
    powershell -ExecutionPolicy Bypass -File (Join-Path $projectRoot "build_exe.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "선행 EXE 빌드에 실패했습니다."
    }
}
else {
    Write-Host "[1/3] 기존 EXE 빌드 결과 재사용 중..."
}

if (-not (Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

if (Test-Path $finalSetupPath) {
    Remove-Item -LiteralPath $finalSetupPath -Force
}

Write-Host "[2/3] 설치 파일 빌드 중..."
& $isccPath (Join-Path $projectRoot "installer\PDFConverter.iss")
if ($LASTEXITCODE -ne 0) {
    throw "설치 파일 빌드에 실패했습니다."
}

Write-Host "[3/3] 완료"
Write-Host "생성 파일: $finalSetupPath"
