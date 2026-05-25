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

    throw "Python 3.11 or newer is required. Install Python and try again."
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
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
}

function Remove-OldFileIfPossible {
    param([string]$PathToRemove)

    if (-not (Test-Path $PathToRemove)) {
        return
    }

    try {
        Remove-Item -LiteralPath $PathToRemove -Force
    }
    catch {
        throw @"
The existing output file is locked and could not be replaced:
$PathToRemove

Please close PDFConverter.exe if it is still running,
close any Explorer window previewing the file,
and run the build again.
"@
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
    Write-Host "[1/5] Creating virtual environment..."
    Invoke-Python $pythonCommandResolved -m venv $venvDir
}
else {
    Write-Host "[1/5] Reusing existing virtual environment..."
}

Write-Host "[2/5] Installing or updating build tools..."
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

Remove-OldFileIfPossible -PathToRemove $finalExePath

$iconArgs = @()
if (Test-Path $iconPath) {
    $iconArgs = @("--icon", $iconPath)
}

Write-Host "[3/5] Building with PyInstaller..."
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
    throw "PyInstaller build failed."
}

Write-Host "[4/5] Copying final executable..."
Copy-Item -LiteralPath (Join-Path $distPath "PDFConverter.exe") -Destination $finalExePath -Force

Write-Host "[5/5] Done"
Write-Host "Created file: $finalExePath"
