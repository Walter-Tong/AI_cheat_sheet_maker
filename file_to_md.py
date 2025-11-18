from __future__ import annotations

"""Minimal utilities for converting course files to Markdown.

Supported cases:
- Text files (currently: .md, .txt): returned or lightly normalised.
- Text PDFs: text extracted via pypdf and wrapped into Markdown.
- Image-only PDFs: pages rendered to images and OCR'd via pytesseract,
  then concatenated into Markdown.

This module does NOT call any LLMs. Higher-level logic (agent.py)
will decide how to use the resulting Markdown.
"""

from pathlib import Path
from typing import Callable, Optional


class ConversionError(Exception):
    """Raised when a document cannot be converted to Markdown."""


QualityChecker = Callable[[str], bool]
OcrFunc = Callable[[bytes], str]


def convert_to_markdown(
    path: str | Path,
    quality_checker: Optional[QualityChecker] = None,
    ocr_func: Optional[OcrFunc] = None,
    use_ocr: bool = False,
) -> Path:
    """Convert a document to Markdown and return the .md file path.

    Handles three cases:
    1. Text files (.md, .txt): .md is returned as-is; .txt is wrapped
       into a sibling .md file.
    2. Text PDFs: text is extracted with pypdf and written as Markdown.
    3. Image-only PDFs: pages are rendered with pdf2image and OCR'd with
       pytesseract, then written as Markdown.
    """

    src_path = Path(path)
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    suffix = src_path.suffix.lower()

    # Case 1: plain text files.
    if suffix == ".md":
        return src_path
    if suffix == ".txt":
        md_path = src_path.with_suffix(".md")
        if md_path.exists():
            return md_path
        text = src_path.read_text(encoding="utf-8", errors="ignore")
        markdown = text.strip() + "\n"
        if quality_checker is not None and not quality_checker(markdown):
            raise ConversionError(f"Text from {src_path} failed quality check")
        md_path.write_text(markdown, encoding="utf-8")
        return md_path

    # For non-text inputs, if a sibling .md already exists, reuse it.
    md_path = src_path.with_suffix(".md")
    if md_path.exists():
        return md_path

    if suffix == ".pdf":
        if use_ocr:
            markdown_text = _convert_pdf_to_markdown_ocr(src_path, ocr_func=ocr_func)
        else:
            markdown_text = _convert_pdf_to_markdown_text(src_path)
    else:
        raise ConversionError(f"Unsupported file type for conversion: {suffix}")

    if quality_checker is not None and not quality_checker(markdown_text):
        raise ConversionError(f"Extracted text for {src_path} failed quality check")

    md_path.write_text(markdown_text, encoding="utf-8")
    return md_path


def _convert_pdf_to_markdown_text(pdf_path: Path) -> str:
    """Convert a text-based PDF to Markdown using pypdf only."""

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ConversionError("pypdf is required for PDF conversion but is not installed") from exc

    reader = PdfReader(str(pdf_path))
    page_texts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        page_texts.append(text)

    lines: list[str] = []
    for idx, text in enumerate(page_texts, start=1):
        clean = text.strip()
        if not clean:
            continue
        lines.append(f"Page {idx}")
        lines.append("")
        lines.append(clean)
        lines.append("")

    if not lines:
        raise ConversionError(f"No usable text extracted from PDF: {pdf_path}")

    return "\n".join(lines)


def _convert_pdf_to_markdown_ocr(pdf_path: Path, ocr_func: Optional[OcrFunc]) -> str:
    """Convert a PDF to Markdown via OCR on rendered page images."""

    if ocr_func is None:
        raise ConversionError("OCR conversion requested but no OCR function was provided")

    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ConversionError("PyMuPDF (fitz) is required for OCR-based PDF conversion but is not installed") from exc

    doc = fitz.open(str(pdf_path))
    if doc.page_count == 0:
        raise ConversionError(f"No pages in PDF for OCR: {pdf_path}")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _render_and_ocr(page_index: int) -> tuple[int, str]:
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
        image_bytes = pix.tobytes("png")
        print(f"Running OCR for page {page_index + 1}...")
        text = ocr_func(image_bytes)
        print(f"Finished OCR for page {page_index + 1}.")
        return page_index, (text or "").strip()

    results: dict[int, str] = {}

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_render_and_ocr, idx): idx for idx in range(doc.page_count)}
        for future in as_completed(futures):
            page_index, clean = future.result()
            if clean:
                results[page_index] = clean

    if not results:
        raise ConversionError(f"OCR produced no content for PDF: {pdf_path}")

    lines: list[str] = []
    for idx in sorted(results):
        lines.append(f"Page {idx + 1}")
        lines.append("")
        lines.append(results[idx])
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":  # Simple manual testing entrypoint.
    import argparse

    from openai_client import llm_ocr

    parser = argparse.ArgumentParser(description="Convert a file to Markdown.")
    parser.add_argument("path", help="Path to the source file")
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Use LLM OCR for PDF files instead of text extraction",
    )
    args = parser.parse_args()

    src = Path(args.path)

    def _dummy_quality_checker(text: str) -> bool:  # pragma: no cover
        return bool(text.strip())

    ocr_cb = llm_ocr if args.ocr else None

    out = convert_to_markdown(
        src,
        quality_checker=_dummy_quality_checker,
        ocr_func=ocr_cb,
        use_ocr=bool(args.ocr),
    )
    print(out)
