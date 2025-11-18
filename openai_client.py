from __future__ import annotations

"""Lightweight wrapper around the OpenAI client.

This module centralises loading configuration from `.env` and exposes
small utilities that other modules (e.g. the agent or OCR helpers)
can use without duplicating setup code.
"""

import base64
import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def _build_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def llm_ocr(image_bytes: bytes) -> str:
    """Use an OpenAI model with vision capabilities to OCR an image.

    The model and params are read from TEXT_EXTRACTION_MODEL and
    TEXT_EXTRACTION_PARAMS in the environment. The prompt always uses
    Markdown so that downstream consumers can rely on Markdown text.
    """

    client = _build_client()

    model = os.getenv("TEXT_EXTRACTION_MODEL") or "gpt-4.1-mini"
    params_raw = os.getenv("TEXT_EXTRACTION_PARAMS") or "{}"

    try:
        extra_params: dict[str, Any] = json.loads(params_raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("TEXT_EXTRACTION_PARAMS must be valid JSON") from exc

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt_md = (
        "You are extracting text from a scanned lecture slide or exam page.\n\n"
        "Return the visible text as clean Markdown, preserving headings and "
        "bullet points where obvious. Do not add commentary beyond what is "
        "visible in the image."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_md},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}",
                        },
                    },
                ],
            }
        ],
        **extra_params,
    )

    # Extract first text segment from the response. Adjust this if the
    # SDK response structure changes.

    return response.choices[0].message.content


if __name__ == "__main__":  # Manual test helper
    import sys
    from pathlib import Path

    if len(sys.argv) != 2:
        print("Usage: python openai_client.py <path-to-image>")
        raise SystemExit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"File not found: {image_path}")
        raise SystemExit(1)

    image_bytes = image_path.read_bytes()
    try:
        text = llm_ocr(image_bytes)
    except Exception as exc:  # pragma: no cover - manual diagnostic helper
        print(f"Error calling LLM OCR: {exc}")
        raise SystemExit(1)

    print("--- OCR result (Markdown) ---")
    print(text)

