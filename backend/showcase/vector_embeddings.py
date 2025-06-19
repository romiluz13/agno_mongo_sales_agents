#!/usr/bin/env python3
"""
Vector Embeddings Collection - MongoDB Showcase Enhancement

SAFETY: This is a NEW collection that doesn't modify existing code.
It safely stores vector embeddings using Voyage AI to showcase MongoDB's 
Vector Search capabilities for semantic similarity in research data.

Features:
- Voyage AI embeddings (voyage-3.5 model)
- MongoDB Vector Search for semantic similarity
- Research data semantic search
- Company intelligence vector matching
"""

import os
import sys
import logging
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import MongoDBManager

logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Document with vector embedding"""
    document_id: str
    content: str
    content_type: str  # "research_data", "company_intelligence", "conversation"
    source_id: str  # Original document ID (research_id, lead_id, etc.)
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime
    embedding_model: str = "voyage-3.5"
    embedding_dimensions: int = 1024

class VectorEmbeddingsManager:
    """
    SAFE MongoDB manager for vector embeddings
    Creates new collection without touching existing code
    """
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv("MONGODB_CONNECTION_STRING")
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY", "pa-i4ZSGUBbo9_umxRLgNz1RAFt_pf_PGvJyE-lAlNOiaK")
        self.db_manager = None
        self.collection = None
        self.voyage_client = None
        
    def connect(self) -> bool:
        """Connect to MongoDB and initialize Voyage AI"""
        try:
            # Connect to MongoDB
            self.db_manager = MongoDBManager()
            if not self.db_manager.connect():
                return False
                
            # NEW COLLECTION - completely safe
            self.collection = self.db_manager.get_collection("vector_embeddings")
            
            # Initialize Voyage AI client
            try:
                import voyageai
                self.voyage_client = voyageai.Client(api_key=self.voyage_api_key)
                logger.info("✅ Connected to vector_embeddings collection and Voyage AI")
                return True
            except ImportError:
                logger.error("❌ voyageai package not installed. Run: pip install voyageai")
                return False
            except Exception as e:
                logger.error(f"❌ Failed to initialize Voyage AI: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.db_manager:
            self.db_manager.disconnect()
    
    def create_embedding(self, text: str, input_type: str = "document") -> Optional[List[float]]:
        """Create vector embedding using Voyage AI"""
        try:
            if not self.voyage_client:
                logger.error("❌ Voyage AI client not initialized")
                return None
            
            # Create embedding using voyage-3.5 model
            result = self.voyage_client.embed(
                [text], 
                model="voyage-3.5", 
                input_type=input_type
            )
            
            if result.embeddings and len(result.embeddings) > 0:
                embedding = result.embeddings[0]
                logger.info(f"✅ Created embedding with {len(embedding)} dimensions")
                return embedding
            else:
                logger.error("❌ No embedding returned from Voyage AI")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating embedding: {e}")
            return None
    
    def store_research_embedding(self, research_id: str, research_data: Dict[str, Any]) -> bool:
        """Store research data with vector embedding"""
        try:
            # Extract text content for embedding
            content_parts = []
            
            # Company intelligence
            if "company_intelligence" in research_data:
                ci = research_data["company_intelligence"]
                if ci.get("recent_news"):
                    content_parts.append(f"Recent news: {ci['recent_news']}")
                if ci.get("growth_signals"):
                    content_parts.append(f"Growth signals: {', '.join(ci['growth_signals'])}")
                if ci.get("challenges"):
                    content_parts.append(f"Challenges: {', '.join(ci['challenges'])}")
            
            # Decision maker insights
            if "decision_maker_insights" in research_data:
                dmi = research_data["decision_maker_insights"]
                if dmi.get("background"):
                    content_parts.append(f"Background: {dmi['background']}")
                if dmi.get("recent_activities"):
                    content_parts.append(f"Activities: {', '.join(dmi['recent_activities'])}")
            
            # Conversation hooks
            if "conversation_hooks" in research_data:
                hooks = research_data["conversation_hooks"]
                content_parts.append(f"Conversation hooks: {', '.join(hooks)}")
            
            # Combine all content
            full_content = " | ".join(content_parts)
            
            if not full_content.strip():
                logger.warning(f"⚠️ No content to embed for research: {research_id}")
                return False
            
            # Create embedding
            embedding = self.create_embedding(full_content, "document")
            if not embedding:
                return False
            
            # Create vector document
            doc_id = f"research_{research_id}_{int(datetime.now().timestamp())}"
            vector_doc = VectorDocument(
                document_id=doc_id,
                content=full_content,
                content_type="research_data",
                source_id=research_id,
                embedding=embedding,
                metadata={
                    "lead_name": research_data.get("lead_name", "Unknown"),
                    "company": research_data.get("company", "Unknown"),
                    "confidence_score": research_data.get("confidence_score", 0.0),
                    "research_timestamp": research_data.get("research_timestamp"),
                    "content_length": len(full_content),
                    "embedding_source": "voyage-3.5"
                },
                created_at=datetime.now(timezone.utc)
            )
            
            # Convert to dict for MongoDB
            doc_dict = asdict(vector_doc)
            doc_dict['created_at'] = vector_doc.created_at.isoformat()
            
            # Store in MongoDB
            result = self.collection.insert_one(doc_dict)
            
            if result.inserted_id:
                logger.info(f"✅ Stored research embedding: {doc_id}")
                return True
            else:
                logger.error(f"❌ Failed to store embedding: {doc_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error storing research embedding: {e}")
            return False
    
    def semantic_search(self, query: str, content_type: str = None, 
                       limit: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity"""
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query, "query")
            if not query_embedding:
                return []
            
            # Build MongoDB aggregation pipeline for vector search
            pipeline = []

            # Define the $vectorSearch stage
            vector_search_stage = {
                "$vectorSearch": {
                    "index": "vector_index",  # As provided from your Atlas setup
                    "path": "embedding",      # Field containing the vector
                    "queryVector": query_embedding,
                    "numCandidates": limit * 15,  # Number of candidates to consider
                    "limit": limit                # Number of results to return
                }
            }

            # Add content_type filter if specified
            if content_type:
                vector_search_stage["$vectorSearch"]["filter"] = {
                    "content_type": content_type
                }
            
            pipeline.append(vector_search_stage)
            
            # Add a projection stage to include the search score and other fields
            pipeline.append(
                {
                    "$project": {
                        "_id": 0,  # Exclude the default _id
                        "document_id": 1,
                        "content": 1,
                        "content_type": 1,
                        "source_id": 1,
                        "metadata": 1,
                        "created_at": 1,
                        "similarity_score": {"$meta": "vectorSearchScore"}
                    }
                }
            )
            
            # Execute search
            logger.info(f"Executing $vectorSearch pipeline: {pipeline}")
            results = list(self.collection.aggregate(pipeline))
            
            logger.info(f"✅ Semantic search found {len(results)} results for: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in semantic search: {e}")
            # Fallback to simple text search
            return self._fallback_text_search(query, content_type, limit)
    
    def _fallback_text_search(self, query: str, content_type: str = None, 
                            limit: int = 5) -> List[Dict[str, Any]]:
        """Fallback text search if vector search fails"""
        try:
            match_filter = {"$text": {"$search": query}}
            if content_type:
                match_filter["content_type"] = content_type
            
            results = list(self.collection.find(
                match_filter,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit))
            
            logger.info(f"✅ Fallback search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Fallback search failed: {e}")
            return []
    
    def find_similar_companies(self, company_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Find companies with similar research profiles"""
        query = f"company similar to {company_name} growth challenges opportunities"
        return self.semantic_search(query, "research_data", limit)
    
    def find_relevant_insights(self, lead_context: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find relevant insights for lead personalization"""
        query = f"insights for {lead_context} personalization conversation hooks"
        return self.semantic_search(query, "research_data", limit)
    
    def get_embedding_analytics(self) -> Dict[str, Any]:
        """Get analytics about stored embeddings"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$content_type",
                        "count": {"$sum": 1},
                        "avg_content_length": {"$avg": "$metadata.content_length"}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_embeddings": {"$sum": "$count"},
                        "by_type": {
                            "$push": {
                                "content_type": "$_id",
                                "count": "$count",
                                "avg_content_length": {"$round": ["$avg_content_length", 0]}
                            }
                        }
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            analytics = result[0] if result else {
                "total_embeddings": 0,
                "by_type": []
            }
            
            logger.info("✅ Generated embedding analytics")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error generating analytics: {e}")
            return {}

# SAFE INTEGRATION HELPER - doesn't modify existing code
def safe_store_research_embedding(research_id: str, research_data: Dict[str, Any]) -> bool:
    """
    SAFE helper function to store research embeddings
    Can be called from existing research code without breaking anything
    """
    try:
        vector_manager = VectorEmbeddingsManager()
        if vector_manager.connect():
            success = vector_manager.store_research_embedding(research_id, research_data)
            vector_manager.disconnect()
            return success
        return False
        
    except Exception as e:
        logger.error(f"❌ Safe embedding storage failed: {e}")
        return False

def safe_semantic_search(query: str, content_type: str = "research_data", 
                        limit: int = 5) -> List[Dict[str, Any]]:
    """
    SAFE helper function for semantic search
    Can be called from anywhere without breaking existing code
    """
    try:
        vector_manager = VectorEmbeddingsManager()
        if vector_manager.connect():
            results = vector_manager.semantic_search(query, content_type, limit)
            vector_manager.disconnect()
            return results
        return []
        
    except Exception as e:
        logger.error(f"❌ Safe semantic search failed: {e}")
        return []
