"""
Test suite for Message Generation Agent

Tests the Message Generation Agent implementation to ensure it works correctly
with the Agno framework and produces high-quality personalized messages.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.message_agent import (
    MessageGenerationAgent, 
    LeadData, 
    ResearchInsights, 
    SenderInfo, 
    MessageInput, 
    MessageOutput,
    create_message_agent
)


class TestMessageGenerationAgent:
    """Test cases for Message Generation Agent functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_keys = {
            'GEMINI_API_KEY': 'test_gemini_key'
        }
        
        self.sample_lead_data = LeadData(
            name="John Doe",
            company="Acme Corp",
            title="VP of Sales"
        )
        
        self.sample_research_insights = ResearchInsights(
            recent_news="Raised $50M Series B funding led by Sequoia Capital",
            conversation_hooks=["Series B funding", "Scaling challenges", "European expansion"],
            timing_rationale="Perfect timing for sales optimization solutions"
        )
        
        self.sample_sender_info = SenderInfo(
            name="Sarah",
            company="TechCorp",
            value_prop="Sales process optimization"
        )
        
        self.sample_message_input = MessageInput(
            lead_data=self.sample_lead_data,
            research_insights=self.sample_research_insights,
            message_type="text",
            sender_info=self.sample_sender_info
        )

    def test_message_agent_initialization(self):
        """Test that Message Generation Agent initializes correctly"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        assert agent is not None
        assert agent.message_agent is not None
        assert agent.voice_agent is not None
        assert agent.image_agent is not None
        assert agent.api_keys == self.api_keys

    def test_create_message_agent_function(self):
        """Test the convenience function for creating message agent"""
        agent = create_message_agent(api_keys=self.api_keys)
        
        assert isinstance(agent, MessageGenerationAgent)
        assert agent.api_keys == self.api_keys

    def test_build_generation_query(self):
        """Test message generation query building"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        query = agent._build_generation_query(self.sample_message_input)
        
        assert "John Doe" in query
        assert "Acme Corp" in query
        assert "VP of Sales" in query
        assert "Series B funding" in query
        assert "Sarah" in query
        assert "TechCorp" in query

    def test_calculate_personalization_score(self):
        """Test personalization score calculation"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        # Test with highly personalized message
        personalized_message = "Hi John! Congrats on Acme Corp's Series B funding! As a VP of Sales, you're probably focused on scaling challenges right now."
        score = agent._calculate_personalization_score(personalized_message, self.sample_message_input)
        assert score > 0.8  # Should be high for personalized message
        
        # Test with generic message
        generic_message = "Hi there! I'd like to discuss our services with you."
        score = agent._calculate_personalization_score(generic_message, self.sample_message_input)
        assert score < 0.3  # Should be low for generic message

    def test_predict_response_rate(self):
        """Test response rate prediction"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        # Test with high personalization
        high_rate = agent._predict_response_rate("Great personalized message?", 0.9)
        assert high_rate > 0.4
        
        # Test with low personalization
        low_rate = agent._predict_response_rate("Generic message", 0.2)
        assert low_rate < 0.3

    def test_extract_message_from_text(self):
        """Test fallback message extraction from text"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        sample_text = "Here's a great message: Hi John! Congrats on the funding!"
        result = agent._extract_message_from_text(sample_text)
        
        assert isinstance(result, dict)
        assert "message_text" in result
        assert "message_voice_script" in result
        assert "message_image_concept" in result
        assert "personalization_score" in result
        assert "predicted_response_rate" in result

    def test_parse_message_response_with_json(self):
        """Test parsing response with valid JSON"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        json_response = '''
        Some text before
        {
            "message_text": "Hi John! Congrats on the funding!",
            "message_voice_script": "Voice version here",
            "message_image_concept": "Image concept here",
            "personalization_score": 0.85,
            "predicted_response_rate": 0.45
        }
        Some text after
        '''
        
        result = agent._parse_message_response(json_response)
        
        assert result["message_text"] == "Hi John! Congrats on the funding!"
        assert result["personalization_score"] == 0.85
        assert result["predicted_response_rate"] == 0.45

    def test_parse_message_response_without_json(self):
        """Test parsing response without valid JSON"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        text_response = "Hi John! This is a great personalized message about your recent funding!"
        result = agent._parse_message_response(text_response)
        
        assert isinstance(result, dict)
        assert "message_text" in result
        assert len(result["message_text"]) > 10

    def test_enhance_message_data(self):
        """Test message data enhancement"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        basic_data = {
            "message_text": "Hi John! Congrats on Acme Corp's funding!"
        }
        
        enhanced = agent._enhance_message_data(basic_data, self.sample_message_input)
        
        assert "personalization_score" in enhanced
        assert "predicted_response_rate" in enhanced
        assert "message_voice_script" in enhanced
        assert "message_image_concept" in enhanced
        assert enhanced["personalization_score"] > 0

    def test_generate_voice_script(self):
        """Test voice script generation"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        text_message = "Hi John! Congrats on the funding!"
        voice_script = agent._generate_voice_script(text_message)
        
        assert isinstance(voice_script, str)
        assert len(voice_script) > len(text_message)
        assert "Hi there!" in voice_script

    def test_generate_image_concept(self):
        """Test image concept generation"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        concept = agent._generate_image_concept(self.sample_message_input)
        
        assert isinstance(concept, str)
        assert "TechCorp" in concept
        assert "Acme Corp" in concept
        assert len(concept) > 20

    def test_create_fallback_message(self):
        """Test fallback message creation"""
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        
        error_msg = "Test error message"
        result = agent._create_fallback_message(self.sample_message_input, error_msg)
        
        assert isinstance(result, MessageOutput)
        assert "John Doe" in result.message_text
        assert "Acme Corp" in result.message_text
        assert result.personalization_score > 0
        assert error_msg in result.tone_analysis

    @patch('agents.message_agent.Agent')
    def test_generate_message_success(self, mock_agent_class):
        """Test successful message generation"""
        # Mock the agent response
        mock_response = Mock()
        mock_response.content = '''
        {
            "message_text": "Hi John! Congrats on Acme Corp's $50M Series B! I help SaaS companies optimize their sales processes during rapid growth phases. Would you be open to a 15-minute chat about how we've helped similar companies scale their sales teams?",
            "message_voice_script": "Hey John, this is Sarah from TechCorp. I just saw the news about your Series B funding - congratulations! I know scaling sales teams is probably top of mind right now. I'd love to share how we've helped other SaaS companies navigate similar growth phases. Would you be open to a quick 15-minute conversation?",
            "message_image_concept": "Company logo with congratulations message and growth chart visual",
            "personalization_score": 0.92,
            "predicted_response_rate": 0.45,
            "tone_analysis": "Professional, timely, value-focused"
        }
        '''
        
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = mock_response
        mock_agent_class.return_value = mock_agent_instance
        
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        result = agent.generate_message(self.sample_message_input)
        
        assert isinstance(result, MessageOutput)
        assert result.personalization_score == 0.92
        assert result.predicted_response_rate == 0.45
        assert "John" in result.message_text
        assert "Acme Corp" in result.message_text
        assert "Series B" in result.message_text

    @patch('agents.message_agent.Agent')
    def test_generate_message_failure(self, mock_agent_class):
        """Test message generation with failure"""
        # Mock the agent to raise an exception
        mock_agent_instance = Mock()
        mock_agent_instance.run.side_effect = Exception("API Error")
        mock_agent_class.return_value = mock_agent_instance
        
        agent = MessageGenerationAgent(api_keys=self.api_keys)
        result = agent.generate_message(self.sample_message_input)
        
        assert isinstance(result, MessageOutput)
        assert result.personalization_score > 0  # Should still have some personalization
        assert "John Doe" in result.message_text
        assert "API Error" in result.tone_analysis

    def test_dataclass_creation(self):
        """Test dataclass creation and validation"""
        # Test LeadData
        lead = LeadData(name="Test Name", company="Test Company", title="Test Title")
        assert lead.name == "Test Name"
        assert lead.company == "Test Company"
        assert lead.title == "Test Title"
        
        # Test ResearchInsights
        insights = ResearchInsights(
            recent_news="Test news",
            conversation_hooks=["hook1", "hook2"],
            timing_rationale="Test rationale"
        )
        assert insights.recent_news == "Test news"
        assert len(insights.conversation_hooks) == 2
        assert insights.timing_rationale == "Test rationale"
        
        # Test SenderInfo
        sender = SenderInfo(name="Test Sender", company="Test Company", value_prop="Test Value")
        assert sender.name == "Test Sender"
        assert sender.company == "Test Company"
        assert sender.value_prop == "Test Value"
        
        # Test MessageInput
        msg_input = MessageInput(
            lead_data=lead,
            research_insights=insights,
            message_type="text",
            sender_info=sender
        )
        assert msg_input.lead_data == lead
        assert msg_input.research_insights == insights
        assert msg_input.message_type == "text"
        assert msg_input.sender_info == sender
        
        # Test MessageOutput
        output = MessageOutput(
            message_text="Test message",
            message_voice_script="Test voice",
            message_image_concept="Test image",
            personalization_score=0.8,
            predicted_response_rate=0.4,
            generation_timestamp="2024-01-01T00:00:00",
            message_length=12,
            tone_analysis="Test tone"
        )
        assert output.message_text == "Test message"
        assert output.personalization_score == 0.8
        assert output.predicted_response_rate == 0.4


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
