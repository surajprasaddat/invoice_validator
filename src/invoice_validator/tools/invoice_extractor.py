import json
import pandas as pd
import torch
import re
import io
from PIL import Image
from pdf2image import convert_from_path
from invoice_validator.utils.callbacks import add_log, progress
try:
    import pypdfium2 as pdfium
except Exception:
    pdfium = None
from transformers import DonutProcessor, VisionEncoderDecoderModel

# -------------------------------------------------
# Hugging Face Model (OCR-free Invoice Extraction)
# -------------------------------------------------
MODEL_NAME = "naver-clova-ix/donut-base-finetuned-cord-v2"

processor = DonutProcessor.from_pretrained(MODEL_NAME)
model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()


# -------------------------------------------------
# Unified Extraction Function
# -------------------------------------------------
def extract_invoice_data(file_path: str, file_type: str) -> dict:
    """
    Supported formats:
    - json  -> loads and returns JSON
    - csv   -> converts CSV rows to structured JSON
    - pdf   -> HuggingFace Donut model
    - png/jpg/jpeg -> HuggingFace Donut model
    """

    file_type = file_type.lower()

    # ----------------------
    # JSON
    # ----------------------
    if file_type == "json":
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ----------------------
    # CSV
    # ----------------------
    if file_type == "csv":
        df = pd.read_csv(file_path)
        return {
            "rows": df.to_dict(orient="records"),
            "columns": list(df.columns)
        }

    # ----------------------
    # PDF / IMAGE (Donut)
    # ----------------------
    # --- PDF / IMAGE (Hugging Face Donut) ---
    if file_type in ["pdf", "png", "jpg", "jpeg"]:
        # 1. Load Model and Processor
        # Using docvqa variant which is great for extracting specific fields
        model_name = "naver-clova-ix/donut-base-finetuned-docvqa"
        processor = DonutProcessor.from_pretrained(model_name)
        model = VisionEncoderDecoderModel.from_pretrained(model_name)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)

        # 2. Prepare Image
        if file_type == "pdf":
            # Convert first page of PDF to image
            try:
                progress(0.25, desc="Rendering PDF via Poppler...")
                images = convert_from_path(file_path)
                image = images[0].convert("RGB")
            except Exception as e:
                add_log("⚠️ Poppler not found; trying PDFium fallback")
                # Fallback to pypdfium2 if available
                if pdfium is not None:
                    try:
                        progress(0.27, desc="Rendering PDF via PDFium...")
                        pdf = pdfium.PdfDocument(file_path)
                        page = pdf[0]
                        bitmap = page.render(scale=2).to_pil()
                        image = bitmap.convert("RGB")
                    except Exception as ef:
                        raise RuntimeError(f"Failed PDF rendering with PDFium: {ef}")
                else:
                    raise RuntimeError(
                        "Unable to render PDF. Install Poppler or add pypdfium2."
                    )
        else:
            image = Image.open(file_path).convert("RGB")

        # 3. Prepare Task Prompt (Asking model to parse document)
        task_prompt = "<s_docvqa><s_question>Extract all information in JSON format</s_question>"
        decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids

        # 4. Generate Output
        pixel_values = processor(image, return_tensors="pt").pixel_values
        
        outputs = model.generate(
            pixel_values.to(device),
            decoder_input_ids=decoder_input_ids.to(device),
            max_length=model.config.decoder.max_position_embeddings,
            pad_token_id=processor.tokenizer.pad_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
            use_cache=True,
            return_dict_in_generate=True,
        )

        # 5. Decode and Post-process
        sequence = processor.batch_decode(outputs.sequences)[0]
        sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
        sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()
        
        # Convert to structured dictionary
        return processor.token2json(sequence)

    return {"error": "Unsupported file type"}
