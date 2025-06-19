"""
MongoDB Database Configuration and Connection Management
Following Agno cookbook patterns for MongoDB integration
"""

import os
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from agno.storage.mongodb import MongoDbStorage
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class MongoDBManager:
    """MongoDB connection and database management following Agno patterns"""
    
    def __init__(self):
        self.connection_string = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
        self.database_name = os.getenv("MONGODB_DATABASE", "agno_sales_agent")
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        
    def connect(self) -> bool:
        """Connect to MongoDB and return success status"""
        try:
            self.client = MongoClient(self.connection_string)
            # Test connection
            self.client.admin.command('ping')
            self.database = self.client[self.database_name]
            logger.info(f"✅ Connected to MongoDB: {self.database_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def get_collection(self, collection_name: str) -> Collection:
        """Get a MongoDB collection"""
        if self.database is None:
            raise Exception("Database not connected")
        return self.database[collection_name]
    
    def create_collections(self) -> bool:
        """Create required collections with indexes"""
        try:
            if self.database is None:
                raise Exception("Database not connected")
            
            # Create collections
            collections = [
                "contacts",
                "agent_sessions",
                "interaction_history",
                "message_previews",
                "message_queue",
                "research_results",
                "workflow_progress"
            ]
            
            for collection_name in collections:
                if collection_name not in self.database.list_collection_names():
                    self.database.create_collection(collection_name)
                    logger.info(f"Created collection: {collection_name}")
            
            # Create indexes for performance
            self._create_indexes()
            
            logger.info("✅ All collections created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collections: {e}")
            return False
    
    def _create_indexes(self):
        """Create indexes for better performance"""
        try:
            # Contacts collection indexes (NEW: For MongoDB single source of truth)
            contacts_collection = self.get_collection("contacts")
            contacts_collection.create_index("monday_item_id", unique=True)
            contacts_collection.create_index("board_id")
            contacts_collection.create_index("last_updated")
            contacts_collection.create_index("data_source")
            contacts_collection.create_index("comprehensive_data.company")
            contacts_collection.create_index("comprehensive_data.name")
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
    
    def get_agno_storage(self, collection_name: str = "agent_sessions") -> MongoDbStorage:
        """Get Agno MongoDbStorage instance following cookbook patterns"""
        return MongoDbStorage(
            collection_name=collection_name,
            db_url=self.connection_string,
            db_name=self.database_name
        )
    
    def test_connection(self) -> dict:
        """Test MongoDB connection and return status"""
        try:
            if self.client is None:
                self.connect()

            if self.database is None:
                raise Exception("Database connection failed")

            # Test basic operations
            test_collection = self.get_collection("connection_test")

            # Insert test document
            test_doc = {"test": "connection", "timestamp": "2024-01-01"}
            result = test_collection.insert_one(test_doc)

            # Read test document
            found_doc = test_collection.find_one({"_id": result.inserted_id})

            # Delete test document
            test_collection.delete_one({"_id": result.inserted_id})

            return {
                "success": True,
                "message": "MongoDB connection test successful",
                "database": self.database_name,
                "collections": list(self.database.list_collection_names())
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"MongoDB connection test failed: {e}",
                "database": None,
                "collections": []
            }

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()

def get_mongodb_manager() -> MongoDBManager:
    """Get the global MongoDB manager instance"""
    return mongodb_manager

def init_database() -> bool:
    """Initialize database connection and collections"""
    manager = get_mongodb_manager()
    if manager.connect():
        return manager.create_collections()
    return False

if __name__ == "__main__":
    # Test the database connection
    logging.basicConfig(level=logging.INFO)
    
    print("🔧 Testing MongoDB connection...")
    manager = MongoDBManager()
    
    # Test connection
    result = manager.test_connection()
    print(f"Connection test result: {result}")
    
    if result["success"]:
        print("✅ MongoDB setup successful!")
        print(f"Database: {result['database']}")
        print(f"Collections: {result['collections']}")
    else:
        print("❌ MongoDB setup failed!")
        print(f"Error: {result['message']}")
    
    manager.disconnect()
