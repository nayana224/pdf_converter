param(
    [string]$PythonCommand = "",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-PythonCommand {
    param([string]$RequestedCommand)

    if ($RequestedCommand) {
        return $RequestedCommand
    }

    $candidates = @(
        @("py", "-3.14"),
        @("py", "-3.13"),
        @("py", "-3.12"),
        @("py", "-3.11"),
        @("py", "-3"),
        @("python")
    )

    foreach ($candidate in $candidates) {
        try {
            if ($candidate.Count -eq 1) {
                & $candidate[0] --version *> $null
            }
            else {
                & $candidate[0] $candidate[1] --version *> $null
            }

            if ($LASTEXITCODE -eq 0) {
                return ($candidate -join " ")
            }
        }
        catch {
        }
    }

    throw "Python 3.11 이상이 필요합니다. Python을 설치한 뒤 다시 시도해 주세요."
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    $parts = $Command -split " "
    $exe = $parts[0]
    $prefix = @()
    if ($parts.Length -gt 1) {
        $prefix = $parts[1..($parts.Length - 1)]
    }

    & $exe @prefix @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "명령 실행 실패: $Command $($Arguments -join ' ')"
    }
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$pythonCommandResolved = Resolve-PythonCommand -RequestedCommand $PythonCommand
$venvDir = Join-Path $projectRoot ".venv"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$pyInstallerExe = Join-Path $venvDir "Scripts\pyinstaller.exe"
$releaseDir = Join-Path $projectRoot "release"
$buildToken = Get-Date -Format "yyyyMMdd_HHmmss"
$distPath = Join-Path $env:TEMP "pdf_converter_dist_$buildToken"
$workPath = Join-Path $env:TEMP "pdf_converter_build_$buildToken"
$specPath = Join-Path $env:TEMP "pdf_converter_spec_$buildToken"
$finalExePath = Join-Path $releaseDir "PDFConverter.exe"
$iconPath = Join-Path $projectRoot "assets\app_icon.ico"

if (-not (Test-Path $pythonExe)) {
    Write-Host "[1/5] 가상환경 생성 중..."
    Invoke-Python $pythonCommandResolved -m venv $venvDir
}
else {
    Write-Host "[1/5] 기존 가상환경 재사용 중..."
}

Write-Host "[2/5] 빌드 도구 설치/업데이트 중..."
Invoke-Python $pythonExe -m pip install --upgrade pip
Invoke-Python $pythonExe -m pip install -r requirements.txt pyinstaller

if ($Clean) {
    foreach ($path in @($distPath, $workPath, $specPath)) {
        if (Test-Path $path) {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
    }
}

if (-not (Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

if (Test-Path $finalExePath) {
    Remove-Item -LiteralPath $finalExePath -Force
}

$iconArgs = @()
if (Test-Path $iconPath) {
    $iconArgs = @("--icon", $iconPath)
}

Write-Host "[3/5] PyInstaller 빌드 중..."
& $pyInstallerExe `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --distpath $distPath `
    --workpath $workPath `
    --specpath $specPath `
    --name PDFConverter `
    @iconArgs `
    app.py
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller 빌드에 실패했습니다."
}

Write-Host "[4/5] 결과 파일 정리 중..."
Copy-Item -LiteralPath (Join-Path $distPath "PDFConverter.exe") -Destination $finalExePath -Force

Write-Host "[5/5] 완료"
Write-Host "생성 파일: $finalExePath"
