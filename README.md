# PDF Converter

A simple Windows desktop app for converting multiple images into a single PDF.

## What This App Does

- Drag and drop multiple images into the app
- Reorder images before saving
- Remove selected items
- Skip duplicate or unsupported files automatically
- Preview the generated PDF
- Open the saved PDF directly after export
- Export pages in A4 layout

## Supported Image Formats

- `JPG`
- `JPEG`
- `PNG`
- `BMP`
- `TIFF`
- `WEBP`
- `GIF`

## Easiest Option for End Users

If you just want to use the app, do not build it yourself.

Download one of these files from the GitHub `Releases` page:

- `PDFConverter-Setup.exe`
  Recommended for most users. Installs the app normally.
- `PDFConverter.exe`
  Portable version. Runs without installation.

## Run Locally

Open **PowerShell** and paste the commands below exactly.

```powershell
cd "C:\path\to\pdf_converter-main"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If `py` is not available on your machine, try:

```powershell
cd "C:\path\to\pdf_converter-main"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Build the EXE Locally

This creates:

- `release\PDFConverter.exe`

Paste this into **PowerShell**:

```powershell
cd "C:\path\to\pdf_converter-main"
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

## Build the Full Release Locally

This creates:

- `release\PDFConverter.exe`
- `release\PDFConverter-Setup.exe` if `Inno Setup 6` is installed

### Option 1: Double-click

Double-click:

- `build_release.bat`

### Option 2: PowerShell

Paste this into **PowerShell**:

```powershell
cd "C:\path\to\pdf_converter-main"
powershell -ExecutionPolicy Bypass -File .\build_release.ps1
```

To build only the EXE and skip the installer:

```powershell
cd "C:\path\to\pdf_converter-main"
powershell -ExecutionPolicy Bypass -File .\build_release.ps1 -SkipInstaller
```

## Installer Build Requirement

To create `PDFConverter-Setup.exe`, you need `Inno Setup 6`.

The script tries these locations automatically:

- `%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`
- `%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe`
- `%ProgramFiles%\Inno Setup 6\ISCC.exe`
- `ISCC.exe` from your `PATH`

If needed, you can pass the compiler path manually:

```powershell
cd "C:\path\to\pdf_converter-main"
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1 -InnoSetupCompiler "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

## GitHub Automatic Build and Release

This repository includes a GitHub Actions workflow:

- `.github/workflows/windows-release.yml`

It automatically:

- sets up Python on a Windows runner
- installs Inno Setup
- builds the EXE and installer
- uploads build artifacts
- publishes release files when you push a version tag

### Manual workflow run

You can also run the workflow manually from the GitHub Actions tab.

### Create a versioned GitHub release

Paste these commands into **PowerShell**:

```powershell
cd "C:\path\to\pdf_converter-main"
git tag v1.0.0
git push origin v1.0.0
```

After that, GitHub Actions builds the release files and attaches them to the GitHub `Releases` page.

## Recommended Release Flow

For sharing with other people, this is the easiest process:

1. Push your latest code to GitHub.
2. Create and push a version tag such as `v1.0.0`.
3. Wait for the GitHub Actions workflow to finish.
4. Share `PDFConverter-Setup.exe` from the GitHub `Releases` page.

## Project Structure

```text
pdf_converter-main/
├─ app.py
├─ build_exe.ps1
├─ build_installer.ps1
├─ build_release.ps1
├─ build_release.bat
├─ requirements.txt
├─ assets/
├─ installer/
├─ pdf_converter/
└─ .github/workflows/
```

## Notes

- The build scripts create `.venv` automatically if it does not exist.
- `build_release.bat` is included for people who do not want to deal with PowerShell execution policy manually.
- The recommended file for non-technical users is `PDFConverter-Setup.exe`.
