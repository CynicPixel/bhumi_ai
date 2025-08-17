import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

class SchemesMongoManager:
    """MongoDB manager for schemes RAG agent conversation storage."""
    
    def __init__(self, mongo_url: str, db_name: str, collection_name: str):
        """Initialize MongoDB manager."""
        self.mongo_url = mongo_url
        self.db_name = db_name
        self.collection_name = collection_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None
        
    def connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            logger.info("🔌 Establishing connection to MongoDB...")
            self.client = MongoClient(self.mongo_url)
            
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Create indexes for better query performance
            self._create_indexes()
            
            logger.info(f"✅ Successfully connected to MongoDB: {self.db_name}.{self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def _create_indexes(self) -> None:
        """Create database indexes for better performance."""
        try:
            # Index on user_id and session_id for fast conversation retrieval
            self.collection.create_index([("user_id", 1), ("session_id", 1)])
            # Index on timestamp for time-based queries
            self.collection.create_index([("timestamp", -1)])
            # Index on message_id for unique message identification
            self.collection.create_index([("message_id", 1)], unique=True)
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def store_conversation(
        self,
        user_id: str,
        session_id: str,
        message_id: str,
        role: str,
        content: str,
        context_id: str = None,
        task_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Store a conversation message in MongoDB.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the chat session
            message_id: Unique identifier for the message
            role: Role of the message sender ('user' or 'ai')
            content: The message content
            context_id: Optional context ID
            task_id: Optional task ID
            metadata: Optional additional metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.collection is None:
                logger.error("MongoDB not connected")
                return False
            
            message_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "message_id": message_id,
                "role": role,
                "timestamp": datetime.utcnow(),
                "context_id": context_id,
                "task_id": task_id,
                "metadata": metadata or {}
            }
            
            # Add role-specific fields
            if role == "user":
                message_doc["message_text"] = content
                message_doc["message_type"] = "user_input"
            elif role == "ai":
                message_doc["response_text"] = content
                message_doc["message_type"] = "ai_response"
            
            result = self.collection.insert_one(message_doc)
            logger.info(f"Stored {role} message: {message_id} for user: {user_id}, session: {session_id}")
            
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Message {message_id} already exists, skipping duplicate")
            return True
        except Exception as e:
            logger.error(f"Failed to store {role} message: {e}")
            return False
    
    def get_conversation_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 10
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
            if self.collection is None:
                logger.error("MongoDB not connected")
                return []
            
            cursor = self.collection.find(
                {"user_id": user_id, "session_id": session_id}
            ).sort("timestamp", 1).limit(limit)
            
            conversations = list(cursor)
            logger.info(f"Retrieved {len(conversations)} messages for user: {user_id}, session: {session_id}")
            
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
        
        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the chat session
            limit: Maximum number of recent conversations to retrieve
            
        Returns:
            List of recent conversation messages ordered by timestamp (newest last)
        """
        try:
            if self.collection is None:
                logger.error("MongoDB not connected")
                return []
            
            cursor = self.collection.find(
                {"user_id": user_id, "session_id": session_id}
            ).sort("timestamp", -1).limit(limit)
            
            conversations = list(cursor)
            # Reverse to get chronological order (oldest to newest)
            conversations.reverse()
            
            logger.info(f"Retrieved last {len(conversations)} conversations for user: {user_id}, session: {session_id}")
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to retrieve last conversations: {e}")
            return []
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        try:
            if self.client is not None:
                self.client.admin.command('ping')
                return True
        except:
            pass
        return False
    
    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB connection closed")
