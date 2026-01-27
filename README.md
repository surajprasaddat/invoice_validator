
# Invoice Validator - Quick Start Guide

This project validates invoices using OCR and AI models. Follow these steps to set up and run the project on your machine.

## 1. Install Tesseract for OCR

Download and install Tesseract OCR from the official documentation:

[Tesseract Installation Guide](https://tesseract-ocr.github.io/tessdoc/Installation.html)

https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe

After installation, note the path to `tesseract.exe` (e.g., `C:\Users\<YourUsername>\AppData\Local\Programs\Tesseract-OCR\tesseract.exe`).

## 2. Create a `.env` File

In the project root directory, create a file named `.env` with the following content (replace `<YourUsername>` with your actual Windows username):

```
TESSERACT_PATH=C:\Users\<YourUsername>\AppData\Local\Programs\Tesseract-OCR\tesseract.exe
MODEL=openrouter/openai/gpt-4o-mini
OPENROUTER_API_KEY=sk-or-v1-56789
```

## 3. Install Python Dependencies

From the project root directory, run:

```
uv sync
```

This will download and install all required Python dependencies.

## 4. Run the Project

To start the invoice validator, run the following command from the project root (replace `<YourUsername>` with your actual username):

```
uv run C:\Users\<YourUsername>\Desktop\invoice_validator\src\invoice_validator\main.py
```

---

**Note:**
- Always use your actual Windows username in the paths above.
- Ensure Tesseract is installed and the path in `.env` is correct.

---

For further customization, configuration, or support, refer to the project documentation or contact the maintainer.
