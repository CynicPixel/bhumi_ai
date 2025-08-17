#!/usr/bin/env python3
"""
Startup script for the Schemes RAG Agent API server.
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from main import app
    import uvicorn
    from config import Config
    from logging_config import setup_logging, get_logger
    
    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)
    
    def main():
        """Main function to start the server."""
        try:
            logger.info("🚀 Starting Schemes RAG Agent API Server...")
            
            # Validate configuration
            Config.validate()
            logger.info("✅ Configuration validated successfully")
            
            # Start the server
            uvicorn.run(
                "main:app",
                host=Config.HOST,
                port=Config.PORT,
                reload=Config.DEBUG,
                log_level="info",
                access_log=True
            )
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            sys.exit(1)
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
