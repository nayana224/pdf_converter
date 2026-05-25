# Release Smoke Test Checklist

## 1. Image to PDF

- Launch the app.
- Confirm `이미지 → PDF` mode is selected by default.
- Add 3 or more image files.
- Reorder the list and verify the order changes.
- Remove one selected image and verify it disappears.
- Try adding the same image again and confirm it is skipped.
- Save a PDF successfully.
- Open the saved PDF from the app.
- Confirm the preview updates after the list changes.

## 2. PDF Merge

- Switch to `PDF 병합` mode.
- Add at least 2 PDF files.
- Reorder the list and verify the order changes.
- Remove one selected PDF and verify it disappears.
- Try adding the same PDF again and confirm it is skipped.
- Confirm merge is blocked when only 1 PDF is present.
- Merge into a new output PDF successfully.
- Open the merged PDF from the app.
- Confirm the preview appears when 2 or more PDFs are present.

## 3. Progress Feedback

- Start an image-to-PDF export with several files.
- Confirm the progress bar becomes visible.
- Confirm the status text changes while processing.
- Confirm action buttons are disabled while processing.
- Confirm the UI returns to normal after success or failure.

## 4. Packaging

- Run `build_release.bat`.
- Confirm `release/PDFToolkit.exe` is created.
- Confirm `release/PDFToolkit-Setup.exe` is created when Inno Setup is installed.
- Launch the packaged EXE.
- Verify both modes open and basic actions still work.

