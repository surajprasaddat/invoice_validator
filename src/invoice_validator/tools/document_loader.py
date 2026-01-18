import json
import pandas as pd
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from pytesseract import TesseractNotFoundError
import io
import os

# Attempt to configure Tesseract on Windows or via environment variables.
def _configure_tesseract_path() -> None:
    """Configure pytesseract to find the Tesseract binary.

    Honors environment variables `TESSERACT_CMD` or `TESSERACT_PATH` if set.
    On Windows, also tries the common install location.
    """
    cmd = os.environ.get("TESSERACT_PATH")
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd

_configure_tesseract_path()

def extract_raw_text(file_path: str) -> str:
    """
    Extract text from PDF, Image, CSV, or JSON files.
    Automatically uses OCR for scanned PDFs or images.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")

    ext = os.path.splitext(file_path)[1].lower()

    # JSON
    if ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f), indent=2)

    # CSV
    elif ext == ".csv":
        df = pd.read_csv(file_path)
        return df.to_string(index=False)

    # PDF
    elif ext == ".pdf":
        return _extract_text_from_pdf(file_path)

    # Image
    elif ext in [".png", ".jpg", ".jpeg"]:
        return _extract_text_from_image(file_path)

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_text_from_pdf(file_path: str) -> str:
    text_output = ""
    pdf = fitz.open(file_path)

    for page_num, page in enumerate(pdf, start=1):
        # Try normal text extraction
        text = page.get_text()
        if text.strip():
            text_output += f"\n--- Page {page_num} ---\n{text}"
        else:
            # Use OCR for scanned pages
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            try:
                ocr_text = pytesseract.image_to_string(img)
            except TesseractNotFoundError:
                raise RuntimeError(
                    "Tesseract OCR not found. Install Tesseract and set TESSERACT_CMD/TESSERACT_PATH or add it to PATH."
                )
            text_output += f"\n--- Page {page_num} (OCR) ---\n{ocr_text}"

    return text_output


def _extract_text_from_image(file_path: str) -> str:
    img = Image.open(file_path)
    try:
        return pytesseract.image_to_string(img)
    except TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract OCR not found. Install Tesseract and set TESSERACT_CMD/TESSERACT_PATH or add it to PATH."
        )
