import json
import pandas as pd
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

def extract_raw_text(file_path: str, file_type: str) -> str:
    if file_type == "json":
        with open(file_path, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f), indent=2)

    if file_type == "csv":
        df = pd.read_csv(file_path)
        return df.to_string(index=False)

    if file_type == "pdf":
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if file_type in ["png", "jpg", "jpeg"]:
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)

    raise ValueError("Unsupported file type")
