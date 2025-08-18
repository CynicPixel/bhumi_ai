"""
Agricultural Schemes Intelligence Agent - A2A Server Entry Point

This module provides the main entry point for running the Agricultural Schemes 
Intelligence Agent as an A2A-compatible server. It integrates the existing RAG
capabilities with the A2A protocol for seamless multi-agent orchestration.

Usage:
    python -m schemes_rag_agent
    
    Or directly:
    python schemes_rag_agent/__main__.py

Features:
- A2A protocol compliance for multi-agent integration
- Agricultural schemes RAG capabilities
- Conversation context preservation
- Streaming response support
- MongoDB conversation persistence
- Pinecone vector search integration
"""

import logging
import os
import sys
import signal
import asyncio
from typing import Optional

import click
import uvicorn
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore

from agent_card import create_agent_card, get_agent_description
from agent_executor import SchemesAgentExecutor
from config import Config
from custom_request_handler import CustomRequestHandler
from logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global server instance for graceful shutdown
server_instance: Optional[uvicorn.Server] = None


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"🛑 Received signal {sig}, initiating graceful shutdown...")
    if server_instance:
        server_instance.should_exit = True
    sys.exit(0)


class MissingConfigurationError(Exception):
    """Exception for missing required configuration."""
    pass


def validate_environment() -> None:
    """
    Validate that all required environment variables and configuration are present.
    
    Raises:
        MissingConfigurationError: If required configuration is missing
    """
    try:
        # Validate core configuration
        config = Config()
        config.validate()
        
        logger.info("✅ Environment validation passed")
        
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        raise MissingConfigurationError(f"Configuration validation failed: {e}")


def log_startup_info(host: str, port: int, agent_card) -> None:
    """
    Log comprehensive startup information for the schemes agent.
    
    Args:
        host: Server host address
        port: Server port number
        agent_card: A2A agent card instance
    """
    logger.info("🌾" + "="*70)
    logger.info("🌾 AGRICULTURAL SCHEMES INTELLIGENCE AGENT")
    logger.info("🌾" + "="*70)
    logger.info(f"🚀 Server starting on {host}:{port}")
    logger.info(f"🎯 Agent: {agent_card.name}")
    logger.info(f"📋 Version: {agent_card.version}")
    logger.info(f"🔗 URL: {agent_card.url}")
    logger.info("📖 API Endpoints:")
    logger.info(f"   • Agent Card: http://{host}:{port}/.well-known/agent.json")
    logger.info(f"   • A2A Protocol: http://{host}:{port}/a2a")
    logger.info(f"   • Health Check: http://{host}:{port}/health")
    logger.info("")
    
    logger.info("🎯 Agricultural Schemes Capabilities:")
    for skill in agent_card.skills:
        logger.info(f"   • {skill.name}")
        logger.info(f"     └─ {skill.description}")
        logger.info(f"     └─ Tags: {', '.join(skill.tags)}")
    
    logger.info("")
    logger.info("💡 Example Queries:")
    for skill in agent_card.skills:
        for example in skill.examples[:3]:  # Show first 3 examples
            logger.info(f"   • {example}")
    
    logger.info("")
    logger.info(get_agent_description())
    logger.info("🌾" + "="*70)


@click.command()
@click.option(
    '--host',
    default=lambda: os.getenv('SCHEMES_AGENT_HOST', 'localhost'),
    help='Host address to bind the server to'
)
@click.option(
    '--port', 
    default=lambda: int(os.getenv('SCHEMES_AGENT_PORT', 10004)),
    help='Port number to bind the server to'
)
@click.option(
    '--debug',
    is_flag=True,
    default=False,
    help='Enable debug mode with auto-reload'
)
@click.option(
    '--workers',
    default=1,
    help='Number of worker processes'
)
def main(host: str, port: int, debug: bool, workers: int) -> None:
    """
    Start the Agricultural Schemes Intelligence Agent A2A server.
    
    This command initializes and starts the A2A-compatible server that provides
    agricultural schemes intelligence using RAG capabilities. The server integrates
    with the multi-agent agricultural ecosystem via the A2A protocol.
    
    Args:
        host: Host address to bind the server to
        port: Port number to bind the server to  
        debug: Enable debug mode with auto-reload
        workers: Number of worker processes (ignored in debug mode)
    """
    global server_instance
    
    try:
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("🚀 Starting Agricultural Schemes Intelligence Agent...")
        
        # Validate environment and configuration
        validate_environment()
        
        # Create agent card for A2A protocol
        logger.info("📝 Creating agent card...")
        agent_card = create_agent_card(host, port)
        
        # Initialize A2A components
        logger.info("🔧 Initializing A2A components...")
        
        # Create task store for A2A task management
        task_store = InMemoryTaskStore()
        logger.info("✅ Task store initialized")
        
        # Create and initialize agent executor
        logger.info("🧠 Initializing schemes agent executor...")
        executor = SchemesAgentExecutor()
        logger.info("✅ Agent executor initialized")
        
        # Create custom request handler
        request_handler = CustomRequestHandler(
            agent_executor=executor,
            task_store=task_store,
        )
        logger.info("✅ Request handler initialized")
        
        # Create A2A Starlette application
        logger.info("🌐 Creating A2A server application...")
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )
        logger.info("✅ A2A server application created")
        
        # Log comprehensive startup information
        log_startup_info(host, port, agent_card)
        
        # Configure uvicorn server
        config = uvicorn.Config(
            app=server.build(),
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            workers=1 if debug else workers,  # Single worker in debug mode
            reload=debug,
        )
        
        # Create and store server instance
        server_instance = uvicorn.Server(config)
        
        # Start the server
        logger.info("🎯 Starting A2A server...")
        if debug:
            logger.info("🐛 Debug mode enabled - auto-reload active")
        
        # Run the server
        server_instance.run()
        
    except MissingConfigurationError as e:
        logger.error(f"❌ Configuration Error: {e}")
        logger.error("Please check your environment variables and configuration.")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Failed to start schemes agent server: {e}")
        logger.error("Check the logs above for more details.")
        sys.exit(1)
    
    finally:
        logger.info("🔌 Agricultural Schemes Intelligence Agent shutdown complete")


if __name__ == "__main__":
    main()
