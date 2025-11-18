from __future__ import annotations

"""Agent logic for checking cheatsheet coverage.

This module currently contains a minimal stub that wires together
converted Markdown contents. The detailed LLM prompts for extracting
topics and checking coverage can be filled in later.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class CourseCorpus:
    cheatsheet: str
    lecture_notes: list[str]
    past_papers: list[str]
    assignments: list[str]


def check_coverage(_corpus: CourseCorpus) -> str:
    """Return a placeholder Markdown report for coverage.

    This is a stub; real implementation should call the LLM defined
    in COVERAGE_MODEL/COVERAGE_PARAMS to extract topics and questions
    and compare them with the cheatsheet contents.
    """

    # For now, just echo basic structure.
    lines: list[str] = []
    lines.append("# Cheatsheet Coverage Report")
    lines.append("")
    lines.append("This is a stub report. Implement LLM-based coverage "
                 "analysis in `agent.check_coverage`.")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    lines.append(f"- Lecture notes files: {_safe_count(_corpus.lecture_notes)}")
    lines.append(f"- Past papers files: {_safe_count(_corpus.past_papers)}")
    lines.append(f"- Assignment question files: {_safe_count(_corpus.assignments)}")
    lines.append("")
    return "\n".join(lines)


def _safe_count(items: Iterable[str]) -> int:
    return sum(1 for _ in items)

