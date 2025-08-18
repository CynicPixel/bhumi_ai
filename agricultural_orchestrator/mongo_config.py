import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MongoDBConfig:
    """MongoDB configuration and connection management."""
    
    def __init__(self):
        self.mongo_url = os.getenv('MONGO_URL')
        self.db_name = os.getenv('DB_NAME', 'Capone')
        self.collection_name = os.getenv('COLLECTION_NAME', 'Bhumi')
        
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None
        
    def connect(self) -> None:
        """Establish connection to MongoDB."""
        if not self.mongo_url:
            logger.warning("MONGO_URL environment variable not set, MongoDB connection skipped")
            return
            
        try:
            self.client = MongoClient(self.mongo_url)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Create indexes for better query performance
            self._create_indexes()
            
            logger.info(f"Successfully connected to MongoDB: {self.db_name}.{self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Don't raise, just log the error
    
    def _create_indexes(self) -> None:
        """Create database indexes for better performance."""
        try:
            # Index on user_id for fast conversation retrieval
            self.collection.create_index([("user_id", 1)])
            # Index on timestamp for time-based queries
            self.collection.create_index([("timestamp", -1)])
            # Index on message_id for unique message identification
            self.collection.create_index([("message_id", 1)], unique=True)
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
        except:
            pass
        return False
    
    def get_collection(self) -> Collection:
        """Get MongoDB collection instance."""
        if self.collection is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self.collection


# Global MongoDB instance
mongo_config = MongoDBConfig()


def get_mongo_collection() -> Collection:
    """Get MongoDB collection instance."""
    try:
        return mongo_config.get_collection()
    except RuntimeError:
        logger.warning("MongoDB not available, returning None")
        return None


def ensure_mongo_connection() -> None:
    """Ensure MongoDB connection is established."""
    if not mongo_config.is_connected():
        mongo_config.connect()
