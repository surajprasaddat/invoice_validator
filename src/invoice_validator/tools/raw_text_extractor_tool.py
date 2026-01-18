from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from invoice_validator.tools.invoice_extractor import extract_invoice_data
from invoice_validator.utils.callbacks import add_log, progress
from invoice_validator.tools.document_loader import extract_raw_text

class RawTextExtractorInput(BaseModel):
    file_path: str = Field(..., description="Path to the invoice file")
    file_type: str = Field(..., description="File type: pdf, json, csv, png, jpg")


class RawTextExtractorTool(BaseTool):
    name: str = "Raw Invoice Text Extractor"
    description: str = (
        "Extracts raw readable text from invoice files such as PDF, image, JSON, or CSV."
    )
    
    args_schema: Type[BaseModel] = RawTextExtractorInput

    def _run(self, file_path: str, file_type: str) -> str:
        add_log("📝 Document Parser Agent started")
        progress(0.2, desc="Parsing document...")
        data = extract_raw_text(file_path, file_type)
        progress(0.3, desc="Document parsed")
        add_log("📄 Raw text (or structured) extracted")
        return data
