import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from mongo_config import get_mongo_collection, ensure_mongo_connection
from logging_config import log_conversation

logger = logging.getLogger(__name__)


class ConversationHelper:
    """Helper class for managing conversations in MongoDB."""
    
    def __init__(self):
        self.collection = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure the helper is properly initialized with MongoDB connection."""
        if not self._initialized:
            try:
                ensure_mongo_connection()
                self.collection = get_mongo_collection()
                self._initialized = True
                logger.info("MongoDB connection established successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize MongoDB connection: {e}")
                # Don't raise, just log the warning and continue
                # This allows the system to work without MongoDB
                self.collection = None
                self._initialized = False
    
    def _is_mongo_available(self) -> bool:
        """Check if MongoDB is available and initialized."""
        # PyMongo collections don't support boolean evaluation, so we check explicitly
        return self._initialized and self.collection is not None
    
    def test_mongo_connection(self) -> bool:
        """Test if MongoDB connection is working by performing a simple operation."""
        try:
            if not self._is_mongo_available():
                return False
            
            # Try a simple operation to test the connection
            self.collection.find_one({}, limit=1)
            return True
        except Exception as e:
            logger.warning(f"MongoDB connection test failed: {e}")
            # Reset state on connection failure
            self._initialized = False
            self.collection = None
            return False
    
    def store_user_message(
        self, 
        user_id: str, 
        session_id: str, 
        message_id: str, 
        message_text: str,
        context_id: str = "",
        task_id: str = ""
    ) -> bool:
        """
        Store a user message in MongoDB.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the chat session
            message_id: Unique identifier for the message
            message_text: The text content of the message
            context_id: The context ID from the request (optional)
            task_id: The task ID from the request (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._ensure_initialized()
            
            # Check if MongoDB is available and test connection
            if not self._is_mongo_available() or not self.test_mongo_connection():
                logger.warning("MongoDB not available or connection failed, skipping message storage")
                return False
            
            message_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "message_id": message_id,
                "role": "user",
                "message_text": message_text,
                "context_id": context_id,
                "task_id": task_id,
                "timestamp": datetime.utcnow(),
                "message_type": "user_input"
            }
            
            result = self.collection.insert_one(message_doc)
            logger.info(f"Stored user message: {message_id} for user: {user_id}, session: {session_id}")
            
            # Log to conversation log file
            log_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type="user_input",
                content=message_text,
                message_id=message_id,
                context_id=context_id,
                task_id=task_id
            )
            
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Message {message_id} already exists, skipping duplicate")
            return True
        except Exception as e:
            logger.error(f"Failed to store user message: {e}")
            # Reset MongoDB state on error to prevent further issues
            self._initialized = False
            self.collection = None
            return False
    
    def store_ai_response(
        self, 
        user_id: str, 
        session_id: str, 
        message_id: str, 
        response_text: str,
        context_id: str = "",
        task_id: str = "",
        artifacts: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Store an AI response in MongoDB.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the chat session
            message_id: Unique identifier for the message
            response_text: The text content of the AI response
            context_id: The context ID from the request (optional)
            task_id: The task ID from the request (optional)
            artifacts: The artifacts from the AI response (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._ensure_initialized()
            
            # Check if MongoDB is available and test connection
            if not self._is_mongo_available() or not self.test_mongo_connection():
                logger.warning("MongoDB not available or connection failed, skipping AI response storage")
                return False
            
            response_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "message_id": message_id,
                "role": "ai",
                "response_text": response_text,
                "context_id": context_id,
                "task_id": task_id,
                "artifacts": artifacts or [],
                "timestamp": datetime.utcnow(),
                "message_type": "ai_response"
            }
            
            result = self.collection.insert_one(response_doc)
            logger.info(f"Stored AI response: {message_id} for user: {user_id}, session: {session_id}")
            
            # Log to conversation log file
            log_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type="ai_response",
                content=response_text,
                message_id=message_id,
                context_id=context_id,
                task_id=task_id
            )
            
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Response {message_id} already exists, skipping duplicate")
            return True
        except Exception as e:
            logger.error(f"Failed to store AI response: {e}")
            # Reset MongoDB state on error to prevent further issues
            self._initialized = False
            self.collection = None
            return False
    
    def get_conversation_history(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a specific user and session.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the chat session
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages ordered by timestamp
        """
        try:
            self._ensure_initialized()
            
            # Check if MongoDB is available
            if not self._is_mongo_available():
                logger.warning("MongoDB not available, returning empty conversation history")
                return []
            
            cursor = self.collection.find(
                {"user_id": user_id, "session_id": session_id}
            ).sort("timestamp", 1).limit(limit)
            
            conversations = list(cursor)
            logger.info(f"Retrieved {len(conversations)} messages for user: {user_id}, session: {session_id}")
            
            # Log to conversation log file
            log_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type="conversation_retrieved",
                content=f"Retrieved {len(conversations)} conversations",
                count=len(conversations),
                limit=limit
            )
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []
    
    def get_last_conversations(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get the last N conversations for a user and session.
        This is optimized for getting recent context.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the chat session
            limit: Maximum number of recent conversations to retrieve
            
        Returns:
            List of recent conversation messages ordered by timestamp (newest last)
        """
        try:
            self._ensure_initialized()
            
            # Check if MongoDB is available
            if not self._is_mongo_available():
                logger.warning("MongoDB not available, returning empty last conversations")
                return []
            
            cursor = self.collection.find(
                {"user_id": user_id, "session_id": session_id}
            ).sort("timestamp", -1).limit(limit)  # Sort by newest first
            
            conversations = list(cursor)
            # Reverse to get chronological logs (oldest to newest)
            conversations.reverse()
            
            logger.info(f"Retrieved last {len(conversations)} conversations for user: {user_id}, session: {session_id}")
            
            # Log to conversation log file
            log_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type="last_conversations_retrieved",
                content=f"Retrieved last {len(conversations)} conversations",
                count=len(conversations),
                limit=limit
            )
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to retrieve last conversations: {e}")
            return []
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """
        Get all session IDs for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List of session IDs
        """
        try:
            self._ensure_initialized()
            
            # Check if MongoDB is available
            if not self._is_mongo_available():
                logger.warning("MongoDB not available, returning empty sessions list")
                return []
            
            sessions = self.collection.distinct("session_id", {"user_id": user_id})
            logger.info(f"Retrieved {len(sessions)} sessions for user: {user_id}")
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to retrieve user sessions: {e}")
            return []
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """
        Delete all messages for a specific session.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the chat session
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._ensure_initialized()
            
            # Check if MongoDB is available
            if not self._is_mongo_available():
                logger.warning("MongoDB not available, cannot delete session")
                return False
            
            result = self.collection.delete_many({
                "user_id": user_id, 
                "session_id": session_id
            })
            
            logger.info(f"Deleted {result.deleted_count} messages for user: {user_id}, session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get conversation statistics for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dictionary containing conversation statistics
        """
        try:
            self._ensure_initialized()
            
            # Check if MongoDB is available
            if not self._is_mongo_available():
                logger.warning("MongoDB not available, returning empty stats")
                return {
                    "user_id": user_id,
                    "total_sessions": 0,
                    "total_messages": 0,
                    "sessions": []
                }
            
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$session_id",
                    "message_count": {"$sum": 1},
                    "last_message": {"$max": "$timestamp"},
                    "first_message": {"$min": "$timestamp"}
                }},
                {"$sort": {"last_message": -1}}
            ]
            
            stats = list(self.collection.aggregate(pipeline))
            
            total_sessions = len(stats)
            total_messages = sum(session["message_count"] for session in stats)
            
            return {
                "user_id": user_id,
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "sessions": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {
                "user_id": user_id,
                "total_sessions": 0,
                "total_messages": 0,
                "sessions": []
            }


# Global conversation helper instance (lazy initialization)
_conversation_helper = None


def get_conversation_helper() -> ConversationHelper:
    """Get the global conversation helper instance with lazy initialization."""
    global _conversation_helper
    if _conversation_helper is None:
        _conversation_helper = ConversationHelper()
    return _conversation_helper
