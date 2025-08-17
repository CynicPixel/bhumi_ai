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
        
        if not self.mongo_url:
            logger.warning("MONGO_URL environment variable not set. MongoDB features will be disabled.")
        
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None
        
    def connect(self) -> None:
        """Establish connection to MongoDB with SSL fallback options."""
        if not self.mongo_url:
            logger.warning("No MONGO_URL configured. Skipping MongoDB connection.")
            return
            
        try:
            # First try with standard connection
            self.client = MongoClient(
                self.mongo_url,
                serverSelectionTimeoutMS=30000,
                socketTimeoutMS=20000,
                connectTimeoutMS=20000
            )
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Create indexes for better query performance
            self._create_indexes()
            
            logger.info(f"Successfully connected to MongoDB: {self.db_name}.{self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            logger.warning("Attempting connection with relaxed SSL settings...")
            
            try:
                # Try with relaxed SSL settings for Windows compatibility
                import ssl
                self.client = MongoClient(
                    self.mongo_url,
                    serverSelectionTimeoutMS=30000,
                    socketTimeoutMS=20000,
                    connectTimeoutMS=20000,
                    ssl=True,
                    ssl_cert_reqs=ssl.CERT_NONE,
                    ssl_ca_certs=None,
                    ssl_match_hostname=False
                )
                # Test the connection
                self.client.admin.command('ping')
                self.db = self.client[self.db_name]
                self.collection = self.db[self.collection_name]
                
                # Create indexes for better query performance
                self._create_indexes()
                
                logger.info(f"Successfully connected to MongoDB with relaxed SSL: {self.db_name}.{self.collection_name}")
                
            except Exception as ssl_error:
                logger.error(f"Failed to connect to MongoDB even with relaxed SSL: {ssl_error}")
                logger.warning("MongoDB connection failed. Application will continue without conversation storage.")
                self.client = None
                self.db = None
                self.collection = None
                # Don't raise the exception - let the app continue without MongoDB
    
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
    
    def get_collection(self) -> Optional[Collection]:
        """Get the MongoDB collection."""
        if self.collection is None:
            logger.warning("MongoDB not connected. Collection operations will be skipped.")
            return None
        return self.collection


# Global MongoDB instance
mongo_config = MongoDBConfig()


def get_mongo_collection() -> Optional[Collection]:
    """Get MongoDB collection instance."""
    return mongo_config.get_collection()


def ensure_mongo_connection() -> None:
    """Ensure MongoDB connection is established."""
    if not mongo_config.is_connected():
        mongo_config.connect()
