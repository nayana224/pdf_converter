from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

import img2pdf
import pikepdf
from PIL import Image

ProgressCallback = Callable[[int, int, str], None]

SUPPORTED_IMAGE_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}

A4_PAGE_SIZE_PT = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
A4_MARGIN_MM = (10, 10)
A4_MARGIN_PT = tuple(img2pdf.mm_to_pt(value) for value in A4_MARGIN_MM)


def is_supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def is_supported_pdf(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_PDF_EXTENSIONS


def _classify_paths(
    paths: Iterable[str | Path],
    existing_paths: Iterable[Path],
    validator: Callable[[Path], bool],
) -> tuple[list[Path], int, int]:
    unique_paths: list[Path] = []
    seen: set[Path] = set(existing_paths)
    duplicate_count = 0
    unsupported_count = 0

    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if path in seen:
            duplicate_count += 1
            continue
        if not validator(path):
            unsupported_count += 1
            continue

        seen.add(path)
        unique_paths.append(path)

    return unique_paths, duplicate_count, unsupported_count


def classify_image_paths(
    paths: Iterable[str | Path],
    existing_paths: Iterable[Path] = (),
) -> tuple[list[Path], int, int]:
    return _classify_paths(paths, existing_paths, is_supported_image)


def classify_pdf_paths(
    paths: Iterable[str | Path],
    existing_paths: Iterable[Path] = (),
) -> tuple[list[Path], int, int]:
    return _classify_paths(paths, existing_paths, is_supported_pdf)


def normalize_paths(paths: Iterable[str | Path]) -> list[Path]:
    unique_paths, _, _ = _classify_paths(paths, (), lambda path: path.is_file())
    return unique_paths


def _report_progress(
    callback: ProgressCallback | None,
    current: int,
    total: int,
    message: str,
) -> None:
    if callback is not None:
        callback(current, total, message)


def validate_images(
    paths: Iterable[Path],
    progress_callback: ProgressCallback | None = None,
) -> None:
    path_list = list(paths)
    total = len(path_list)

    for index, path in enumerate(path_list, start=1):
        _report_progress(progress_callback, index, total, f"Validating image {index}/{total}: {path.name}")
        with Image.open(path) as image:
            image.verify()


def validate_pdfs(
    paths: Iterable[Path],
    progress_callback: ProgressCallback | None = None,
) -> None:
    path_list = list(paths)
    total = len(path_list)

    for index, path in enumerate(path_list, start=1):
        _report_progress(progress_callback, index, total, f"Validating PDF {index}/{total}: {path.name}")
        with pikepdf.Pdf.open(path):
            pass


def get_pdf_page_count(pdf_path: str | Path) -> int:
    path = Path(pdf_path).expanduser().resolve()
    with pikepdf.Pdf.open(path) as pdf:
        return len(pdf.pages)


def convert_images_to_pdf(
    image_paths: Iterable[Path],
    output_path: str | Path,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    normalized, _, _ = classify_image_paths(image_paths)
    if not normalized:
        raise ValueError("No images were provided for conversion.")

    validate_images(normalized, progress_callback=progress_callback)
    total_steps = len(normalized) + 1
    _report_progress(progress_callback, total_steps, total_steps, "Building PDF file...")

    layout_fun = img2pdf.get_layout_fun(
        pagesize=A4_PAGE_SIZE_PT,
        border=A4_MARGIN_PT,
    )

    destination = Path(output_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb") as pdf_file:
        pdf_file.write(
            img2pdf.convert(
                [str(path) for path in normalized],
                layout_fun=layout_fun,
                rotation=img2pdf.Rotation.ifvalid,
            )
        )

    return destination


def merge_pdfs(
    pdf_paths: Iterable[Path],
    output_path: str | Path,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    normalized, _, _ = classify_pdf_paths(pdf_paths)
    if len(normalized) < 2:
        raise ValueError("At least two PDF files are required for merge.")

    validate_pdfs(normalized, progress_callback=progress_callback)
    total_steps = len(normalized) + 1
    destination = Path(output_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    _report_progress(progress_callback, total_steps, total_steps, "Merging PDF pages...")
    merged_pdf = pikepdf.Pdf.new()

    for path in normalized:
        with pikepdf.Pdf.open(path) as source_pdf:
            merged_pdf.pages.extend(source_pdf.pages)

    merged_pdf.save(destination)
    return destination


def split_pdf(
    pdf_paths: Iterable[Path],
    output_dir: str | Path,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    normalized, _, _ = classify_pdf_paths(pdf_paths)
    if len(normalized) != 1:
        raise ValueError("Exactly one PDF file is required for split.")

    source_path = normalized[0]
    validate_pdfs([source_path], progress_callback=progress_callback)

    destination_dir = Path(output_dir).expanduser().resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)

    with pikepdf.Pdf.open(source_path) as source_pdf:
        page_count = len(source_pdf.pages)
        total_steps = page_count + 1

        for page_index, page in enumerate(source_pdf.pages, start=1):
            _report_progress(
                progress_callback,
                page_index + 1,
                total_steps,
                f"Saving split page {page_index}/{page_count}...",
            )
            split_document = pikepdf.Pdf.new()
            split_document.pages.append(page)
            split_document.save(destination_dir / f"{source_path.stem}-page-{page_index:03d}.pdf")

    return destination_dir
