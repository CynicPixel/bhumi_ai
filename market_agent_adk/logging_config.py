import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def setup_logging(log_level=logging.INFO, log_dir="logs"):
    """
    Setup logging configuration with file and console handlers.
    Logs are stored in files that persist across server restarts.
    
    Args:
        log_level: Logging level (default: INFO)
        log_dir: Directory to store log files (default: "logs")
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Generate unique log filename with timestamp for this server session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"session_{timestamp}"
    
    # Log file paths - using persistent naming for market agent
    main_log_file = log_path / "market_agent.log"
    conversation_log_file = log_path / "market_conversations.log"
    error_log_file = log_path / "market_errors.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s'
    )
    
    # Console handler (INFO level and above) with UTF-8 encoding for Windows
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Fix UTF-8 encoding for Windows console
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8')
        except:
            pass  # Fallback silently if reconfigure fails
    
    root_logger.addHandler(console_handler)
    
    # Main log file handler (DEBUG level and above) - APPEND mode for persistence
    main_file_handler = RotatingFileHandler(
        main_log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        mode='a'  # Append mode to preserve logs across restarts
    )
    main_file_handler.setLevel(logging.DEBUG)
    main_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(main_file_handler)
    
    # Conversation-specific logger
    conversation_logger = logging.getLogger('conversations')
    conversation_logger.setLevel(logging.DEBUG)
    
    # Conversation file handler - APPEND mode for persistence
    conv_file_handler = RotatingFileHandler(
        conversation_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        mode='a'  # Append mode to preserve logs across restarts
    )
    conv_file_handler.setLevel(logging.DEBUG)
    conv_file_handler.setFormatter(detailed_formatter)
    conversation_logger.addHandler(conv_file_handler)
    
    # Error log file handler (ERROR level and above) - APPEND mode for persistence
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5,
        mode='a'  # Append mode to preserve logs across restarts
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Log startup information
    startup_logger = logging.getLogger('startup')
    startup_logger.info(f"🚀 Bhumi AI Market Agent starting up...")
    startup_logger.info(f"📁 Log directory: {log_path.absolute()}")
    startup_logger.info(f"📝 Main log file: {main_log_file}")
    startup_logger.info(f"💬 Conversation log file: {conversation_log_file}")
    startup_logger.info(f"❌ Error log file: {error_log_file}")
    startup_logger.info(f"🆔 Session ID: {session_id}")
    startup_logger.info(f"💾 Log persistence: ENABLED (logs will persist across restarts)")
    
    return {
        'main_log_file': main_log_file,
        'conversation_log_file': conversation_log_file,
        'error_log_file': error_log_file,
        'session_id': session_id
    }


def log_conversation(user_id: str, session_id: str, message_type: str, content: str, 
                    message_id: str = None, context_id: str = None, task_id: str = None,
                    count: int = None, limit: int = None):
    """
    Log conversation events to the conversation log file.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        message_type: Type of conversation event
        content: Content or description of the event
        message_id: Optional message identifier
        context_id: Optional context identifier
        task_id: Optional task identifier
        count: Optional count for batch operations
        limit: Optional limit for batch operations
    """
    logger = logging.getLogger('conversations')
    
    # Create a structured log message
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'session_id': session_id,
        'message_type': message_type,
        'content': content[:200] + '...' if len(content) > 200 else content,  # Truncate long content
        'message_id': message_id,
        'context_id': context_id,
        'task_id': task_id
    }
    
    if count is not None:
        log_data['count'] = count
    if limit is not None:
        log_data['limit'] = limit
    
    # Format the log message
    log_message = f"💬 CONVERSATION | {log_data['timestamp']} | User: {user_id} | Session: {session_id} | Type: {message_type}"
    
    if message_id:
        log_message += f" | MessageID: {message_id}"
    if context_id:
        log_message += f" | Context: {context_id}"
    if task_id:
        log_message += f" | Task: {task_id}"
    if count is not None:
        log_message += f" | Count: {count}"
    if limit is not None:
        log_message += f" | Limit: {limit}"
    
    log_message += f" | Content: {log_data['content']}"
    
    logger.info(log_message)


def log_server_event(event_type: str, details: str = None, error: Exception = None):
    """
    Log server events to the main log file.
    
    Args:
        event_type: Type of server event
        details: Additional details about the event
        error: Optional error that occurred
    """
    logger = logging.getLogger('startup')
    
    if error:
        logger.error(f"🚨 SERVER EVENT | {event_type} | Error: {str(error)}")
        if details:
            logger.error(f"   Details: {details}")
    else:
        logger.info(f"📡 SERVER EVENT | {event_type}")
        if details:
            logger.info(f"   Details: {details}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def initialize_logging():
    """
    Initialize logging for the market agent.
    This function should be called early in the application startup.
    """
    # Setup logging with default configuration
    log_config = setup_logging()
    
    # Log the initialization
    logger = logging.getLogger('startup')
    logger.info("✅ Logging system initialized successfully")
    
    return log_config
