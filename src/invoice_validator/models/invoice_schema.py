from pydantic import BaseModel, field_validator
from typing import List, Optional


class Vendor(BaseModel):
    name: Optional[str] = None
    gstin: Optional[str] = None

class Buyer(BaseModel):
    name: Optional[str] = None
    gstin: Optional[str] = None

class LineItem(BaseModel):
    description: Optional[str] = None
    hsn_sac: Optional[str] = None
    quantity: float = 0
    unit: Optional[str] = None
    rate: float = 0
    amount: float = 0

    @field_validator("quantity", "rate", "amount", mode="before")
    def coerce_none_to_zero(cls, v):
        return 0 if v is None else v


class ParsedInvoice(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    vendor: Vendor = Vendor()
    buyer: Buyer = Buyer()
    line_items: List[LineItem] = []

    subtotal: float = 0
    cgst_rate: float = 0
    cgst_amount: float = 0
    sgst_rate: float = 0
    sgst_amount: float = 0
    igst_rate: float = 0
    igst_amount: float = 0
    total_tax: float = 0
    total_amount: float = 0

    confidence: int = 0

    @field_validator(
        "subtotal",
        "cgst_rate",
        "cgst_amount",
        "sgst_rate",
        "sgst_amount",
        "igst_rate",
        "igst_amount",
        "total_tax",
        "total_amount",
        mode="before",
    )
    def coerce_none_to_zero(cls, v):
        return 0 if v is None else v
