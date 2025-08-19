import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    """Setup comprehensive logging configuration with file rotation."""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter with colors
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler with rotation (10MB max, keep 5 backup files)
    log_file = logs_dir / "schemes_rag_agent.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # File formatter (more detailed)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Error file handler (only errors)
    error_log_file = logs_dir / "schemes_rag_agent_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Set specific logger levels and disable problematic uvicorn logging
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Disable uvicorn's default logging to prevent format conflicts
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.propagate = False
    
    return root_logger

def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logging.getLogger(name)

def log_conversation(user_id: str, session_id: str, message_type: str, content: str, **kwargs):
    """Log conversation events to a separate file."""
    conversation_logger = logging.getLogger("conversation")
    
    # Create conversation log file
    logs_dir = Path("logs")
    conversation_log_file = logs_dir / "conversations.log"
    
    # Add file handler if not already added
    if not conversation_logger.handlers:
        conversation_handler = logging.handlers.RotatingFileHandler(
            conversation_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        conversation_handler.setLevel(logging.INFO)
        
        conversation_formatter = logging.Formatter(
            '%(asctime)s - %(message_type)s - User: %(user_id)s - Session: %(session_id)s - %(content)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        conversation_handler.setFormatter(conversation_formatter)
        conversation_logger.addHandler(conversation_handler)
        conversation_logger.setLevel(logging.INFO)
    
    # Log the conversation event
    conversation_logger.info(
        f"Conversation Event",
        extra={
            "user_id": user_id,
            "session_id": session_id,
            "message_type": message_type,
            "content": content[:200] + "..." if len(content) > 200 else content,
            **kwargs
        }
    )
