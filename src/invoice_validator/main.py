import json
from pathlib import Path
import warnings
import gradio as gr
from datetime import datetime
import os
from invoice_validator.crew import InvoiceValidator
from invoice_validator.models.invoice_schema import ParsedInvoice
from invoice_validator.utils.logger import setup_logger
import traceback

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
logger = setup_logger()
crew = InvoiceValidator()

# Global variable to store logs
log_messages = []

def add_log(message):
    """Add message to log display"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_messages.append(f"[{timestamp}] {message}")
    return "\n".join(log_messages[-50:])  # Keep last 50 messages

def save_uploaded_file(file):
    """Save uploaded file and return path"""
    if file is None:
        return None
    
    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{os.path.basename(file.name)}"
    file_path = os.path.join("data/uploads/", filename)
    
    # Copy file
    import shutil
    shutil.copy(file.name, file_path)
    
    return file_path

def detect_file_type(file_path):
    """Detect file type from extension"""
    ext = os.path.splitext(file_path)[1].lower()
    type_map = {
        '.pdf': 'PDF',
        '.png': 'Image',
        '.jpg': 'Image',
        '.jpeg': 'Image',
        '.json': 'JSON',
        '.csv': 'CSV'
    }
    return type_map.get(ext, 'Unknown')

def process_invoice(file, progress=gr.Progress()):
    """Main validation function"""
    global log_messages
    log_messages = []
    
    try:
        # Validation checks
        if file is None:
            add_log("❌ ERROR: No file uploaded")
            return "Please upload an invoice file first.", "\n".join(log_messages), ""
        
        add_log("📁 File upload detected")
        
        # Save file
        file_path = save_uploaded_file(file)
        file_type = detect_file_type(file_path)
        
        add_log(f"📄 File saved: {os.path.basename(file_path)}")
        add_log(f"🔍 File type detected: {file_type}")
        
        # Check if file type is supported
        if file_type == 'Unknown':
            add_log("❌ ERROR: Unsupported file format")
            return "Unsupported file format. Please upload PDF, Image, JSON, or CSV.", "\n".join(log_messages), ""
    
        
        # progress(0.2, desc="Parsing document...")
        # add_log("📝 Document Parser Agent started")
        
        # progress(0.4, desc="Validating GST compliance...")
        # add_log("✅ GST Validator Agent started")
        
        # progress(0.6, desc="Validating TDS compliance...")
        # add_log("💰 TDS Validator Agent started")
        
        # progress(0.7, desc="Resolving ambiguities...")
        # add_log("🔍 Ambiguity Resolver Agent started")
        
        # progress(0.8, desc="Generating report...")
        # add_log("📊 Report Generator Agent started")
        
        # Run validation
        result = crew.validate_invoice(file_path, file_type, progress, add_log)
        
        progress(0.9, desc="Finalizing report...")
        add_log("✅ Validation completed successfully")
        
        # Save report
        report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = os.path.join("outputs/reports", report_filename)
        
        with open(report_path, 'w') as f:
            f.write(str(result))
        
        add_log(f"💾 Report saved: {report_filename}")
        progress(1.0, desc="Done!")

        report = format_report(result)
        
        return report, "\n".join(log_messages)
        
    except Exception as e:
        error_msg = f"❌ ERROR: {str(e)}\n\n{traceback.format_exc()}"
        add_log(error_msg)
        logger.error(error_msg)
        return f"Validation failed: {str(e)}", "\n".join(log_messages), ""

def format_report(result: dict) -> str:
    """Format the validation result into a readable report"""
    

    report = f"""
# 🧾 INVOICE VALIDATION REPORT

{result.get('raw', str(result))}

"""
    return report

def create_gradio_interface():
    """Create the Gradio UI"""
    
    with gr.Blocks() as app:
        
        gr.Markdown("""
        # 🧾 Invoice Validation System
        ### Upload your invoice PDF, images, JSON, CSV file to validate GST & TDS compliance automatically!
                    
        """)
        
        with gr.Row():
            # Left Column - Input
            with gr.Column(scale=1):
                gr.Markdown("### 📤 Upload Invoice")
                
                file_input = gr.File(
                    label="Upload Invoice (PDF / Image / JSON / CSV)",
                    file_types=[".pdf", ".png", ".jpg", ".jpeg", ".json", ".csv"],
                    type="filepath"
                )
                
                gr.Markdown("""
                **Supported Format:** PDF, Images (PNG/JPG/JPEG), JSON, CSV  
                **Example fields:** invoice_id, vendor name, buyer name, line_items->hsn_sac, GST details
                """)
                validate_btn = gr.Button(
                    "🔍 Validate Invoice",
                    variant="primary",
                    size="lg"
                )
                
                gr.Markdown("---")
                
                gr.Markdown("### 📜 Agent Activity Logs")
                
                log_output = gr.Textbox(
                    label="Real-time Progress & Errors",
                    lines=12,
                    interactive=False
                )
            
            # Right Column - Output
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Validation Report")
                
                report_output = gr.Textbox(
                    label="Compliance Analysis",
                    lines=25,
                    interactive=False,
                    max_lines=50
                )

                # Examples & Info
                
                with gr.Accordion("📖 What Gets Validated", open=False):
                    gr.Markdown("""
                    ### GST Compliance Checks:
                    - ✅ GSTIN format validation (15 characters, check digit)
                    - ✅ HSN/SAC code presence and format
                    - ✅ Tax rate validation (0%, 5%, 12%, 18%, 28%)
                    - ✅ CGST/SGST vs IGST logic (interstate/intrastate)
                    - ✅ Tax calculation accuracy
                    - ✅ Mandatory field presence
                    - ✅ Composition scheme violations
                    - ✅ Suspended GSTIN detection
                    
                    ### TDS Compliance Checks:
                    - ✅ TDS applicability (Section 194J for professional services)
                    - ✅ Correct TDS rate (10% for 194J)
                    - ✅ Threshold validation (₹30,000)
                    - ✅ PAN requirement check
                    
                    ### Edge Cases Handled:
                    - 🔍 Composition dealers charging GST (violation)
                    - 🔍 Wrong tax rates for product categories
                    - 🔍 Suspended/cancelled GSTIN usage
                    - 🔍 Missing mandatory fields
                    - 🔍 Incorrect interstate/intrastate tax application
                    """)
        
        # Event Handlers
        validate_btn.click(
            fn=process_invoice,
            inputs=[file_input],
            outputs=[report_output, log_output]
        )

    return app

def main():
    """Main entry point"""
    print("🚀 Starting Invoice Validator with CrewAI...")
    print("📁 Creating necessary directories...")
    
    # Create directories
    for dir_path in ["data/reports", "data/uploads"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Launch Gradio
    app = create_gradio_interface()
    app.launch(
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()
