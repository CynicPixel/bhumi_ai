import uvicorn
import psutil
import signal
import sys
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from config import Config
from rag_agent import SchemesRAGAgent
from logging_config import setup_logging, get_logger

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Schemes RAG Agent API",
    description="AI-powered agricultural schemes assistant with RAG capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG agent instance
rag_agent: Optional[SchemesRAGAgent] = None

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str = Field(..., description="User's query about agricultural schemes")
    user_id: str = Field(..., description="Unique identifier for the user")
    session_id: str = Field(..., description="Session identifier for the conversation")
    context_id: Optional[str] = Field(None, description="Optional context identifier")
    task_id: Optional[str] = Field(None, description="Optional task identifier")

class QueryResponse(BaseModel):
    success: bool = Field(..., description="Whether the query was processed successfully")
    response: str = Field(..., description="AI-generated response")
    message_id: str = Field(..., description="Unique identifier for the user message")
    ai_message_id: str = Field(..., description="Unique identifier for the AI response")
    rag_context_used: bool = Field(..., description="Whether RAG context was used")
    timestamp: str = Field(..., description="ISO timestamp of the response")
    error: Optional[str] = Field(None, description="Error message if any")

class ConversationHistoryRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    session_id: str = Field(..., description="Session identifier")
    limit: Optional[int] = Field(10, description="Maximum number of messages to retrieve")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Current timestamp")
    components: Dict[str, str] = Field(..., description="Status of individual components")

def kill_port(port: int):
    """Kill any process using the specified port."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections']:
                    if conn.laddr.port == port:
                        logger.info(f"Killing process {proc.info['pid']} using port {port}")
                        proc.terminate()
                        proc.wait(timeout=5)
                        logger.info(f"Successfully killed process on port {port}")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
    except Exception as e:
        logger.warning(f"Error killing port {port}: {e}")
    return False

def find_free_port(start_port: int = 8000, max_attempts: int = 100):
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Check if port is free
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                logger.info(f"Found free port: {port}")
                return port
        except OSError:
            continue
    
    # If no free port found, try to kill the default port
    logger.warning(f"No free port found, attempting to kill port {start_port}")
    if kill_port(start_port):
        return start_port
    
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG agent on startup."""
    global rag_agent
    try:
        logger.info("🚀 Starting Schemes RAG Agent...")
        
        # Validate configuration
        Config.validate()
        
        # Initialize RAG agent
        rag_agent = SchemesRAGAgent()
        if not rag_agent.initialize():
            logger.error("Failed to initialize RAG agent")
            raise RuntimeError("RAG agent initialization failed")
        
        logger.info("✅ Schemes RAG Agent started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start RAG agent: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global rag_agent
    if rag_agent:
        rag_agent.close()
        logger.info("RAG Agent connections closed")
    logger.info("Server shutdown complete")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_rag_agent() -> SchemesRAGAgent:
    """Dependency to get the RAG agent instance."""
    if not rag_agent:
        raise HTTPException(status_code=503, detail="RAG agent not available")
    return rag_agent

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Schemes RAG Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    global rag_agent
    
    components = {
        "api": "healthy",
        "rag_agent": "unhealthy" if not rag_agent else "healthy"
    }
    
    if rag_agent:
        # Check individual component health
        if rag_agent.pinecone_manager and rag_agent.pinecone_manager.index:
            components["pinecone"] = "healthy"
        else:
            components["pinecone"] = "unhealthy"
        
        if rag_agent.mongo_manager and rag_agent.mongo_manager.is_connected():
            components["mongodb"] = "healthy"
        else:
            components["mongodb"] = "unhealthy"
    
    overall_status = "healthy" if all(status == "healthy" for status in components.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        components=components
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    agent: SchemesRAGAgent = Depends(get_rag_agent)
):
    """
    Process a user query using RAG and return an AI-generated response.
    
    This endpoint:
    1. Stores the user query in MongoDB
    2. Retrieves relevant context from Pinecone using RAG
    3. Generates a response using Gemini AI
    4. Stores the AI response in MongoDB
    5. Returns the response with metadata
    """
    try:
        logger.info(f"Processing query for user: {request.user_id}, session: {request.session_id}")
        
        # Process the query
        result = agent.process_query(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            context_id=request.context_id,
            task_id=request.task_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        # Convert to response model
        response = QueryResponse(
            success=result["success"],
            response=result["response"],
            message_id=result["message_id"],
            ai_message_id=result["ai_message_id"],
            rag_context_used=result["rag_context_used"],
            timestamp=result["timestamp"]
        )
        
        logger.info(f"Successfully processed query for user: {request.user_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/conversation/history")
async def get_conversation_history(
    user_id: str,
    session_id: str,
    limit: int = 10,
    agent: SchemesRAGAgent = Depends(get_rag_agent)
):
    """
    Retrieve conversation history for a specific user and session.
    
    Args:
        user_id: Unique identifier for the user
        session_id: Session identifier
        limit: Maximum number of messages to retrieve (default: 10)
    """
    try:
        if limit > 100:
            limit = 100  # Cap the limit to prevent abuse
        
        conversations = agent.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
            "conversations": conversations,
            "count": len(conversations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}")

@app.post("/conversation/start")
async def start_conversation(
    user_id: str,
    session_id: Optional[str] = None
):
    """
    Start a new conversation session.
    
    Args:
        user_id: Unique identifier for the user
        session_id: Optional session identifier (will generate one if not provided)
    """
    try:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        return {
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
            "message": "Conversation session started",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@app.get("/config")
async def get_config():
    """Get current configuration (without sensitive information)."""
    return {
        "model": Config.GEMINI_MODEL,
        "max_tokens": Config.MAX_TOKENS,
        "temperature": Config.TEMPERATURE,
        "max_context_length": Config.MAX_CONTEXT_LENGTH,
        "similarity_threshold": Config.SIMILARITY_THRESHOLD,
        "max_retrieval_results": Config.MAX_RETRIEVAL_RESULTS,
        "pinecone_index": Config.PINECONE_INDEX,
        "mongo_database": Config.DB_NAME,
        "mongo_collection": Config.COLLECTION_NAME
    }

if __name__ == "__main__":
    # Find a free port
    try:
        port = find_free_port(Config.PORT)
        logger.info(f"Starting server on port {port}")
        
        # Run the server
        uvicorn.run(
            "main:app",
            host=Config.HOST,
            port=port,
            reload=Config.DEBUG,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
