import argparse
import json
import os
import sys
import time
from pathlib import Path

import fitz
from pptx import Presentation

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from features.pdf_to_pptx import (  # noqa: E402
    HAS_PDFTOPPT,
    convert_pdf_to_pptx,
    convert_with_pdftoppt,
)


def summarize_pdf(input_path):
    with fitz.open(input_path) as doc:
        pages = len(doc)
        pages_with_text = 0
        pages_with_images = 0

        for page in doc:
            text = page.get_text("text")
            if text and text.strip():
                pages_with_text += 1

            if page.get_images(full=True):
                pages_with_images += 1

    return {
        "pages": pages,
        "pages_with_text": pages_with_text,
        "pages_with_images": pages_with_images,
    }


def analyze_pptx(output_path):
    if not os.path.exists(output_path):
        return {
            "exists": False,
        }

    prs = Presentation(output_path)
    slide_count = len(prs.slides)

    total_shapes = 0
    picture_shapes = 0
    text_shapes_with_text = 0
    total_text_chars = 0
    slides_with_content = 0

    for slide in prs.slides:
        has_content = False

        for shape in slide.shapes:
            total_shapes += 1

            if hasattr(shape, "image"):
                picture_shapes += 1
                has_content = True

            if getattr(shape, "has_text_frame", False) and shape.text_frame:
                text = shape.text_frame.text or ""
                text = text.strip()
                if text:
                    text_shapes_with_text += 1
                    total_text_chars += len(text)
                    has_content = True

        if has_content:
            slides_with_content += 1

    return {
        "exists": True,
        "size_bytes": os.path.getsize(output_path),
        "slides": slide_count,
        "slides_with_content": slides_with_content,
        "total_shapes": total_shapes,
        "picture_shapes": picture_shapes,
        "text_shapes_with_text": text_shapes_with_text,
        "total_text_chars": total_text_chars,
        "avg_shapes_per_slide": (total_shapes / slide_count) if slide_count else 0,
        "avg_text_chars_per_slide": (total_text_chars / slide_count) if slide_count else 0,
    }


def run_current_pipeline(input_pdf, output_dir):
    output_path = os.path.join(output_dir, "current_pipeline.pptx")
    start = time.perf_counter()
    ok, msg = convert_pdf_to_pptx(
        input_pdf,
        output_path,
        enable_pdftoppt=False,
    )
    elapsed = round(time.perf_counter() - start, 3)

    return {
        "ok": ok,
        "msg": msg,
        "seconds": elapsed,
        "output": output_path,
        "analysis": analyze_pptx(output_path),
    }


def run_pdftoppt_engine(input_pdf, output_dir, warning_threshold):
    output_path = os.path.join(output_dir, "pdftoppt_engine.pptx")

    if not HAS_PDFTOPPT:
        return {
            "ok": False,
            "msg": "pdftoppt package is not installed",
            "seconds": 0,
            "output": output_path,
            "analysis": {"exists": False},
        }

    start = time.perf_counter()
    ok, msg = convert_with_pdftoppt(
        input_pdf,
        output_path,
        warning_threshold=warning_threshold,
    )
    elapsed = round(time.perf_counter() - start, 3)

    return {
        "ok": ok,
        "msg": msg,
        "seconds": elapsed,
        "output": output_path,
        "analysis": analyze_pptx(output_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark PDF-to-PPTX conversion engines on one PDF."
    )
    parser.add_argument("--input", required=True, help="Path to the input PDF.")
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", "pdf_tools_ab_compare"),
        help="Directory where benchmark outputs are written.",
    )
    parser.add_argument(
        "--pdftoppt-warning-threshold",
        type=int,
        default=None,
        help="Optional warning threshold for pdftoppt. If exceeded, run is marked failed.",
    )

    args = parser.parse_args()

    input_pdf = os.path.abspath(args.input)
    output_dir = os.path.abspath(args.output_dir)

    if not os.path.exists(input_pdf):
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    os.makedirs(output_dir, exist_ok=True)

    report = {
        "input_pdf": input_pdf,
        "pdf_summary": summarize_pdf(input_pdf),
        "current_pipeline": run_current_pipeline(input_pdf, output_dir),
        "pdftoppt_engine": run_pdftoppt_engine(
            input_pdf,
            output_dir,
            warning_threshold=args.pdftoppt_warning_threshold,
        ),
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
