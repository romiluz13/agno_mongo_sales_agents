"""
Test suite for Research Storage Module

Tests the research data processing and MongoDB storage functionality.
"""

import os
import sys
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.research_storage import (
    ResearchDataProcessor, 
    ResearchStorageManager, 
    ResearchRecord,
    create_research_processor,
    create_research_storage
)


class TestResearchDataProcessor:
    """Test cases for Research Data Processor"""
    
    def setup_method(self):
        """Setup test environment"""
        self.processor = ResearchDataProcessor()
        
        self.sample_raw_data = {
            "confidence_score": 0.85,
            "company_intelligence": {
                "recent_news": "Company raised $50M Series B funding led by Sequoia Capital",
                "growth_signals": ["Hiring 100+ engineers", "Expanding to Europe", "New product launch"],
                "challenges": ["Scaling sales team", "International compliance", "Competition"]
            },
            "decision_maker_insights": {
                "background": "Former Salesforce VP with 15 years experience in enterprise sales",
                "recent_activities": ["Speaking at SaaStr conference", "Posted about scaling challenges"]
            },
            "conversation_hooks": [
                "Congratulations on the Series B funding",
                "Saw your SaaStr talk about scaling sales teams",
                "Your European expansion timing is perfect"
            ],
            "timing_rationale": "Recent funding + new VP of Sales + scaling challenges = perfect timing",
            "sources": ["https://techcrunch.com/...", "https://linkedin.com/..."],
            "research_timestamp": "2024-01-15T10:30:00Z"
        }
        
        self.sample_lead_info = {
            "lead_name": "John Doe",
            "company": "Acme Corp",
            "title": "VP of Sales",
            "industry": "SaaS",
            "company_size": "500 employees"
        }

    def test_processor_initialization(self):
        """Test processor initializes correctly"""
        processor = ResearchDataProcessor()
        assert processor is not None
        assert processor.confidence_weights is not None
        assert len(processor.confidence_weights) == 6

    def test_process_research_data_success(self):
        """Test successful research data processing"""
        result = self.processor.process_research_data(self.sample_raw_data, self.sample_lead_info)
        
        assert isinstance(result, ResearchRecord)
        assert result.lead_name == "John Doe"
        assert result.company == "Acme Corp"
        assert result.status == "completed"
        assert result.confidence_score > 0.0
        assert len(result.conversation_hooks) == 3
        assert result.error_message is None

    def test_generate_research_id(self):
        """Test research ID generation"""
        research_id = self.processor._generate_research_id(self.sample_lead_info)
        
        assert "research_" in research_id
        assert "acme_corp" in research_id
        assert "john_doe" in research_id
        assert len(research_id) > 20

    def test_calculate_enhanced_confidence_score(self):
        """Test enhanced confidence score calculation"""
        # Test with complete data
        score = self.processor._calculate_enhanced_confidence_score(self.sample_raw_data)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high for complete data
        
        # Test with minimal data
        minimal_data = {
            "company_intelligence": {},
            "decision_maker_insights": {},
            "conversation_hooks": []
        }
        score = self.processor._calculate_enhanced_confidence_score(minimal_data)
        assert score == 0.0

    def test_process_company_intelligence(self):
        """Test company intelligence processing"""
        company_intel = self.sample_raw_data["company_intelligence"]
        processed = self.processor._process_company_intelligence(company_intel)
        
        assert isinstance(processed, dict)
        assert "recent_news" in processed
        assert "growth_signals" in processed
        assert "challenges" in processed
        assert isinstance(processed["growth_signals"], list)
        assert isinstance(processed["challenges"], list)
        assert len(processed["growth_signals"]) == 3

    def test_process_decision_maker_insights(self):
        """Test decision maker insights processing"""
        dm_insights = self.sample_raw_data["decision_maker_insights"]
        processed = self.processor._process_decision_maker_insights(dm_insights)
        
        assert isinstance(processed, dict)
        assert "background" in processed
        assert "recent_activities" in processed
        assert isinstance(processed["recent_activities"], list)
        assert len(processed["recent_activities"]) == 2

    def test_process_conversation_hooks(self):
        """Test conversation hooks processing"""
        hooks = self.sample_raw_data["conversation_hooks"]
        processed = self.processor._process_conversation_hooks(hooks)
        
        assert isinstance(processed, list)
        assert len(processed) == 3
        
        # Test with invalid input
        invalid_hooks = "not a list"
        processed = self.processor._process_conversation_hooks(invalid_hooks)
        assert processed == []

    def test_process_timing_rationale(self):
        """Test timing rationale processing"""
        rationale = self.sample_raw_data["timing_rationale"]
        processed = self.processor._process_timing_rationale(rationale)
        
        assert isinstance(processed, str)
        assert len(processed) > 10
        
        # Test with invalid input
        processed = self.processor._process_timing_rationale("")
        assert processed == "General outreach timing"

    def test_create_error_record(self):
        """Test error record creation"""
        error_msg = "Test error message"
        error_record = self.processor._create_error_record(self.sample_lead_info, error_msg)
        
        assert isinstance(error_record, ResearchRecord)
        assert error_record.status == "failed"
        assert error_record.error_message == error_msg
        assert error_record.confidence_score == 0.0
        assert error_record.lead_name == "John Doe"

    def test_create_research_processor_function(self):
        """Test convenience function for creating processor"""
        processor = create_research_processor()
        assert isinstance(processor, ResearchDataProcessor)


