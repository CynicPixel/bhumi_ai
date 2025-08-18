"""
Conversation Helper for A2A Integration

This module provides conversation context management for A2A protocol integration,
ensuring seamless conversation tracking and context preservation across A2A sessions.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from config import Config
from mongo_manager import SchemesMongoManager

logger = logging.getLogger(__name__)


def get_conversation_helper() -> 'ConversationHelper':
    """
    Factory function to create and return a conversation helper instance.
    
    Returns:
        ConversationHelper: Initialized conversation helper instance
    """
    try:
        return ConversationHelper()
    except Exception as e:
        logger.error(f"Failed to create conversation helper: {e}")
        raise


class ConversationHelper:
    """
    Manages conversation context for A2A integration with the schemes RAG agent.
    
    This class provides methods to store and retrieve conversation messages,
    maintain session context, and integrate with the existing MongoDB conversation
    storage system while adding A2A-specific context tracking.
    """
    
    def __init__(self):
        """Initialize the conversation helper with MongoDB connection."""
        self.config = Config()
        self.mongo_manager = None
        self._initialized = False
        self._initialize_mongo()
        
    def _initialize_mongo(self) -> None:
        """Initialize MongoDB connection for conversation storage."""
        try:
            self.mongo_manager = SchemesMongoManager(
                mongo_url=self.config.MONGO_URL,
                db_name=self.config.DB_NAME,
                collection_name=self.config.COLLECTION_NAME
            )
            
            if self.mongo_manager.connect():
                self._initialized = True
                logger.info("✅ Conversation helper MongoDB connection established")
            else:
                logger.error("❌ Failed to connect to MongoDB for conversation helper")
                
        except Exception as e:
            logger.error(f"Error initializing MongoDB for conversation helper: {e}")
    
    def is_initialized(self) -> bool:
        """Check if the conversation helper is properly initialized."""
        return self._initialized and self.mongo_manager is not None
    
    def store_user_message(
        self,
        user_id: str,
        session_id: str,
        message_text: str,
        context_id: str,
        task_id: str,
        message_id: str = None,
        **kwargs
    ) -> bool:
        """
        Store a user message with A2A context information.
        
        Args:
            user_id: Unique identifier for the user
            session_id: A2A session identifier
            message_text: The user's message content
            context_id: A2A context identifier
            task_id: A2A task identifier
            message_id: Optional message identifier (will generate if not provided)
            **kwargs: Additional metadata to store
            
        Returns:
            bool: True if message was stored successfully, False otherwise
        """
        if not self.is_initialized():
            logger.warning("Conversation helper not initialized, cannot store user message")
            return False
            
        try:
            if not message_id:
                message_id = str(uuid.uuid4())
                
            # Store user message with A2A context
            return self.mongo_manager.store_conversation(
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                role="user",
                content=message_text,
                context_id=context_id,
                task_id=task_id,
                metadata={
                    "source": "a2a_protocol",
                    "timestamp": datetime.utcnow().isoformat(),
                    "additional_context": kwargs
                }
            )
            
        except Exception as e:
            logger.error(f"Error storing user message: {e}")
            return False
    
    def store_ai_response(
        self,
        user_id: str,
        session_id: str,
        response_text: str,
        context_id: str,
        task_id: str,
        message_id: str = None,
        metadata: Dict[str, Any] = None,
        **kwargs
    ) -> bool:
        """
        Store an AI response with A2A context and processing metadata.
        
        Args:
            user_id: Unique identifier for the user
            session_id: A2A session identifier  
            response_text: The AI's response content
            context_id: A2A context identifier
            task_id: A2A task identifier
            message_id: Optional message identifier (will generate if not provided)
            metadata: Processing metadata from RAG agent
            **kwargs: Additional metadata to store
            
        Returns:
            bool: True if response was stored successfully, False otherwise
        """
        if not self.is_initialized():
            logger.warning("Conversation helper not initialized, cannot store AI response")
            return False
            
        try:
            if not message_id:
                message_id = str(uuid.uuid4())
                
            # Combine RAG metadata with A2A context
            combined_metadata = {
                "source": "a2a_protocol",
                "timestamp": datetime.utcnow().isoformat(),
                "a2a_context": {
                    "context_id": context_id,
                    "task_id": task_id,
                    "session_id": session_id
                }
            }
            
            # Add RAG processing metadata if provided
            if metadata:
                combined_metadata.update({
                    "rag_processing": metadata,
                    "rag_context_used": metadata.get("rag_context_used", False),
                    "context_length": metadata.get("context_length", 0),
                    "search_strategy": metadata.get("search_strategy", "unknown")
                })
            
            # Add any additional metadata
            if kwargs:
                combined_metadata["additional_context"] = kwargs
                
            # Store AI response with comprehensive metadata
            return self.mongo_manager.store_conversation(
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                role="ai",
                content=response_text,
                context_id=context_id,
                task_id=task_id,
                metadata=combined_metadata
            )
            
        except Exception as e:
            logger.error(f"Error storing AI response: {e}")
            return False
    
    def get_conversation_context(
        self,
        user_id: str,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for RAG context enhancement.
        
        Args:
            user_id: Unique identifier for the user
            session_id: A2A session identifier
            limit: Maximum number of conversation messages to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of conversation messages with metadata
        """
        if not self.is_initialized():
            logger.warning("Conversation helper not initialized, returning empty context")
            return []
            
        try:
            # Get conversation history using existing mongo manager
            return self.mongo_manager.get_last_conversations(
                user_id=user_id,
                session_id=session_id,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error retrieving conversation context: {e}")
            return []
    
    def get_last_conversation(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the last conversation message for the user and session.
        
        Args:
            user_id: Unique identifier for the user
            session_id: A2A session identifier
            
        Returns:
            Optional[Dict[str, Any]]: Last conversation message or None
        """
        try:
            conversations = self.get_conversation_context(user_id, session_id, limit=1)
            return conversations[0] if conversations else None
            
        except Exception as e:
            logger.error(f"Error retrieving last conversation: {e}")
            return None
    
    def get_session_summary(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get a summary of the conversation session.
        
        Args:
            user_id: Unique identifier for the user
            session_id: A2A session identifier
            
        Returns:
            Dict[str, Any]: Session summary with statistics
        """
        try:
            conversations = self.get_conversation_context(user_id, session_id, limit=100)
            
            user_messages = [c for c in conversations if c.get('role') == 'user']
            ai_messages = [c for c in conversations if c.get('role') == 'ai']
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "total_messages": len(conversations),
                "user_messages": len(user_messages),
                "ai_messages": len(ai_messages),
                "last_activity": conversations[0].get('timestamp') if conversations else None,
                "has_a2a_context": any(
                    c.get('metadata', {}).get('source') == 'a2a_protocol' 
                    for c in conversations
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating session summary: {e}")
            return {
                "session_id": session_id,
                "user_id": user_id,
                "error": str(e)
            }
    
    def close(self) -> None:
        """Close the conversation helper and its connections."""
        try:
            if self.mongo_manager:
                self.mongo_manager.disconnect()
                logger.info("🔌 Conversation helper connections closed")
        except Exception as e:
            logger.error(f"Error closing conversation helper: {e}")
