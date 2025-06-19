import os
import logging
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv
import json
from bson import json_util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

class MongoDBInspector:
    """
    Connects to MongoDB and inspects its collections and schemas.
    """
    def __init__(self):
        self.connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        self.database_name = os.getenv("MONGODB_DATABASE", "agno_sales_agent")
        self.client: MongoClient | None = None
        self.database: Database | None = None

        if not self.connection_string:
            raise ValueError("MONGODB_CONNECTION_STRING environment variable not set.")

    def connect(self):
        """Establishes a connection to the MongoDB database."""
        try:
            self.client = MongoClient(self.connection_string)
            self.client.admin.command('ping')  # Verify connection
            self.database = self.client[self.database_name]
            logging.info(f"Successfully connected to database: '{self.database_name}'")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    def disconnect(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed.")

    def list_collections(self):
        """Lists all collections in the database."""
        if self.database is None:
            logging.error("Not connected to a database.")
            return []
        return self.database.list_collection_names()

    def get_sample_document(self, collection_name: str):
        """Fetches a single sample document from a specified collection."""
        if self.database is None:
            logging.error("Not connected to a database.")
            return None
        try:
            collection = self.database[collection_name]
            sample = collection.find_one()
            return sample
        except Exception as e:
            logging.error(f"Could not fetch sample from '{collection_name}': {e}")
            return None

def main():
    """
    Main function to run the MongoDB inspection.
    """
    inspector = MongoDBInspector()
    key_collections = [
        "agent_configurations",
        "contacts",
        "workflow_progress",
        "research_results",
        "interaction_history",
        "message_queue",
        "research_agent_sessions"
    ]

    try:
        inspector.connect()
        all_collections = inspector.list_collections()

        print("# MongoDB Schema Verification Report")
        print("\n---\n")
        print("## 1. All Collections in Database")
        print(f"\nFound {len(all_collections)} collections in the '{inspector.database_name}' database:\n")
        for name in sorted(all_collections):
            print(f"- `{name}`")

        print("\n---\n")
        print("## 2. Sample Document from Key Collections")
        print("\nFetching one sample document from each key collection to verify schema.\n")

        for collection_name in key_collections:
            print(f"### Collection: `{collection_name}`")
            if collection_name not in all_collections:
                print("\n*Collection not found in the database.*\n")
                continue
            
            sample_doc = inspector.get_sample_document(collection_name)
            
            if sample_doc:
                # Use json_util to handle MongoDB specific types like ObjectId
                print("\n```json")
                print(json.dumps(sample_doc, indent=2, default=json_util.default))
                print("```\n")
            else:
                print("\n*No documents found in this collection or could not fetch a sample.*\n")

    except Exception as e:
        logging.error(f"An error occurred during the inspection process: {e}")
    finally:
        inspector.disconnect()

if __name__ == "__main__":
    main()