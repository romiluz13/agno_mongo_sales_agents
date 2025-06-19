"""
Research Data Processing & Storage Module

This module handles research result parsing, confidence scoring, and MongoDB storage
using cookbook/storage/mongodb_storage patterns for the Agno Sales Extension.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from agno.storage.mongodb import MongoDbStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ResearchRecord:
    """Research record for MongoDB storage"""
    research_id: str
    lead_name: str
    company: str
    title: str
    industry: str
    company_size: str
    confidence_score: float
    company_intelligence: Dict[str, Any]
    decision_maker_insights: Dict[str, Any]
    conversation_hooks: List[str]
    timing_rationale: str
    sources: List[str]
    research_timestamp: str
    created_at: datetime
    updated_at: datetime
    status: str = "completed"  # completed, failed, processing
    error_message: Optional[str] = None


class ResearchDataProcessor:
    """
    Processes and validates research data with confidence scoring
    following Agno framework patterns.
    """
    
    def __init__(self):
        """Initialize the research data processor"""
        self.confidence_weights = {
            'recent_news': 0.25,
            'growth_signals': 0.20,
            'challenges': 0.15,
            'decision_maker_background': 0.15,
            'recent_activities': 0.15,
            'conversation_hooks': 0.10
        }
    
    def process_research_data(self, raw_data: Dict[str, Any], lead_info: Dict[str, str]) -> ResearchRecord:
        """
        Process raw research data into a structured ResearchRecord
        
        Args:
            raw_data: Raw research data from the agent
            lead_info: Lead information (name, company, title, etc.)
            
        Returns:
            ResearchRecord: Processed and validated research record
        """
        try:
            # Generate unique research ID
            research_id = self._generate_research_id(lead_info)
            
            # Extract and validate data
            confidence_score = self._calculate_enhanced_confidence_score(raw_data)
            company_intelligence = self._process_company_intelligence(raw_data.get('company_intelligence', {}))
            decision_maker_insights = self._process_decision_maker_insights(raw_data.get('decision_maker_insights', {}))
            conversation_hooks = self._process_conversation_hooks(raw_data.get('conversation_hooks', []))
            timing_rationale = self._process_timing_rationale(raw_data.get('timing_rationale', ''))
            sources = raw_data.get('sources', [])
            
            # Create research record
            record = ResearchRecord(
                research_id=research_id,
                lead_name=lead_info.get('lead_name', ''),
                company=lead_info.get('company', ''),
                title=lead_info.get('title', ''),
                industry=lead_info.get('industry', ''),
                company_size=lead_info.get('company_size', ''),
                confidence_score=confidence_score,
                company_intelligence=company_intelligence,
                decision_maker_insights=decision_maker_insights,
                conversation_hooks=conversation_hooks,
                timing_rationale=timing_rationale,
                sources=sources,
                research_timestamp=raw_data.get('research_timestamp', datetime.now(timezone.utc).isoformat()),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                status="completed"
            )
            
            logger.info(f"Research data processed successfully for {lead_info.get('lead_name')} with confidence {confidence_score:.2f}")
            return record
            
        except Exception as e:
            logger.error(f"Failed to process research data: {e}")
            # Return error record
            return self._create_error_record(lead_info, str(e))
    
    def _generate_research_id(self, lead_info: Dict[str, str]) -> str:
        """Generate unique research ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        company_clean = lead_info.get('company', '').replace(' ', '_').lower()
        name_clean = lead_info.get('lead_name', '').replace(' ', '_').lower()
        return f"research_{company_clean}_{name_clean}_{timestamp}"
    
    def _calculate_enhanced_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate enhanced confidence score based on data quality"""
        score = 0.0
        
        # Company intelligence scoring
        company_intel = data.get('company_intelligence', {})
        if company_intel.get('recent_news') and len(company_intel['recent_news']) > 50:
            score += self.confidence_weights['recent_news']
        
        growth_signals = company_intel.get('growth_signals', [])
        if growth_signals and len(growth_signals) > 0:
            score += self.confidence_weights['growth_signals'] * min(len(growth_signals) / 3, 1.0)
        
        challenges = company_intel.get('challenges', [])
        if challenges and len(challenges) > 0:
            score += self.confidence_weights['challenges'] * min(len(challenges) / 3, 1.0)
        
        # Decision maker insights scoring
        dm_insights = data.get('decision_maker_insights', {})
        if dm_insights.get('background') and len(dm_insights['background']) > 30:
            score += self.confidence_weights['decision_maker_background']
        
        recent_activities = dm_insights.get('recent_activities', [])
        if recent_activities and len(recent_activities) > 0:
            score += self.confidence_weights['recent_activities'] * min(len(recent_activities) / 2, 1.0)
        
        # Conversation hooks scoring
        hooks = data.get('conversation_hooks', [])
        if hooks and len(hooks) >= 2:
            score += self.confidence_weights['conversation_hooks']
        
        return min(score, 1.0)
    
    def _process_company_intelligence(self, company_intel: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate company intelligence data"""
        processed = {
            'recent_news': company_intel.get('recent_news', ''),
            'growth_signals': company_intel.get('growth_signals', []),
            'challenges': company_intel.get('challenges', []),
            'market_position': company_intel.get('market_position', ''),
            'financial_status': company_intel.get('financial_status', ''),
            'competitive_landscape': company_intel.get('competitive_landscape', '')
        }
        
        # Ensure lists are actually lists
        if not isinstance(processed['growth_signals'], list):
            processed['growth_signals'] = [processed['growth_signals']] if processed['growth_signals'] else []
        
        if not isinstance(processed['challenges'], list):
            processed['challenges'] = [processed['challenges']] if processed['challenges'] else []
        
        return processed
    
    def _process_decision_maker_insights(self, dm_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate decision maker insights"""
        processed = {
            'background': dm_insights.get('background', ''),
            'recent_activities': dm_insights.get('recent_activities', []),
            'professional_interests': dm_insights.get('professional_interests', []),
            'pain_points': dm_insights.get('pain_points', []),
            'decision_making_style': dm_insights.get('decision_making_style', '')
        }
        
        # Ensure lists are actually lists
        for key in ['recent_activities', 'professional_interests', 'pain_points']:
            if not isinstance(processed[key], list):
                processed[key] = [processed[key]] if processed[key] else []
        
        return processed
    
    def _process_conversation_hooks(self, hooks: List[str]) -> List[str]:
        """Process and validate conversation hooks"""
        if not isinstance(hooks, list):
            return []
        
        # Filter out empty or very short hooks
        processed_hooks = [hook.strip() for hook in hooks if isinstance(hook, str) and len(hook.strip()) > 10]
        
        # Limit to top 5 hooks
        return processed_hooks[:5]
    
    def _process_timing_rationale(self, rationale: str) -> str:
        """Process and validate timing rationale"""
        if not isinstance(rationale, str):
            return "General outreach timing"
        
        return rationale.strip() if len(rationale.strip()) > 10 else "General outreach timing"
    
    def _create_error_record(self, lead_info: Dict[str, str], error_msg: str) -> ResearchRecord:
        """Create error record when processing fails"""
        return ResearchRecord(
            research_id=self._generate_research_id(lead_info),
            lead_name=lead_info.get('lead_name', ''),
            company=lead_info.get('company', ''),
            title=lead_info.get('title', ''),
            industry=lead_info.get('industry', ''),
            company_size=lead_info.get('company_size', ''),
            confidence_score=0.0,
            company_intelligence={},
            decision_maker_insights={},
            conversation_hooks=[],
            timing_rationale="",
            sources=[],
            research_timestamp=datetime.now(timezone.utc).isoformat(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status="failed",
            error_message=error_msg
        )


class ResearchStorageManager:
    """
    MongoDB storage manager for research data using Agno patterns
    """
    
    def __init__(self, connection_string: str, database_name: str = "agno_sales_agent"):
        """
        Initialize MongoDB storage manager
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.collection: Optional[Collection] = None
        self.collection_name = "research_results"
        
        # Initialize Agno storage for agent sessions
        self.agno_storage = MongoDbStorage(
            collection_name="research_agent_sessions",
            db_url=connection_string,
            db_name=database_name
        )
    
    def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            # Test connection
            self.client.admin.command('ping')
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            # Create indexes
            self._create_indexes()
            
            logger.info(f"✅ Connected to MongoDB for research storage: {self.database_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    def _create_indexes(self):
        """Create necessary indexes for efficient querying"""
        try:
            # Create indexes for common queries
            self.collection.create_index("research_id", unique=True)
            self.collection.create_index("company")
            self.collection.create_index("lead_name")
            self.collection.create_index("created_at")
            self.collection.create_index("confidence_score")
            self.collection.create_index("status")
            self.collection.create_index([("company", 1), ("lead_name", 1)])
            
            logger.info("✅ MongoDB indexes created successfully")
        except PyMongoError as e:
            logger.warning(f"⚠️ Could not create indexes: {e}")
    
    def store_research_result(self, research_record: ResearchRecord) -> bool:
        """
        Store research result in MongoDB
        
        Args:
            research_record: ResearchRecord to store
            
        Returns:
            bool: Success status
        """
        try:
            if self.collection is None:
                raise Exception("Database not connected")

            # Convert to dict for storage
            record_dict = asdict(research_record)
            
            # Handle datetime serialization
            record_dict['created_at'] = research_record.created_at.isoformat()
            record_dict['updated_at'] = research_record.updated_at.isoformat()
            
            # Upsert the record
            result = self.collection.replace_one(
                {"research_id": research_record.research_id},
                record_dict,
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Research result stored: {research_record.research_id}")
                return True
            else:
                logger.warning(f"⚠️ No changes made to research record: {research_record.research_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to store research result: {e}")
            return False
    
    def get_research_result(self, research_id: str) -> Optional[ResearchRecord]:
        """Get research result by ID"""
        try:
            if self.collection is None:
                raise Exception("Database not connected")

            doc = self.collection.find_one({"research_id": research_id})
            if doc:
                # Convert back to ResearchRecord
                doc.pop('_id', None)  # Remove MongoDB _id
                
                # Parse datetime fields
                doc['created_at'] = datetime.fromisoformat(doc['created_at'])
                doc['updated_at'] = datetime.fromisoformat(doc['updated_at'])
                
                return ResearchRecord(**doc)
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get research result: {e}")
            return None
    
    def get_research_by_company(self, company: str, limit: int = 10) -> List[ResearchRecord]:
        """Get research results by company"""
        try:
            if self.collection is None:
                raise Exception("Database not connected")

            cursor = self.collection.find(
                {"company": {"$regex": company, "$options": "i"}},
                limit=limit
            ).sort("created_at", -1)
            
            results = []
            for doc in cursor:
                doc.pop('_id', None)
                doc['created_at'] = datetime.fromisoformat(doc['created_at'])
                doc['updated_at'] = datetime.fromisoformat(doc['updated_at'])
                results.append(ResearchRecord(**doc))
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get research by company: {e}")
            return []
    
    def get_agno_storage(self) -> MongoDbStorage:
        """Get Agno storage instance for agent sessions"""
        return self.agno_storage
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Convenience functions
def create_research_processor() -> ResearchDataProcessor:
    """Create research data processor instance"""
    return ResearchDataProcessor()


def create_research_storage(connection_string: str, database_name: str = "agno_sales_agent") -> ResearchStorageManager:
    """Create research storage manager instance"""
    return ResearchStorageManager(connection_string, database_name)
