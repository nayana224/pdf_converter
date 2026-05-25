# PDF Toolkit Requirements

## Goal

Build a Windows desktop app that supports all of the following:

- converting multiple images into a single PDF
- merging multiple PDF files into a single PDF
- splitting one PDF into separate page files

The app should be easy to run locally, easy to package as an EXE/installer, and easy for non-technical users to understand.

## Current Scope

This phase adds the next expansion item:

1. PDF split support
2. updated mode structure for three workflows
3. release docs that cover the new split flow

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

The existing PDF merge flow must continue to support:

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

### 3. PDF Split

The app must add a PDF split workflow.

Required behavior:

- users can add one PDF file for splitting
- users can remove the selected PDF and choose a different one
- users can choose a destination folder for split output
- the app creates one PDF file per page
- each split file uses a predictable name such as `source-page-001.pdf`
- the result folder can be opened from the app after success

Validation rules:

- split mode should accept only 1 PDF at a time
- duplicate or additional PDFs beyond the first should be rejected with a clear message
- unsupported files should be skipped
- broken or unreadable PDFs should show a clear error message

### 4. Mode Separation

The app should clearly separate the three workflows:

- Image to PDF
- PDF Merge
- PDF Split

Recommended UX:

- provide three mode buttons or tabs near the top of the screen
- update helper text, file picker filters, and action button text based on the active mode
- keep the overall layout familiar so the app still feels simple

### 5. Progress and Status Feedback

The app must show visible progress feedback while doing export work.

Minimum acceptable behavior:

- disable conflicting actions while conversion, merge, or split is running
- show a status message such as `Processing...`, `Merging PDFs...`, or `Splitting PDF...`
- show a progress indicator in the window
- restore the UI after success or failure

Nice-to-have behavior:

- show different progress text for image conversion, PDF merge, and PDF split
- keep the last success message visible after the task finishes

## Non-Functional Requirements

- The app should remain a local-only desktop utility.
- The app should not require uploading files to any external service.
- The app should continue to work as a packaged EXE.
- The app should remain easy to distribute through `PDFToolkit.exe` and `PDFToolkit-Setup.exe`.

## Dependencies

The current stack includes:

- `PySide6`
- `img2pdf`
- `Pillow`
- `pikepdf`

For PDF split, the implementation should reuse the current PDF library stack when possible.

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

### PDF Split Checklist

- switch to split mode
- add 1 PDF file
- try adding a second PDF and confirm the app rejects it clearly
- remove the selected PDF and add a different one
- choose a destination folder successfully
- confirm one PDF file per page is created
- open the created result folder from the app

### Packaging Checklist

- run `build_release.bat`
- verify `release/PDFToolkit.exe` is created
- verify `release/PDFToolkit-Setup.exe` is created when Inno Setup is installed
- launch the packaged EXE and verify all three modes open normally

## Out of Scope for This Phase

The following features are not required in this phase:

- page extraction
- page rotation
- custom page size options
- compression/quality presets
- OCR
- auto-update

## Definition of Done

This phase is complete when:

- the app supports Image to PDF, PDF Merge, and PDF Split
- users can switch all three modes in the GUI
- conversion, merge, and split operations show visible progress feedback
- the smoke-test checklist is documented for the new mode
- the packaged app still builds successfully
