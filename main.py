from __future__ import annotations

"""Entry point for the cheatsheet coverage agent.

Usage:
    python main.py CS231

This will:
- Locate the course directory under COURSES_BASE_DIR.
- Convert relevant files in lecture_notes, past_papers, and
  assignment/question to Markdown using `file_to_md`.
- Read the cheatsheet (MD or PDF converted to MD).
- Call the agent to compute a coverage report and write it to
  REPORTS_DIR/<course_code>_coverage_report.md.

Per-folder OCR behaviour for PDFs is controlled via environment
variables (defaults to text extraction):
- LECTURE_NOTES_USE_OCR ("true"/"false")
- PAST_PAPERS_USE_OCR
- ASSIGNMENT_USE_OCR
- CHEATSHEET_USE_OCR
"""

import os
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

from agent import CourseCorpus, check_coverage
from file_to_md import ConversionError, convert_to_markdown
from openai_client import llm_ocr


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


def _gather_markdown_files(base_dir: Path, use_ocr: bool) -> list[str]:
    """Convert supported files under a directory tree to Markdown.

    Returns a list of Markdown strings, one per file.
    """

    markdown_texts: list[str] = []
    if not base_dir.exists():
        return markdown_texts

    for path in sorted(base_dir.rglob("*")):
        if path.is_dir():
            continue
        suffix = path.suffix.lower()
        if suffix not in {".md", ".txt", ".pdf"}:
            continue

        try:
            md_path = convert_to_markdown(
                path,
                ocr_func=llm_ocr if use_ocr else None,
                use_ocr=use_ocr if suffix == ".pdf" else False,
            )
            markdown_texts.append(md_path.read_text(encoding="utf-8", errors="ignore"))
        except ConversionError as exc:
            print(f"[WARN] Skipping {path} due to conversion error: {exc}")

    return markdown_texts


def _load_cheatsheet(course_dir: Path, use_ocr: bool) -> str:
    """Load the cheatsheet for a course as Markdown text.

    Behaviour:
    - If `cheatsheet.md` exists, read and return it directly.
    - If only `cheatsheet.pdf` exists, always convert it on-the-fly via
      `convert_to_markdown` but do not rely on or reuse any previously
      generated Markdown copy by name; the content is read and only the
      text is used by the agent.
    """

    md_path = course_dir / "cheatsheet.md"
    pdf_path = course_dir / "cheatsheet.pdf"

    if md_path.exists():
        return md_path.read_text(encoding="utf-8", errors="ignore")
    if pdf_path.exists():
        try:
            # Always convert from the PDF source so we get a fresh view
            # of the cheatsheet content for this run.
            md_converted = convert_to_markdown(
                pdf_path,
                ocr_func=llm_ocr if use_ocr else None,
                use_ocr=use_ocr,
            )
        except ConversionError as exc:
            raise SystemExit(f"Failed to convert cheatsheet PDF: {exc}") from exc
        return md_converted.read_text(encoding="utf-8", errors="ignore")

    raise SystemExit(f"No cheatsheet.md or cheatsheet.pdf found in {course_dir}")


def main() -> None:
    load_dotenv()

    import argparse

    parser = argparse.ArgumentParser(description="Cheatsheet coverage agent")
    parser.add_argument("course_code", help="Course code, e.g. CS231")
    args = parser.parse_args()

    base_dir = Path(os.getenv("COURSES_BASE_DIR", "./course"))
    reports_dir = Path(os.getenv("REPORTS_DIR", "./reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)

    course_dir = base_dir / args.course_code
    if not course_dir.exists():
        raise SystemExit(f"Course directory not found: {course_dir}")

    lecture_dir = course_dir / "lecture_notes"
    past_papers_dir = course_dir / "past_papers"
    assignment_dir = course_dir / "assignment" / "question"

    lecture_use_ocr = _env_flag("LECTURE_NOTES_USE_OCR", default=False)
    past_use_ocr = _env_flag("PAST_PAPERS_USE_OCR", default=False)
    assignment_use_ocr = _env_flag("ASSIGNMENT_USE_OCR", default=False)
    cheatsheet_use_ocr = _env_flag("CHEATSHEET_USE_OCR", default=False)

    print(f"[INFO] Processing course {args.course_code} in {course_dir}")
    print(f"[INFO] OCR settings - lecture_notes={lecture_use_ocr}, past_papers={past_use_ocr}, "
          f"assignment={assignment_use_ocr}, cheatsheet={cheatsheet_use_ocr}")

    cheatsheet_md = _load_cheatsheet(course_dir, use_ocr=cheatsheet_use_ocr)

    lecture_md_list = _gather_markdown_files(lecture_dir, use_ocr=lecture_use_ocr)
    past_md_list = _gather_markdown_files(past_papers_dir, use_ocr=past_use_ocr)
    assignment_md_list = _gather_markdown_files(assignment_dir, use_ocr=assignment_use_ocr)

    corpus = CourseCorpus(
        cheatsheet=cheatsheet_md,
        lecture_notes=lecture_md_list,
        past_papers=past_md_list,
        assignments=assignment_md_list,
    )

    report_markdown = check_coverage(corpus)

    output_path = reports_dir / f"{args.course_code}_coverage_report.md"
    output_path.write_text(report_markdown, encoding="utf-8")
    print(f"[INFO] Coverage report written to {output_path}")


if __name__ == "__main__":
    main()
