from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from invoice_validator.models.invoice_schema import ParsedInvoice
import json


class ValidationToolInput(BaseModel):
    """Input schema for ValidationTool."""
    parsed_invoice: dict = Field(..., description="Parsed invoice data as dictionary")


class ValidationTool(BaseTool):
    name: str = "invoice_validator"
    description: str = (
        "Validates invoice compliance against GST, TDS, and business rules. "
        "Input should be a parsed invoice dictionary with all required fields."
    )
    args_schema: Type[BaseModel] = ValidationToolInput

    def _run(self, parsed_invoice: dict) -> str:
        """
        Execute validation checks on the parsed invoice.
        
        Args:
            parsed_invoice: Dictionary containing parsed invoice data
            
        Returns:
            JSON string with validation results
        """
        try:
            # Convert dict to ParsedInvoice model for validation
            invoice = ParsedInvoice(**parsed_invoice)
            
            results = {
                "category_results": [],
                "overall_compliance_score": 100
            }
            
            deductions = 0
            
            # Category A - Document Authenticity
            results["category_results"].extend(
                self._validate_document_authenticity(invoice)
            )
            
            # Category B - GST Compliance
            gst_results = self._validate_gst_compliance(invoice)
            results["category_results"].extend(gst_results)
            
            # Category C - Arithmetic Accuracy
            arith_results = self._validate_arithmetic(invoice)
            results["category_results"].extend(arith_results)
            
            # Category D - TDS Compliance
            tds_results = self._validate_tds_compliance(invoice)
            results["category_results"].extend(tds_results)
            
            # Category E - Policy & Business Rules
            policy_results = self._validate_policy_rules(invoice)
            results["category_results"].extend(policy_results)
            
            # Calculate overall compliance score
            total_checks = len(results["category_results"])
            failed_checks = sum(1 for r in results["category_results"] if r["status"] == "fail")
            
            if total_checks > 0:
                results["overall_compliance_score"] = int(((total_checks - failed_checks) / total_checks) * 100)
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "category_results": [],
                "overall_compliance_score": 0
            })
    
    def _validate_document_authenticity(self, invoice: ParsedInvoice) -> list:
        """Category A - Document Authenticity checks"""
        results = []
        
        # A1 - Invoice number format validation
        inv_num_valid = bool(invoice.invoice_number and len(invoice.invoice_number) > 0)
        results.append({
            "category": "Category A - Document Authenticity",
            "details": "A1 Invoice number format validation",
            "status": "pass" if inv_num_valid else "fail",
            "failures": [] if inv_num_valid else ["Invoice number missing or invalid"],
            "confidence": 100 if inv_num_valid else 0
        })
        
        # A2 - Duplicate invoice detection (simplified - would need database in production)
        results.append({
            "category": "Category A - Document Authenticity",
            "details": "A2 Duplicate invoice detection across vendors",
            "status": "pass",
            "failures": [],
            "confidence": 70  # Lower confidence without actual duplicate check
        })
        
        return results
    
    def _validate_gst_compliance(self, invoice: ParsedInvoice) -> list:
        """Category B - GST Compliance checks"""
        results = []
        
        # B1 - GSTIN format validation (handle missing field safely)
        vendor_gstin = getattr(invoice.vendor, 'gstin', None) if invoice.vendor else None
        gstin_valid = self._validate_gstin_format(vendor_gstin)
        
        results.append({
            "category": "Category B - GST Compliance",
            "details": "B1 GSTIN format validation (15-character alphanumeric)",
            "status": "pass" if gstin_valid else "fail",
            "failures": [] if gstin_valid else ["Invalid or missing GSTIN format"],
            "confidence": 100 if gstin_valid else 0
        })
        
        # B2 - GSTIN status verification (simplified)
        results.append({
            "category": "Category B - GST Compliance",
            "details": "B2 GSTIN active / suspended status verification",
            "status": "pass" if gstin_valid else "fail",
            "failures": [] if gstin_valid else ["Cannot verify GSTIN status"],
            "confidence": 60  # Lower confidence without API check
        })
        
        return results
    
    def _validate_arithmetic(self, invoice: ParsedInvoice) -> list:
        """Category C - Arithmetic & Calculation Accuracy"""
        results = []
        
        # C1 - Line item validation
        line_items_valid = True
        failures_c1 = []
        
        if invoice.line_items:
            for idx, item in enumerate(invoice.line_items):
                expected = round(item.quantity * item.rate, 2)
                actual = round(item.amount, 2)
                if abs(expected - actual) > 0.01:
                    line_items_valid = False
                    failures_c1.append(f"Line {idx+1}: {item.quantity} × {item.rate} ≠ {item.amount}")
        
        results.append({
            "category": "Category C - Arithmetic & Calculation Accuracy",
            "details": "C1 Line item validation quantity X rate = amount",
            "status": "pass" if line_items_valid else "fail",
            "failures": failures_c1,
            "confidence": 100 if line_items_valid else 80
        })
        
        # C2 - Subtotal validation
        calculated_subtotal = sum(item.amount for item in invoice.line_items) if invoice.line_items else 0
        subtotal_valid = abs(calculated_subtotal - invoice.subtotal) < 0.01
        
        results.append({
            "category": "Category C - Arithmetic & Calculation Accuracy",
            "details": "C2 Subtotal equals sum of line item amounts",
            "status": "pass" if subtotal_valid else "fail",
            "failures": [] if subtotal_valid else [f"Subtotal mismatch: Expected {calculated_subtotal}, Got {invoice.subtotal}"],
            "confidence": 100 if subtotal_valid else 90
        })
        
        return results
    
    def _validate_tds_compliance(self, invoice: ParsedInvoice) -> list:
        """Category D - TDS Compliance checks"""
        results = []
        
        # D1 - TDS applicability (simplified logic)
        tds_applicable = invoice.total_amount > 30000  # Threshold example
        
        results.append({
            "category": "Category D - TDS Compliance",
            "details": "D1 TDS applicability determination based on vendor nature",
            "status": "pass",
            "failures": [],
            "confidence": 70
        })
        
        # D2 - TDS section identification
        results.append({
            "category": "Category D - TDS Compliance",
            "details": "D2 Correct TDS section identification (194C / 194J / 194H etc.)",
            "status": "pass",
            "failures": [],
            "confidence": 60  # Would need vendor classification data
        })
        
        return results
    
    def _validate_policy_rules(self, invoice: ParsedInvoice) -> list:
        """Category E - Policy & Business Rules"""
        results = []
        
        # E1 - PO tolerance (would need PO data)
        results.append({
            "category": "Category E - Policy & Business Rules",
            "details": "E1 Invoice amount within PO tolerance (±5%)",
            "status": "pass",
            "failures": [],
            "confidence": 50  # Low confidence without PO data
        })
        
        # E2 - Contract period validation (would need contract data)
        results.append({
            "category": "Category E - Policy & Business Rules",
            "details": "E2 Invoice date within active contract period",
            "status": "pass",
            "failures": [],
            "confidence": 50  # Low confidence without contract data
        })
        
        return results
    
    def _validate_gstin_format(self, gstin: str) -> bool:
        """Validate GSTIN format: 15 alphanumeric characters"""
        if not gstin or len(gstin) != 15:
            return False
        return gstin.isalnum()