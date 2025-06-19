"""
Test suite for Message Quality Optimizer

Tests the message quality testing, optimization, and approval workflow functionality.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.message_quality_optimizer import (
    MessageQualityOptimizer,
    QualityMetrics,
    MessageApproval,
    OptimizedMessage,
    MessageStatus,
    create_message_quality_optimizer
)
from agents.research_agent import LeadInput
from agents.message_agent import SenderInfo


class TestMessageQualityOptimizer:
    """Test cases for Message Quality Optimizer functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_keys = {
            'GEMINI_API_KEY': 'test_gemini_key',
            'TAVILY_API_KEY': 'test_tavily_key'
        }
        
        self.mongodb_connection = "mongodb://localhost:27017"
        
        self.sample_lead_input = LeadInput(
            lead_name="Jensen Huang",
            company="NVIDIA",
            title="CEO",
            industry="Technology",
            company_size="50,000+ employees"
        )
        
        self.sample_sender_info = SenderInfo(
            name="Sarah Chen",
            company="CloudScale Solutions",
            value_prop="AI infrastructure optimization"
        )

    def test_quality_optimizer_initialization(self):
        """Test that Message Quality Optimizer initializes correctly"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            assert optimizer is not None
            assert optimizer.target_response_rate == 0.40
            assert optimizer.quality_threshold == 0.75
            assert optimizer.research_agent is not None
            assert optimizer.message_agent is not None
            assert optimizer.multimodal_agent is not None

    def test_create_quality_optimizer_function(self):
        """Test the convenience function for creating quality optimizer"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = create_message_quality_optimizer(self.api_keys, self.mongodb_connection)
            
            assert isinstance(optimizer, MessageQualityOptimizer)

    def test_calculate_readability_score(self):
        """Test readability score calculation"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Test optimal readability (10-20 words per sentence)
            optimal_message = "This is a well-structured message with optimal word count per sentence. It should score highly on readability."
            score = optimizer._calculate_readability_score(optimal_message)
            assert score >= 0.95  # Allow for floating point precision
            
            # Test short sentences
            short_message = "Short. Very short. Too short."
            score = optimizer._calculate_readability_score(short_message)
            assert 0.8 <= score < 1.0
            
            # Test long sentences
            long_message = "This is an extremely long sentence that contains way too many words and should result in a lower readability score because it's difficult to read and understand."
            score = optimizer._calculate_readability_score(long_message)
            assert score < 0.8

    def test_calculate_sentiment_score(self):
        """Test sentiment score calculation"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Test positive message
            positive_message = "Congrats on your excellent growth! This is an amazing opportunity for collaboration."
            score = optimizer._calculate_sentiment_score(positive_message)
            assert score > 0.7
            
            # Test neutral message
            neutral_message = "I would like to discuss business opportunities with your company."
            score = optimizer._calculate_sentiment_score(neutral_message)
            assert 0.5 <= score <= 0.8
            
            # Test message with professional words
            professional_message = "Let's explore partnership opportunities to drive growth and discuss collaboration."
            score = optimizer._calculate_sentiment_score(professional_message)
            assert score > 0.6

    def test_calculate_urgency_score(self):
        """Test urgency score calculation"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Test high urgency message
            urgent_message = "Perfect timing! This exclusive opportunity is available now for a quick discussion."
            score = optimizer._calculate_urgency_score(urgent_message)
            assert score > 0.7
            
            # Test low urgency message
            low_urgency_message = "I would like to connect with you about our services."
            score = optimizer._calculate_urgency_score(low_urgency_message)
            assert score < 0.5

    def test_calculate_value_proposition_score(self):
        """Test value proposition score calculation"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Test strong value proposition
            strong_value_message = "We help optimize performance and increase revenue while reducing costs for better results."
            score = optimizer._calculate_value_proposition_score(strong_value_message)
            assert score > 0.8
            
            # Test weak value proposition
            weak_value_message = "We provide services to companies in your industry."
            score = optimizer._calculate_value_proposition_score(weak_value_message)
            assert score < 0.5

    def test_calculate_cta_score(self):
        """Test call-to-action score calculation"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Test strong CTA
            strong_cta_message = "Would you be interested in a quick chat to discuss this opportunity?"
            score = optimizer._calculate_cta_score(strong_cta_message)
            assert score > 0.7
            
            # Test weak CTA
            weak_cta_message = "Let me know if you want to learn more."
            score = optimizer._calculate_cta_score(weak_cta_message)
            assert score < 0.5

    def test_assess_message_quality(self):
        """Test comprehensive message quality assessment"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Mock message output
            mock_message = Mock()
            mock_message.message_text = "Hi Jensen! Congrats on NVIDIA's record revenue growth! Would you be interested in discussing AI infrastructure optimization?"
            mock_message.personalization_score = 0.9
            mock_message.predicted_response_rate = 0.45
            
            mock_research = Mock()
            
            quality_metrics = optimizer._assess_message_quality(mock_message, mock_research)
            
            assert isinstance(quality_metrics, QualityMetrics)
            assert quality_metrics.personalization_score == 0.9
            assert quality_metrics.predicted_response_rate == 0.45
            assert 0.0 <= quality_metrics.overall_quality_score <= 1.0

    def test_generate_optimization_notes(self):
        """Test optimization notes generation"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Test low quality metrics
            low_quality = QualityMetrics(
                personalization_score=0.5,
                predicted_response_rate=0.2,
                readability_score=0.6,
                sentiment_score=0.7,
                urgency_score=0.4,
                value_proposition_score=0.5,
                call_to_action_score=0.6,
                overall_quality_score=0.5
            )
            
            notes = optimizer._generate_optimization_notes(low_quality)
            
            assert len(notes) > 0
            assert any("response rate" in note.lower() for note in notes)
            assert any("personalization" in note.lower() for note in notes)

    def test_implement_approval_workflow_approved(self):
        """Test approval workflow for high-quality message"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # High quality message
            high_quality = QualityMetrics(
                personalization_score=0.9,
                predicted_response_rate=0.5,
                readability_score=0.8,
                sentiment_score=0.8,
                urgency_score=0.7,
                value_proposition_score=0.8,
                call_to_action_score=0.9,
                overall_quality_score=0.85
            )
            
            optimized_message = OptimizedMessage(
                original_message="Original message",
                optimized_message="Optimized message",
                quality_metrics=high_quality,
                optimization_notes=[]
            )
            
            approval = optimizer.implement_approval_workflow(optimized_message)
            
            assert isinstance(approval, MessageApproval)
            assert approval.status == MessageStatus.APPROVED
            assert len(approval.suggested_improvements) == 0

    def test_implement_approval_workflow_needs_revision(self):
        """Test approval workflow for medium-quality message"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Medium quality message
            medium_quality = QualityMetrics(
                personalization_score=0.7,
                predicted_response_rate=0.3,
                readability_score=0.6,
                sentiment_score=0.7,
                urgency_score=0.5,
                value_proposition_score=0.6,
                call_to_action_score=0.7,
                overall_quality_score=0.65
            )
            
            optimized_message = OptimizedMessage(
                original_message="Original message",
                optimized_message="Optimized message",
                quality_metrics=medium_quality,
                optimization_notes=["Needs improvement"]
            )
            
            approval = optimizer.implement_approval_workflow(optimized_message)
            
            assert approval.status == MessageStatus.NEEDS_REVISION
            assert len(approval.suggested_improvements) > 0

    def test_implement_approval_workflow_rejected(self):
        """Test approval workflow for low-quality message"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Low quality message
            low_quality = QualityMetrics(
                personalization_score=0.3,
                predicted_response_rate=0.1,
                readability_score=0.4,
                sentiment_score=0.5,
                urgency_score=0.3,
                value_proposition_score=0.3,
                call_to_action_score=0.4,
                overall_quality_score=0.35
            )
            
            optimized_message = OptimizedMessage(
                original_message="Original message",
                optimized_message="Optimized message",
                quality_metrics=low_quality,
                optimization_notes=["Major issues"]
            )
            
            approval = optimizer.implement_approval_workflow(optimized_message)
            
            assert approval.status == MessageStatus.REJECTED
            assert len(approval.suggested_improvements) > 0

    @patch('agents.message_quality_optimizer.MessageQualityOptimizer.test_message_quality_with_research')
    def test_batch_quality_test(self, mock_test_quality):
        """Test batch quality testing functionality"""
        with patch('agents.message_quality_optimizer.ResearchStorageManager'):
            optimizer = MessageQualityOptimizer(self.api_keys, self.mongodb_connection)
            
            # Mock successful quality test
            mock_quality_metrics = QualityMetrics(
                personalization_score=0.9,
                predicted_response_rate=0.45,
                readability_score=0.8,
                sentiment_score=0.8,
                urgency_score=0.7,
                value_proposition_score=0.8,
                call_to_action_score=0.9,
                overall_quality_score=0.82
            )
            
            mock_optimized_message = OptimizedMessage(
                original_message="Original",
                optimized_message="Optimized",
                quality_metrics=mock_quality_metrics,
                optimization_notes=[]
            )
            
            mock_test_quality.return_value = mock_optimized_message
            
            # Test data
            test_leads = [
                (self.sample_lead_input, self.sample_sender_info),
                (LeadInput("Test Lead", "Test Company", "CEO", "Tech", "100"), self.sample_sender_info)
            ]
            
            results = optimizer.batch_quality_test(test_leads, target_count=2)
            
            assert isinstance(results, dict)
            assert results['total_tests'] == 2
            assert results['success_rate'] > 0
            assert 'average_response_rate' in results
            assert 'approval_rate' in results

    def test_quality_metrics_dataclass(self):
        """Test QualityMetrics dataclass"""
        metrics = QualityMetrics(
            personalization_score=0.9,
            predicted_response_rate=0.45,
            readability_score=0.8,
            sentiment_score=0.8,
            urgency_score=0.7,
            value_proposition_score=0.8,
            call_to_action_score=0.9,
            overall_quality_score=0.82
        )
        
        assert metrics.personalization_score == 0.9
        assert metrics.predicted_response_rate == 0.45
        assert metrics.overall_quality_score == 0.82

    def test_message_approval_dataclass(self):
        """Test MessageApproval dataclass"""
        quality_metrics = QualityMetrics(
            personalization_score=0.9,
            predicted_response_rate=0.45,
            readability_score=0.8,
            sentiment_score=0.8,
            urgency_score=0.7,
            value_proposition_score=0.8,
            call_to_action_score=0.9,
            overall_quality_score=0.82
        )
        
        approval = MessageApproval(
            message_id="test_123",
            status=MessageStatus.APPROVED,
            reviewer_notes="Excellent message",
            approval_timestamp="2024-01-01T00:00:00",
            quality_metrics=quality_metrics,
            suggested_improvements=[]
        )
        
        assert approval.message_id == "test_123"
        assert approval.status == MessageStatus.APPROVED
        assert approval.quality_metrics.overall_quality_score == 0.82

    def test_optimized_message_dataclass(self):
        """Test OptimizedMessage dataclass"""
        quality_metrics = QualityMetrics(
            personalization_score=0.9,
            predicted_response_rate=0.45,
            readability_score=0.8,
            sentiment_score=0.8,
            urgency_score=0.7,
            value_proposition_score=0.8,
            call_to_action_score=0.9,
            overall_quality_score=0.82
        )
        
        optimized = OptimizedMessage(
            original_message="Original message",
            optimized_message="Optimized message",
            quality_metrics=quality_metrics,
            optimization_notes=["Improved personalization"]
        )
        
        assert optimized.original_message == "Original message"
        assert optimized.optimized_message == "Optimized message"
        assert len(optimized.optimization_notes) == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
