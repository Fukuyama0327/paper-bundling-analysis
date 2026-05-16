#!/usr/bin/env python3
"""Extract page-level text from a PDF.

This small utility is for literature review notes. It writes a plain text file
with page markers so we can cite page-level evidence in drafting notes.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("output_txt", type=Path)
    args = parser.parse_args()

    reader = PdfReader(str(args.input_pdf))
    args.output_txt.parent.mkdir(parents=True, exist_ok=True)

    with args.output_txt.open("w", encoding="utf-8") as f:
        for page_index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            f.write(f"\n\n===== Page {page_index} =====\n")
            f.write(text)
            f.write("\n")


if __name__ == "__main__":
    main()
