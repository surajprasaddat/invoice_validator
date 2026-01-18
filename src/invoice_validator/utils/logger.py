import logging
import sys
from datetime import datetime
import os

def setup_logger(name="InvoiceValidator", log_file=None, level=logging.INFO):
    """
    Set up a custom logger for the invoice validation system
    
    Args:
        name: Logger name
        log_file: Optional file path for logging
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    else:
        # Default log file
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(
            log_dir, 
            f"invoice_validator_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger


class CrewLogger:
    """Custom logger adapter for CrewAI agents"""
    
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.logger = setup_logger(f"Agent_{agent_name}")
    
    def log_start(self, task_description):
        """Log task start"""
        self.logger.info(f"🚀 {self.agent_name} started: {task_description}")
    
    def log_progress(self, message):
        """Log progress update"""
        self.logger.info(f"⚙️ {self.agent_name}: {message}")
    
    def log_completion(self, result_summary):
        """Log task completion"""
        self.logger.info(f"✅ {self.agent_name} completed: {result_summary}")
    
    def log_error(self, error_message):
        """Log error"""
        self.logger.error(f"❌ {self.agent_name} error: {error_message}")
    
    def log_warning(self, warning_message):
        """Log warning"""
        self.logger.warning(f"⚠️ {self.agent_name} warning: {warning_message}")