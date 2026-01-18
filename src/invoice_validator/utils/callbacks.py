"""
Enhanced callbacks module for real-time streaming updates.
Provides global callback functions that can be used by tools and agents.
"""

from datetime import datetime
from typing import Callable, Optional

# Global callback references
_progress_callback: Optional[Callable] = None
_add_log_callback: Optional[Callable] = None
_log_messages = []

def set_callbacks(progress_fn: Callable, add_log_fn: Callable):
    """
    Set the global callback functions for progress and logging.
    
    Args:
        progress_fn: Function to update progress (accepts progress value 0-1 and desc)
        add_log_fn: Function to add log messages (accepts message string)
    """
    global _progress_callback, _add_log_callback, _log_messages
    _progress_callback = progress_fn
    _add_log_callback = add_log_fn
    _log_messages = []

def progress(value: float, desc: str = ""):
    """
    Update progress indicator.
    
    Args:
        value: Progress value between 0 and 1
        desc: Description of current progress
    """
    if _progress_callback:
        _progress_callback(value, desc=desc)

def add_log(message: str) -> str:
    """
    Add a log message with timestamp.
    
    Args:
        message: Log message to add
        
    Returns:
        Formatted log output (all messages joined)
    """
    global _log_messages
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    _log_messages.append(formatted_msg)
    
    # Keep only last 100 messages
    if len(_log_messages) > 100:
        _log_messages = _log_messages[-100:]
    
    log_output = "\n".join(_log_messages)
    
    # Call the actual callback if set
    if _add_log_callback:
        return _add_log_callback(message)
    
    return log_output

def get_logs() -> str:
    """
    Get all current log messages.
    
    Returns:
        All log messages joined with newlines
    """
    return "\n".join(_log_messages)

def clear_logs():
    """Clear all log messages."""
    global _log_messages
    _log_messages = []

# Agent-specific logging helpers
def log_agent_start(agent_name: str):
    """Log when an agent starts."""
    add_log(f"🤖 {agent_name} started")

def log_agent_complete(agent_name: str):
    """Log when an agent completes."""
    add_log(f"✅ {agent_name} completed")

def log_agent_error(agent_name: str, error: str):
    """Log when an agent encounters an error."""
    add_log(f"❌ {agent_name} error: {error}")

def log_task_start(task_name: str):
    """Log when a task starts."""
    add_log(f"📋 Task started: {task_name}")

def log_task_complete(task_name: str):
    """Log when a task completes."""
    add_log(f"✅ Task completed: {task_name}")

def log_info(message: str):
    """Log informational message."""
    add_log(f"ℹ️ {message}")

def log_warning(message: str):
    """Log warning message."""
    add_log(f"⚠️ WARNING: {message}")

def log_error(message: str):
    """Log error message."""
    add_log(f"❌ ERROR: {message}")

def log_success(message: str):
    """Log success message."""
    add_log(f"✅ {message}")