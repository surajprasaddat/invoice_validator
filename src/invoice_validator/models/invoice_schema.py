from pydantic import BaseModel, field_validator
from typing import List, Optional

class Vendor(BaseModel):
    name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None

class Buyer(BaseModel):
    name: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None

class LineItem(BaseModel):
    description: Optional[str] = None
    hsn_sac: Optional[str] = None
    quantity: Optional[float] = 0
    unit: Optional[str] = None
    rate: Optional[float] = 0
    amount: Optional[float] = 0

    @field_validator('quantity', 'rate', 'amount', mode='before')
    def _coerce_none_to_zero(cls, v):
        return 0 if v is None else v

class ParsedInvoice(BaseModel):
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    vendor: Vendor
    buyer: Buyer
    line_items: List[LineItem] = []
    subtotal: Optional[float] = 0
    cgst_rate: Optional[float] = 0
    cgst_amount: Optional[float] = 0
    sgst_rate: Optional[float] = 0
    sgst_amount: Optional[float] = 0
    igst_rate: Optional[float] = 0
    igst_amount: Optional[float] = 0
    total_tax: Optional[float] = 0
    total_amount: Optional[float] = 0

    @field_validator(
        'subtotal', 'cgst_rate', 'cgst_amount', 'sgst_rate', 'sgst_amount',
        'igst_rate', 'igst_amount', 'total_tax', 'total_amount', mode='before'
    )
    def _coerce_none_to_zero(cls, v):
        return 0 if v is None else v
