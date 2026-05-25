# PDF Converter Requirements

## Goal

Build a Windows desktop app that supports both:

- converting multiple images into a single PDF
- merging multiple PDF files into a single PDF

The app should be easy to run locally, easy to package as an EXE/installer, and easy for non-technical users to understand.

## Current Scope

This phase adds three priority items:

1. PDF merge support
2. visible progress/status feedback during export work
3. a lightweight smoke-test checklist for release verification

## Functional Requirements

### 1. Image to PDF

The existing image-to-PDF flow must continue to support:

- drag and drop image files into the list
- selecting image files from a file dialog
- reordering the list before export
- removing selected items
- skipping duplicate files
- skipping unsupported files
- previewing the generated PDF when preview support is available
- saving the result as a single PDF
- reopening the saved PDF from the app

### 2. PDF Merge

The app must add a PDF merge workflow.

Required behavior:

- users can add multiple PDF files
- users can reorder the PDF list before merge
- users can remove selected PDF files
- users can merge the selected PDFs into one output file
- the output path can be chosen with a save dialog
- the merged PDF can be reopened from the app

Validation rules:

- if fewer than 2 PDF files are selected, merge should not proceed
- duplicate PDF files should be skipped
- unsupported files should be skipped
- broken or unreadable PDF files should show a clear error message

### 3. Mode Separation

The app should clearly separate the two workflows:

- Image to PDF
- PDF Merge

Recommended UX:

- provide two mode buttons or tabs near the top of the screen
- update helper text, file picker filters, and action button text based on the active mode
- keep the overall layout familiar so the app still feels simple

### 4. Progress and Status Feedback

The app must show visible progress feedback while doing export work.

Minimum acceptable behavior:

- disable conflicting actions while conversion or merge is running
- show a status message such as `Processing...` or `Merging PDFs...`
- show a progress indicator in the window
- restore the UI after success or failure

Nice-to-have behavior:

- show different progress text for image conversion and PDF merge
- keep the last success message visible after the task finishes

## Non-Functional Requirements

- The app should remain a local-only desktop utility.
- The app should not require uploading files to any external service.
- The app should continue to work as a packaged EXE.
- The app should remain easy to distribute through `PDFConverter.exe` and `PDFConverter-Setup.exe`.

## Dependencies

The current stack includes:

- `PySide6`
- `img2pdf`
- `Pillow`

For PDF merge, the implementation may use an already available PDF library such as `pikepdf`, or add an explicit dependency if needed.

## Release Smoke-Test Checklist

Before release, verify the following manually.

### Image to PDF Checklist

- add multiple supported images
- reorder them and confirm the output order matches
- remove one selected image and confirm it disappears
- try adding duplicates and confirm they are skipped
- save a PDF successfully
- open the saved PDF from the app
- verify preview updates when the image list changes

### PDF Merge Checklist

- add at least 2 PDF files
- reorder them and confirm merge order matches
- remove one selected PDF and confirm it disappears
- try adding duplicates and confirm they are skipped
- merge into a new output PDF successfully
- open the merged PDF from the app
- try merging with only 1 PDF and confirm the app blocks the action clearly

### Packaging Checklist

- run `build_release.bat`
- verify `release/PDFConverter.exe` is created
- verify `release/PDFConverter-Setup.exe` is created when Inno Setup is installed
- launch the packaged EXE and verify both modes open normally

## Out of Scope for This Phase

The following features are not required in this phase:

- PDF split
- page extraction
- page rotation
- custom page size options
- compression/quality presets
- OCR
- auto-update

## Definition of Done

This phase is complete when:

- the app supports both Image to PDF and PDF Merge
- users can switch modes in the GUI
- export and merge operations show visible progress feedback
- the smoke-test checklist is documented
- the packaged app still builds successfully
