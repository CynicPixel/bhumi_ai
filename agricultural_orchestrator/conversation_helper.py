import logging
from typing import Dict, Any, List
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from mongo_config import get_mongo_collection, ensure_mongo_connection

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
                logger.info("🔍 Initializing MongoDB connection...")
                ensure_mongo_connection()
                self.collection = get_mongo_collection()
                if self.collection is not None:
                    self._initialized = True
                    logger.info("✅ MongoDB connection established successfully")
                else:
                    logger.warning("⚠️ MongoDB collection not available")
                    self._initialized = False
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize MongoDB connection: {e}")
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
        message_id: str, 
        message_text: str,
        context_id: str,
        task_id: str
    ) -> bool:
        """
        Store a user message in MongoDB.
        
        Args:
            user_id: Unique identifier for the user
            message_id: Unique identifier for the message
            message_text: The text content of the message
            context_id: The context ID from the request
            task_id: The task ID from the request
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"🔍 Attempting to store user message: user_id={user_id}, message_id={message_id}")
            self._ensure_initialized()
            
            # Check if MongoDB is available and test connection
            if not self._is_mongo_available() or not self.test_mongo_connection():
                logger.warning("MongoDB not available or connection failed, skipping message storage")
                return False
            
            message_doc = {
                "user_id": user_id,
                "message_id": message_id,
                "role": "user",
                "message_text": message_text,
                "context_id": context_id,
                "task_id": task_id,
                "timestamp": datetime.utcnow(),
                "message_type": "user_input"
            }
            
            result = self.collection.insert_one(message_doc)
            logger.info(f"Stored user message: {message_id} for user: {user_id}")
            
            # Log to conversation log file
            logger.info(f"Conversation logged: user={user_id}, message_id={message_id}")
            
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
        message_id: str, 
        response_text: str,
        context_id: str,
        task_id: str,
        artifacts: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Store an AI response in MongoDB.
        
        Args:
            user_id: Unique identifier for the user
            message_id: Unique identifier for the message
            response_text: The text content of the AI response
            context_id: The context ID from the request
            task_id: The task ID from the request
            artifacts: The artifacts from the AI response
            
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
            logger.info(f"Stored AI response: {message_id} for user: {user_id}")
            
            # Log to conversation log file
            logger.info(f"Conversation logged: user={user_id}, message_id={message_id}")
            
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
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a specific user.
        
        Args:
            user_id: Unique identifier for the user
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
                {"user_id": user_id}
            ).sort("timestamp", 1).limit(limit)
            
            conversations = list(cursor)
            logger.info(f"Retrieved {len(conversations)} messages for user: {user_id}")
            
            # Log to conversation log file
            logger.info(f"Conversation retrieved: user={user_id}, count={len(conversations)}")
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []
    
    def get_last_conversations(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the last N conversations for a user.
        This is optimized for getting recent context.
        
        Args:
            user_id: Unique identifier for the user
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
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit)  # Sort by newest first
            
            conversations = list(cursor)
            # Reverse to get chronological logs (oldest to newest)
            conversations.reverse()
            
            logger.info(f"Retrieved last {len(conversations)} conversations for user: {user_id}")
            
            # Log to conversation log file
            logger.info(f"Last conversations retrieved: user={user_id}, count={len(conversations)}")
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to retrieve last conversations: {e}")
            return []
    
    def get_user_conversation_count(self, user_id: str) -> int:
        """
        Get conversation count for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Number of conversations
        """
        try:
            self._ensure_initialized()
            
            # Check if MongoDB is available
            if not self._is_mongo_available():
                logger.warning("MongoDB not available, returning 0")
                return 0
            
            count = self.collection.count_documents({"user_id": user_id})
            logger.info(f"Retrieved conversation count for user: {user_id}: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to retrieve user conversation count: {e}")
            return 0
    
    def delete_user_conversations(self, user_id: str) -> bool:
        """
        Delete all messages for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._ensure_initialized()
            
            # Check if MongoDB is available
            if not self._is_mongo_available():
                logger.warning("MongoDB not available, cannot delete user conversations")
                return False
            
            result = self.collection.delete_many({
                "user_id": user_id
            })
            
            logger.info(f"Deleted {result.deleted_count} messages for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user conversations: {e}")
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
                    "total_messages": 0,
                    "last_message": None,
                    "first_message": None
                }
            
            # Get basic stats
            total_messages = self.collection.count_documents({"user_id": user_id})
            
            if total_messages > 0:
                # Get first and last message timestamps
                first_message = self.collection.find_one(
                    {"user_id": user_id}, 
                    sort=[("timestamp", 1)]
                )
                last_message = self.collection.find_one(
                    {"user_id": user_id}, 
                    sort=[("timestamp", -1)]
                )
                
                first_timestamp = first_message.get("timestamp") if first_message else None
                last_timestamp = last_message.get("timestamp") if last_message else None
            else:
                first_timestamp = None
                last_timestamp = None
            
            return {
                "user_id": user_id,
                "total_messages": total_messages,
                "first_message": first_timestamp,
                "last_message": last_timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {
                "user_id": user_id,
                "total_messages": 0,
                "first_message": None,
                "last_message": None
            }


# Global conversation helper instance (lazy initialization)
_conversation_helper = None


def get_conversation_helper() -> ConversationHelper:
    """Get the global conversation helper instance with lazy initialization."""
    global _conversation_helper
    if _conversation_helper is None:
        _conversation_helper = ConversationHelper()
    return _conversation_helper
