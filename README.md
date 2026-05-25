# PDF Toolkit

Convert images to PDF and merge PDF files on Windows.

## Quick Start

If you just want to use the app, download it from the GitHub `Releases` page.

Recommended file:

- `PDFToolkit-Setup.exe`

Steps:

1. Download `PDFToolkit-Setup.exe` from the latest release.
2. Run the installer.
3. Launch `PDF Toolkit` from the Start menu or desktop shortcut.

Portable option:

- `PDFToolkit.exe`
  Use this if you want to run the app without installing it.

## Main Features

- Convert multiple images into one PDF
- Merge multiple PDF files into one PDF
- Drag and drop files into the app
- Reorder files before saving
- Remove selected items
- Skip duplicate files automatically
- Preview the output PDF inside the app
- Show progress feedback during export and merge

## Supported Input Types

### Images

- `JPG`
- `JPEG`
- `PNG`
- `BMP`
- `TIFF`
- `WEBP`
- `GIF`

### PDF

- `PDF`

## Download Options

- `PDFToolkit-Setup.exe`
  Recommended for most users. Installs the app normally.
- `PDFToolkit.exe`
  Portable version. Runs without installation.

## Updating to a New Version

1. Close the app if it is running.
2. Download the newest `PDFToolkit-Setup.exe` from `Releases`.
3. Run the installer again.

The installer is configured to reuse the previous install location and close the app when possible.

## For Developers

### Run Locally

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

### Build the EXE Locally

```powershell
cd "C:\path\to\pdf_converter-main"
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

If the build says the output file is locked, close any running `PDFToolkit.exe` window and try again.

### Build the Full Release Locally

Double-click:

- `build_release.bat`

Or run:

```powershell
cd "C:\path\to\pdf_converter-main"
powershell -ExecutionPolicy Bypass -File .\build_release.ps1
```

To build only the EXE and skip the installer:

```powershell
cd "C:\path\to\pdf_converter-main"
powershell -ExecutionPolicy Bypass -File .\build_release.ps1 -SkipInstaller
```

### Installer Build Requirement

To create `PDFToolkit-Setup.exe`, you need `Inno Setup 6`.

If needed, you can pass the compiler path manually:

```powershell
cd "C:\path\to\pdf_converter-main"
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1 -InnoSetupCompiler "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

### GitHub Actions Release Flow

This repository includes a GitHub Actions workflow:

- `.github/workflows/windows-release.yml`

Typical release flow:

```powershell
cd "C:\path\to\pdf_converter-main"
git push origin main
git tag v1.0.0
git push origin v1.0.0
```

That workflow builds:

- `PDFToolkit.exe`
- `PDFToolkit-Setup.exe`

and attaches them to the GitHub `Releases` page.

## Related Docs

- `docs/pdf_converter.md`
- `docs/release_smoke_test.md`

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
├─ docs/
├─ installer/
├─ pdf_converter/
└─ .github/workflows/
```


