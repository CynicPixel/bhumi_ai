import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO, log_dir="logs"):
    """
    Setup logging configuration with file and console handlers.
    Logs are stored in files that reset on each server restart.
    
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
    
    # Log file paths
    main_log_file = log_path / f"bhumi_ai_{timestamp}.log"
    conversation_log_file = log_path / f"conversations_{timestamp}.log"
    error_log_file = log_path / f"errors_{timestamp}.log"
    
    # Clear any existing log files from previous sessions
    clear_old_logs(log_path)
    
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
    
    # Console handler (INFO level and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Main log file handler (DEBUG level and above)
    main_file_handler = RotatingFileHandler(
        main_log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    main_file_handler.setLevel(logging.DEBUG)
    main_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(main_file_handler)
    
    # Conversation-specific logger
    conversation_logger = logging.getLogger('conversations')
    conversation_logger.setLevel(logging.DEBUG)
    
    # Conversation file handler
    conv_file_handler = RotatingFileHandler(
        conversation_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    conv_file_handler.setLevel(logging.DEBUG)
    conv_file_handler.setFormatter(detailed_formatter)
    conversation_logger.addHandler(conv_file_handler)
    
    # Error log file handler (ERROR level and above)
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Log startup information
    startup_logger = logging.getLogger('startup')
    startup_logger.info(f"🚀 Bhumi AI Weather Agent starting up...")
    startup_logger.info(f"📁 Log directory: {log_path.absolute()}")
    startup_logger.info(f"📝 Main log file: {main_log_file}")
    startup_logger.info(f"💬 Conversation log file: {conversation_log_file}")
    startup_logger.info(f"❌ Error log file: {error_log_file}")
    startup_logger.info(f"🆔 Session ID: {session_id}")
    
    return {
        'main_log_file': main_log_file,
        'conversation_log_file': conversation_log_file,
        'error_log_file': error_log_file,
        'session_id': session_id,
        'log_path': log_path
    }

def clear_old_logs(log_path):
    """Clear old log files from previous sessions."""
    try:
        for log_file in log_path.glob("*.log"):
            if log_file.exists():
                log_file.unlink()
                print(f"🗑️  Cleared old log file: {log_file.name}")
    except Exception as e:
        print(f"⚠️  Warning: Could not clear old log files: {e}")

def get_logger(name):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_conversation(user_id, session_id, message_type, content, **kwargs):
    """
    Log conversation events to the conversation-specific log file.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        message_type: Type of message (user_input, ai_response, etc.)
        content: Message content
        **kwargs: Additional fields to log
    """
    logger = logging.getLogger('conversations')
    
    log_data = {
        'user_id': user_id,
        'session_id': session_id,
        'message_type': message_type,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        **kwargs
    }
    
    if message_type == 'user_input':
        logger.info(f"👤 USER [{user_id}:{session_id}] → {content[:100]}{'...' if len(content) > 100 else ''}")
    elif message_type == 'ai_response':
        logger.info(f"🤖 AI [{user_id}:{session_id}] → {content[:100]}{'...' if len(content) > 100 else ''}")
    elif message_type == 'conversation_retrieved':
        logger.info(f"📚 Retrieved {kwargs.get('count', 0)} conversations for [{user_id}:{session_id}]")
    else:
        logger.info(f"💬 {message_type.upper()} [{user_id}:{session_id}] → {content[:100]}{'...' if len(content) > 100 else ''}")
    
    # Also log detailed data at debug level
    logger.debug(f"Conversation event: {log_data}")

def log_error(error, context=None, **kwargs):
    """
    Log errors to the error log file.
    
    Args:
        error: Error message or exception
        context: Additional context information
        **kwargs: Additional fields to log
    """
    logger = logging.getLogger('errors')
    
    if isinstance(error, Exception):
        error_msg = f"{type(error).__name__}: {str(error)}"
        error_traceback = getattr(error, '__traceback__', None)
    else:
        error_msg = str(error)
        error_traceback = None
    
    log_data = {
        'error': error_msg,
        'context': context,
        'timestamp': datetime.now().isoformat(),
        **kwargs
    }
    
    logger.error(f"❌ ERROR: {error_msg}")
    if context:
        logger.error(f"   Context: {context}")
    
    # Log detailed data at debug level
    logger.debug(f"Error details: {log_data}")
    
    # If there's a traceback, log it
    if error_traceback:
        import traceback
        logger.debug(f"Traceback: {''.join(traceback.format_tb(error_traceback))}")

def log_server_event(event_type, details=None, **kwargs):
    """
    Log server events to the main log file.
    
    Args:
        event_type: Type of server event
        details: Additional details about the event
        **kwargs: Additional fields to log
    """
    logger = logging.getLogger('server')
    
    log_data = {
        'event_type': event_type,
        'details': details,
        'timestamp': datetime.now().isoformat(),
        **kwargs
    }
    
    if event_type == 'startup':
        logger.info(f"🚀 SERVER STARTUP: {details}")
    elif event_type == 'shutdown':
        logger.info(f"🛑 SERVER SHUTDOWN: {details}")
    elif event_type == 'request':
        logger.info(f"📥 REQUEST: {details}")
    elif event_type == 'response':
        logger.info(f"📤 RESPONSE: {details}")
    else:
        logger.info(f"📋 {event_type.upper()}: {details}")
    
    # Log detailed data at debug level
    logger.debug(f"Server event: {log_data}")

# Global logging configuration
_logging_config = None

def get_logging_config():
    """Get the current logging configuration."""
    return _logging_config

def initialize_logging(log_level=logging.INFO, log_dir="logs"):
    """Initialize logging and return configuration."""
    global _logging_config
    _logging_config = setup_logging(log_level, log_dir)
    return _logging_config