class TestResearchStorageManager:
    """Test cases for Research Storage Manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.connection_string = "mongodb://localhost:27017"
        self.database_name = "test_agno_sales_agent"
        
        self.sample_record = ResearchRecord(
            research_id="test_research_123",
            lead_name="John Doe",
            company="Acme Corp",
            title="VP of Sales",
            industry="SaaS",
            company_size="500 employees",
            confidence_score=0.85,
            company_intelligence={"recent_news": "Test news"},
            decision_maker_insights={"background": "Test background"},
            conversation_hooks=["Hook 1", "Hook 2"],
            timing_rationale="Test rationale",
            sources=["source1", "source2"],
            research_timestamp="2024-01-15T10:30:00Z",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status="completed"
        )

    def test_storage_manager_initialization(self):
        """Test storage manager initializes correctly"""
        manager = ResearchStorageManager(self.connection_string, self.database_name)
        
        assert manager.connection_string == self.connection_string
        assert manager.database_name == self.database_name
        assert manager.collection_name == "research_results"
        assert manager.agno_storage is not None

    @patch('agents.research_storage.MongoClient')
    def test_connect_success(self, mock_mongo_client):
        """Test successful MongoDB connection"""
        # Mock successful connection
        mock_client = Mock()
        mock_client.admin.command.return_value = True
        mock_database = Mock()
        mock_collection = Mock()

        # Properly mock the __getitem__ method for dictionary-like access
        def mock_getitem_client(key):
            return mock_database
        def mock_getitem_database(key):
            return mock_collection

        mock_client.__getitem__ = Mock(side_effect=mock_getitem_client)
        mock_database.__getitem__ = Mock(side_effect=mock_getitem_database)
        mock_mongo_client.return_value = mock_client

        manager = ResearchStorageManager(self.connection_string, self.database_name)
        result = manager.connect()

        assert result is True
        assert manager.client is not None
        assert manager.database is not None
        assert manager.collection is not None

    @patch('agents.research_storage.MongoClient')
    def test_connect_failure(self, mock_mongo_client):
        """Test MongoDB connection failure"""
        # Mock connection failure
        mock_mongo_client.side_effect = Exception("Connection failed")
        
        manager = ResearchStorageManager(self.connection_string, self.database_name)
        result = manager.connect()
        
        assert result is False

    def test_get_agno_storage(self):
        """Test getting Agno storage instance"""
        manager = ResearchStorageManager(self.connection_string, self.database_name)
        agno_storage = manager.get_agno_storage()
        
        assert agno_storage is not None
        assert agno_storage.collection_name == "research_agent_sessions"
        assert agno_storage.db_name == self.database_name

    @patch('agents.research_storage.MongoClient')
    def test_store_research_result_success(self, mock_mongo_client):
        """Test successful research result storage"""
        # Mock successful storage
        mock_client = Mock()
        mock_client.admin.command.return_value = True
        mock_database = Mock()
        mock_collection = Mock()
        mock_result = Mock()
        mock_result.upserted_id = "test_id"
        mock_result.modified_count = 0
        mock_collection.replace_one.return_value = mock_result

        # Properly mock the __getitem__ method for dictionary-like access
        def mock_getitem_client(key):
            return mock_database
        def mock_getitem_database(key):
            return mock_collection

        mock_client.__getitem__ = Mock(side_effect=mock_getitem_client)
        mock_database.__getitem__ = Mock(side_effect=mock_getitem_database)
        mock_mongo_client.return_value = mock_client

        manager = ResearchStorageManager(self.connection_string, self.database_name)
        manager.connect()
        result = manager.store_research_result(self.sample_record)

        assert result is True

    @patch('agents.research_storage.MongoClient')
    def test_get_research_result_success(self, mock_mongo_client):
        """Test successful research result retrieval"""
        # Mock successful retrieval
        mock_client = Mock()
        mock_client.admin.command.return_value = True
        mock_database = Mock()
        mock_collection = Mock()
        
        # Mock document data
        mock_doc = {
            "research_id": "test_research_123",
            "lead_name": "John Doe",
            "company": "Acme Corp",
            "title": "VP of Sales",
            "industry": "SaaS",
            "company_size": "500 employees",
            "confidence_score": 0.85,
            "company_intelligence": {"recent_news": "Test news"},
            "decision_maker_insights": {"background": "Test background"},
            "conversation_hooks": ["Hook 1", "Hook 2"],
            "timing_rationale": "Test rationale",
            "sources": ["source1", "source2"],
            "research_timestamp": "2024-01-15T10:30:00Z",
            "created_at": "2024-01-15T10:30:00+00:00",
            "updated_at": "2024-01-15T10:30:00+00:00",
            "status": "completed",
            "error_message": None
        }
        
        mock_collection.find_one.return_value = mock_doc

        # Properly mock the __getitem__ method for dictionary-like access
        def mock_getitem_client(key):
            return mock_database
        def mock_getitem_database(key):
            return mock_collection

        mock_client.__getitem__ = Mock(side_effect=mock_getitem_client)
        mock_database.__getitem__ = Mock(side_effect=mock_getitem_database)
        mock_mongo_client.return_value = mock_client
        
        manager = ResearchStorageManager(self.connection_string, self.database_name)
        manager.connect()
        result = manager.get_research_result("test_research_123")
        
        assert result is not None
        assert isinstance(result, ResearchRecord)
        assert result.research_id == "test_research_123"
        assert result.lead_name == "John Doe"

    def test_create_research_storage_function(self):
        """Test convenience function for creating storage manager"""
        manager = create_research_storage(self.connection_string, self.database_name)
        assert isinstance(manager, ResearchStorageManager)
        assert manager.connection_string == self.connection_string
        assert manager.database_name == self.database_name


class TestResearchRecord:
    """Test cases for ResearchRecord dataclass"""
    
    def test_research_record_creation(self):
        """Test ResearchRecord creation"""
        record = ResearchRecord(
            research_id="test_123",
            lead_name="John Doe",
            company="Acme Corp",
            title="VP of Sales",
            industry="SaaS",
            company_size="500 employees",
            confidence_score=0.85,
            company_intelligence={"test": "data"},
            decision_maker_insights={"test": "insights"},
            conversation_hooks=["hook1", "hook2"],
            timing_rationale="test rationale",
            sources=["source1"],
            research_timestamp="2024-01-15T10:30:00Z",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert record.research_id == "test_123"
        assert record.lead_name == "John Doe"
        assert record.confidence_score == 0.85
        assert record.status == "completed"  # default value
        assert record.error_message is None  # default value


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
