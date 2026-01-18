from pathlib import Path
import warnings
import gradio as gr
from datetime import datetime
import os
import inspect
from invoice_validator.crew import InvoiceValidator
from invoice_validator.utils.logger import setup_logger
import traceback
from invoice_validator.tools.document_loader import extract_raw_text

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

_RAW_CACHE = {}

def process_invoice(file, progress=gr.Progress()):
    """Main validation function with REAL-TIME UPDATES"""
    global log_messages
    log_messages = []
    
    try:
        # Validation checks
        if file is None:
            log_output = add_log("❌ ERROR: No file uploaded")
            yield "Please upload an invoice file first.", log_output, {}
            return
        
        log_output = add_log("📁 File upload detected")
        yield "", log_output, {}
        
        # Save file
        file_path = save_uploaded_file(file)
        file_type = detect_file_type(file_path)
        
        log_output = add_log(f"📄 File saved: {os.path.basename(file_path)}")
        yield "", log_output, {}
        
        log_output = add_log(f"🔍 File type detected: {file_type}")
        yield "", log_output, {}
        
        # Check if file type is supported
        if file_type == 'Unknown':
            log_output = add_log("❌ ERROR: Unsupported file format")
            yield "Unsupported file format. Please upload PDF, Image, JSON, or CSV.", log_output, {}
            return

        # Extract raw text
        log_output = add_log("📝 Extracting text from document...")
        yield "", log_output, {}
        
        if file_path in _RAW_CACHE:
            data = _RAW_CACHE[file_path]
        else:
            data = extract_raw_text(file_path)
            _RAW_CACHE[file_path] = data
        
        log_output = add_log("✅ Text extraction completed")
        yield "", log_output, {}
        
        # Run validation with REAL-TIME STREAMING
        progress(0.2, desc="Starting validation pipeline...")
        log_output = add_log("🚀 Initializing CrewAI pipeline...")
        yield "", log_output, {}
        
        # Stream results from crew
        for update in crew.validate_invoice_streaming(data, progress, add_log):
            report = update.get('report', '')
            logs = update.get('logs', '')
            json_data = update.get('json_data', {})
            
            # Yield real-time updates
            yield report, logs, json_data
        
    except Exception as e:
        error_msg = f"❌ ERROR: {str(e)}\n\n{traceback.format_exc()}"
        log_output = add_log(error_msg)
        logger.error(error_msg)
        yield f"Validation failed: {str(e)}", log_output, {}

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
                """)
                validate_btn = gr.Button(
                    "🔍 Validate Invoice",
                    variant="primary",
                    size="lg"
                )
                
                gr.Markdown("---")
                
                gr.Markdown("### 📜 Agent Activity Logs")
                gr.Markdown("*Updates in real-time as agents work*")
                
                log_output = gr.Textbox(
                    label="Real-time Progress & Errors",
                    lines=12,
                    interactive=False
                )

                gr.Markdown("---")

                gr.Markdown("### 📦 Data Extraction (JSON)")
                gr.Markdown("*Updates after parsing completes*")
                json_display = gr.JSON(label="Parsed Invoice Data")
            
            # Right Column - Output
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Validation Report")
                gr.Markdown("*Updates after all validation completes*")
                
                report_output = gr.Markdown(
                    label="Compliance Analysis"
                )
        
        # Event Handlers - Use streaming for real-time updates
        validate_btn.click(
            fn=process_invoice,
            inputs=[file_input],
            outputs=[report_output, log_output, json_display]
        )

    return app

def main():
    """Main entry point"""
    print("🚀 Starting Invoice Validator with CrewAI...")
    print("📁 Creating necessary directories...")
    
    # Create directories
    for dir_path in ["data/reports", "data/uploads", "outputs/reports"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Launch Gradio
    app = create_gradio_interface()
    app.launch(
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()