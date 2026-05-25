from __future__ import annotations

from pathlib import Path
from typing import Iterable

import img2pdf
from PIL import Image


SUPPORTED_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}

A4_PAGE_SIZE_PT = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
A4_MARGIN_MM = (10, 10)
A4_MARGIN_PT = tuple(img2pdf.mm_to_pt(value) for value in A4_MARGIN_MM)


def is_supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def classify_image_paths(
    paths: Iterable[str | Path],
    existing_paths: Iterable[Path] = (),
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
        if not is_supported_image(path):
            unsupported_count += 1
            continue

        seen.add(path)
        unique_paths.append(path)

    return unique_paths, duplicate_count, unsupported_count


def normalize_paths(paths: Iterable[str | Path]) -> list[Path]:
    unique_paths, _, _ = classify_image_paths(paths)
    return unique_paths


def validate_images(paths: Iterable[Path]) -> None:
    for path in paths:
        with Image.open(path) as image:
            image.verify()


def convert_images_to_pdf(image_paths: Iterable[Path], output_path: str | Path) -> Path:
    normalized = normalize_paths(image_paths)
    if not normalized:
        raise ValueError("변환할 이미지가 없습니다.")

    validate_images(normalized)
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
