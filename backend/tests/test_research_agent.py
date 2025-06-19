"""
Test suite for Research Agent

Tests the Research Agent implementation to ensure it works correctly
with the Agno framework and produces expected outputs.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.research_agent import ResearchAgent, LeadInput, ResearchOutput, create_research_agent


class TestResearchAgent:
    """Test cases for Research Agent functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_keys = {
            'TAVILY_API_KEY': 'test_tavily_key',
            'GEMINI_API_KEY': 'test_gemini_key'
        }
        
        self.sample_lead = LeadInput(
            lead_name="John Doe",
            company="Acme Corp",
            title="VP of Sales",
            industry="SaaS",
            company_size="500 employees"
        )

    def test_research_agent_initialization(self):
        """Test that Research Agent initializes correctly"""
        agent = ResearchAgent(api_keys=self.api_keys)
        
        assert agent is not None
        assert agent.agent is not None
        assert agent.api_keys == self.api_keys

    def test_create_research_agent_function(self):
        """Test the convenience function for creating research agent"""
        agent = create_research_agent(api_keys=self.api_keys)
        
        assert isinstance(agent, ResearchAgent)
        assert agent.api_keys == self.api_keys

    def test_build_research_query(self):
        """Test research query building"""
        agent = ResearchAgent(api_keys=self.api_keys)
        query = agent._build_research_query(self.sample_lead)
        
        assert "John Doe" in query
        assert "Acme Corp" in query
        assert "VP of Sales" in query
        assert "SaaS" in query
        assert "500 employees" in query

    def test_calculate_confidence_score(self):
        """Test confidence score calculation"""
        agent = ResearchAgent(api_keys=self.api_keys)
        
        # Test with complete data
        complete_data = {
            "company_intelligence": {
                "recent_news": "Some news",
                "growth_signals": ["Signal 1"],
                "challenges": ["Challenge 1"]
            },
            "decision_maker_insights": {
                "background": "Some background",
                "recent_activities": ["Activity 1"]
            }
        }
        
        score = agent._calculate_confidence_score(complete_data)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high for complete data
        
        # Test with minimal data
        minimal_data = {
            "company_intelligence": {},
            "decision_maker_insights": {}
        }
        
        score = agent._calculate_confidence_score(minimal_data)
        assert score == 0.0

    def test_extract_data_from_text(self):
        """Test fallback text extraction"""
        agent = ResearchAgent(api_keys=self.api_keys)
        
        sample_text = "This is some research text about a company"
        result = agent._extract_data_from_text(sample_text)
        
        assert isinstance(result, dict)
        assert "confidence_score" in result
        assert "company_intelligence" in result
        assert "decision_maker_insights" in result
        assert "conversation_hooks" in result
        assert "timing_rationale" in result

    def test_parse_research_response_with_json(self):
        """Test parsing response with valid JSON"""
        agent = ResearchAgent(api_keys=self.api_keys)
        
        json_response = '''
        Some text before
        {
            "confidence_score": 0.85,
            "company_intelligence": {
                "recent_news": "Test news"
            },
            "conversation_hooks": ["Hook 1", "Hook 2"]
        }
        Some text after
        '''
        
        result = agent._parse_research_response(json_response)
        
        assert result["confidence_score"] == 0.85
        assert result["company_intelligence"]["recent_news"] == "Test news"
        assert len(result["conversation_hooks"]) == 2

    def test_parse_research_response_without_json(self):
        """Test parsing response without valid JSON"""
        agent = ResearchAgent(api_keys=self.api_keys)
        
        text_response = "This is just plain text without JSON"
        result = agent._parse_research_response(text_response)
        
        assert isinstance(result, dict)
        assert "confidence_score" in result
        assert result["confidence_score"] == 0.6  # Default fallback score

    def test_create_fallback_output(self):
        """Test fallback output creation"""
        agent = ResearchAgent(api_keys=self.api_keys)
        
        error_msg = "Test error message"
        result = agent._create_fallback_output(self.sample_lead, error_msg)
        
        assert isinstance(result, ResearchOutput)
        assert result.confidence_score == 0.1
        assert error_msg in result.company_intelligence["recent_news"]
        assert len(result.conversation_hooks) >= 2
        assert "Acme Corp" in result.conversation_hooks[0]

    @patch('agents.research_agent.Agent')
    def test_research_lead_success(self, mock_agent_class):
        """Test successful lead research"""
        # Mock the agent response
        mock_response = Mock()
        mock_response.content = '''
        {
            "confidence_score": 0.85,
            "company_intelligence": {
                "recent_news": "Raised $50M Series B",
                "growth_signals": ["Hiring 100+ engineers"],
                "challenges": ["Scaling sales team"]
            },
            "decision_maker_insights": {
                "background": "Former Salesforce VP",
                "recent_activities": ["Speaking at SaaStr conference"]
            },
            "conversation_hooks": [
                "Congratulations on the Series B funding",
                "Saw your SaaStr talk about scaling sales teams"
            ],
            "timing_rationale": "Perfect timing for sales optimization solutions"
        }
        '''
        
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = mock_response
        mock_agent_class.return_value = mock_agent_instance
        
        agent = ResearchAgent(api_keys=self.api_keys)
        result = agent.research_lead(self.sample_lead)
        
        assert isinstance(result, ResearchOutput)
        assert result.confidence_score == 0.85
        assert "Series B" in result.company_intelligence["recent_news"]
        assert len(result.conversation_hooks) == 2
        assert result.timing_rationale == "Perfect timing for sales optimization solutions"

    @patch('agents.research_agent.Agent')
    def test_research_lead_failure(self, mock_agent_class):
        """Test lead research with failure"""
        # Mock the agent to raise an exception
        mock_agent_instance = Mock()
        mock_agent_instance.run.side_effect = Exception("API Error")
        mock_agent_class.return_value = mock_agent_instance
        
        agent = ResearchAgent(api_keys=self.api_keys)
        result = agent.research_lead(self.sample_lead)
        
        assert isinstance(result, ResearchOutput)
        assert result.confidence_score == 0.1
        assert "API Error" in result.company_intelligence["recent_news"]

    def test_lead_input_dataclass(self):
        """Test LeadInput dataclass"""
        lead = LeadInput(
            lead_name="Test Name",
            company="Test Company",
            title="Test Title",
            industry="Test Industry",
            company_size="100 employees"
        )
        
        assert lead.lead_name == "Test Name"
        assert lead.company == "Test Company"
        assert lead.title == "Test Title"
        assert lead.industry == "Test Industry"
        assert lead.company_size == "100 employees"

    def test_research_output_dataclass(self):
        """Test ResearchOutput dataclass"""
        output = ResearchOutput(
            confidence_score=0.85,
            company_intelligence={"test": "data"},
            decision_maker_insights={"test": "insights"},
            conversation_hooks=["hook1", "hook2"],
            timing_rationale="test rationale",
            research_timestamp="2024-01-01T00:00:00",
            sources=["source1", "source2"]
        )
        
        assert output.confidence_score == 0.85
        assert output.company_intelligence == {"test": "data"}
        assert len(output.conversation_hooks) == 2
        assert len(output.sources) == 2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
