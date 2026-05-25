# PDF Converter

A simple Windows desktop app for two common local PDF tasks:

- convert multiple images into one PDF
- merge multiple PDF files into one PDF

## For Normal Users

If you only want to use the app, do not build it yourself.

Download one of these files from the GitHub `Releases` page:

- `PDFConverter-Setup.exe`
  Recommended for most users. This is the standard installer.
- `PDFConverter.exe`
  Portable version. Runs without installation.

### Recommended option

Use `PDFConverter-Setup.exe`.

Why:

- easier for non-technical users
- normal install/uninstall flow
- desktop shortcut option
- easier to replace with a newer version later

### Updating to a newer version

The normal update path is simple:

1. Close the app if it is running.
2. Run the new `PDFConverter-Setup.exe`.
3. Complete the installer.

The installer is configured to reuse the previous install location and to close the running app when possible.

## Features

### Image to PDF

- drag and drop image files
- add files from a file picker
- reorder items before export
- remove selected items
- skip duplicate files automatically
- skip unsupported files automatically
- preview the generated PDF
- open the saved PDF from the app
- export with an A4-based layout

### PDF Merge

- drag and drop PDF files
- add PDF files from a file picker
- reorder PDFs before merge
- remove selected items
- skip duplicate files automatically
- block merge when fewer than 2 PDFs are selected
- preview the merged result
- open the merged PDF from the app

### In-App Feedback

- progress bar during export and merge
- status text updates during processing
- action buttons disabled while processing

## Supported File Types

### Image input

- `JPG`
- `JPEG`
- `PNG`
- `BMP`
- `TIFF`
- `WEBP`
- `GIF`

### PDF input

- `PDF`

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

If the build says the output file is locked, close any running `PDFConverter.exe` window and try again.

## Build the Full Release Locally

This creates:

- `release\PDFConverter.exe`
- `release\PDFConverter-Setup.exe` if `Inno Setup 6` is installed

### Option 1: Double-click

Double-click:

- `build_release.bat`

This will:

- run the full release build
- keep the console open if the build fails
- open the `release` folder automatically when the build succeeds

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

### Create a versioned GitHub release

Paste these commands into **PowerShell**:

```powershell
cd "C:\path\to\pdf_converter-main"
git tag v1.0.0
git push origin v1.0.0
```

After that, GitHub Actions builds the release files and attaches them to the GitHub `Releases` page.

## Recommended Release Flow

1. Push your latest code to GitHub.
2. Create and push a version tag such as `v1.0.0`.
3. Wait for the GitHub Actions workflow to finish.
4. Share `PDFConverter-Setup.exe` from the GitHub `Releases` page.

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

## Notes

- The build scripts create `.venv` automatically if it does not exist.
- `build_release.bat` is included for people who do not want to deal with PowerShell execution policy manually.
- The recommended file for non-technical users is `PDFConverter-Setup.exe`.
