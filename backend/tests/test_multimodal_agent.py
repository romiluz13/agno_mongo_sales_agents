"""
Test suite for Multimodal Message Agent

Tests the multimodal capabilities including voice generation, image creation,
and comprehensive message generation functionality.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.multimodal_message_agent import (
    MultimodalMessageAgent,
    MultimodalOutput,
    create_multimodal_message_agent
)
from agents.message_agent import MessageInput, LeadData, ResearchInsights, SenderInfo


class TestMultimodalMessageAgent:
    """Test cases for Multimodal Message Agent functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_keys = {
            'GEMINI_API_KEY': 'test_gemini_key',
            'OPENAI_API_KEY': 'test_openai_key'
        }
        
        self.test_output_dir = "test_tmp"
        
        self.sample_message_input = MessageInput(
            lead_data=LeadData(
                name="Jensen Huang",
                company="NVIDIA",
                title="CEO"
            ),
            research_insights=ResearchInsights(
                recent_news="NVIDIA reports record Q3 revenue growth of 206%",
                conversation_hooks=["Record revenue", "AI chip demand", "Data center expansion"],
                timing_rationale="Perfect timing for AI infrastructure discussions"
            ),
            message_type="multimodal",
            sender_info=SenderInfo(
                name="Sarah Chen",
                company="CloudScale Solutions",
                value_prop="AI infrastructure optimization"
            )
        )

    def test_multimodal_agent_initialization(self):
        """Test that Multimodal Message Agent initializes correctly"""
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        
        assert agent is not None
        assert agent.text_agent is not None
        assert agent.voice_agent is not None
        assert agent.image_agent is not None
        assert agent.output_dir.exists()

    def test_create_multimodal_agent_function(self):
        """Test the convenience function for creating multimodal agent"""
        agent = create_multimodal_message_agent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        
        assert isinstance(agent, MultimodalMessageAgent)
        assert agent.api_keys == self.api_keys

    def test_build_text_generation_query(self):
        """Test text generation query building"""
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        query = agent._build_text_generation_query(self.sample_message_input)
        
        assert "Jensen Huang" in query
        assert "NVIDIA" in query
        assert "CEO" in query
        assert "Record revenue" in query
        assert "Sarah Chen" in query
        assert "CloudScale Solutions" in query

    def test_create_voice_script(self):
        """Test voice script creation"""
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        
        message_text = "Hi Jensen! Congrats on NVIDIA's record revenue growth!"
        voice_script = agent._create_voice_script(message_text, self.sample_message_input)
        
        assert isinstance(voice_script, str)
        assert "Jensen Huang" in voice_script
        assert "NVIDIA" in voice_script
        assert "Sarah Chen" in voice_script
        assert "30 seconds" in voice_script

    def test_create_image_prompt(self):
        """Test image generation prompt creation"""
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        
        message_text = "Congrats on the record revenue!"
        image_prompt = agent._create_image_prompt(message_text, self.sample_message_input)
        
        assert isinstance(image_prompt, str)
        assert "NVIDIA" in image_prompt
        assert "CloudScale Solutions" in image_prompt
        assert "professional" in image_prompt.lower()
        assert "branding" in image_prompt.lower()

    def test_parse_text_response_with_json(self):
        """Test parsing text response with valid JSON"""
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        
        json_response = '''
        {
            "message_text": "Hi Jensen! Congrats on NVIDIA's record revenue!",
            "message_voice_script": "Voice version here",
            "message_image_concept": "Image concept here",
            "personalization_score": 0.92,
            "predicted_response_rate": 0.48,
            "tone_analysis": "Professional and congratulatory"
        }
        '''
        
        result = agent._parse_text_response(json_response, self.sample_message_input)
        
        assert result["message_text"] == "Hi Jensen! Congrats on NVIDIA's record revenue!"
        assert result["personalization_score"] == 0.92
        assert result["predicted_response_rate"] == 0.48

    def test_parse_text_response_fallback(self):
        """Test parsing text response with fallback"""
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        
        invalid_response = "This is not JSON format"
        result = agent._parse_text_response(invalid_response, self.sample_message_input)
        
        assert isinstance(result, dict)
        assert "message_text" in result
        assert "Jensen Huang" in result["message_text"]
        assert "NVIDIA" in result["message_text"]

    def test_create_fallback_multimodal_output(self):
        """Test fallback multimodal output creation"""
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        
        error_msg = "Test error message"
        result = agent._create_fallback_multimodal_output(self.sample_message_input, error_msg)
        
        assert isinstance(result, MultimodalOutput)
        assert "Jensen Huang" in result.message_text
        assert "NVIDIA" in result.message_text
        assert result.personalization_score > 0
        assert error_msg in result.tone_analysis
        assert result.voice_audio_content is None
        assert result.generated_image_content is None

    @patch('agents.multimodal_message_agent.Agent')
    def test_generate_text_message(self, mock_agent_class):
        """Test text message generation"""
        # Mock the agent response
        mock_response = Mock()
        mock_response.content = '''
        {
            "message_text": "Hi Jensen! Congrats on NVIDIA's record Q3 revenue growth of 206%! Your AI chip innovations are transforming the industry. Would you be open to discussing how we optimize AI infrastructure for companies experiencing similar explosive growth?",
            "message_voice_script": "Hi Jensen, this is Sarah from CloudScale Solutions. Congratulations on NVIDIA's incredible Q3 results!",
            "message_image_concept": "Professional congratulatory image with NVIDIA and CloudScale logos",
            "personalization_score": 0.95,
            "predicted_response_rate": 0.52,
            "tone_analysis": "Professional, congratulatory, industry-focused"
        }
        '''
        
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = mock_response
        mock_agent_class.return_value = mock_agent_instance
        
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        result = agent._generate_text_message(self.sample_message_input)
        
        assert isinstance(result, dict)
        assert result["personalization_score"] == 0.95
        assert result["predicted_response_rate"] == 0.52
        assert "Jensen" in result["message_text"]
        assert "NVIDIA" in result["message_text"]

    @patch('agents.multimodal_message_agent.write_audio_to_file')
    @patch('agents.multimodal_message_agent.Agent')
    def test_generate_voice_message_success(self, mock_agent_class, mock_write_audio):
        """Test successful voice message generation"""
        # Mock the voice agent response
        mock_response = Mock()
        mock_response.response_audio = Mock()
        mock_response.response_audio.content = b"fake_audio_content"
        
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = mock_response
        mock_agent_class.return_value = mock_agent_instance
        
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        agent.voice_enabled = True  # Force enable for test
        
        message_text = "Hi Jensen! Congrats on the record revenue!"
        voice_content, voice_path, audio_duration = agent._generate_voice_message(
            message_text, self.sample_message_input
        )
        
        assert voice_content == b"fake_audio_content"
        assert voice_path is not None
        assert "NVIDIA" in voice_path
        assert audio_duration > 0
        mock_write_audio.assert_called_once()

    def test_generate_voice_message_disabled(self):
        """Test voice message generation when disabled"""
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        agent.voice_enabled = False
        
        message_text = "Test message"
        voice_content, voice_path, audio_duration = agent._generate_voice_message(
            message_text, self.sample_message_input
        )
        
        assert voice_content is None
        assert voice_path is None
        assert audio_duration is None

    @patch('agents.multimodal_message_agent.Image')
    @patch('agents.multimodal_message_agent.BytesIO')
    @patch('agents.multimodal_message_agent.Agent')
    def test_generate_image_message_success(self, mock_agent_class, mock_bytesio, mock_pil_image):
        """Test successful image message generation"""
        # Mock the image agent response
        mock_image_response = Mock()
        mock_image_response.content = b"fake_image_content"
        
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = Mock()
        mock_agent_instance.get_images.return_value = [mock_image_response]
        mock_agent_class.return_value = mock_agent_instance
        
        # Mock PIL Image
        mock_image = Mock()
        mock_pil_image.open.return_value = mock_image
        
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        
        message_text = "Congrats on the record revenue!"
        image_content, image_path, image_description = agent._generate_image_message(
            message_text, self.sample_message_input
        )
        
        assert image_content == b"fake_image_content"
        assert image_path is not None
        assert "NVIDIA" in image_path
        assert image_description is not None
        assert "NVIDIA" in image_description

    @patch('agents.multimodal_message_agent.Agent')
    def test_generate_image_message_no_images(self, mock_agent_class):
        """Test image message generation when no images returned"""
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = Mock()
        mock_agent_instance.get_images.return_value = []
        mock_agent_class.return_value = mock_agent_instance
        
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        
        message_text = "Test message"
        image_content, image_path, image_description = agent._generate_image_message(
            message_text, self.sample_message_input
        )
        
        assert image_content is None
        assert image_path is None
        assert image_description is None

    @patch('agents.multimodal_message_agent.MultimodalMessageAgent._generate_image_message')
    @patch('agents.multimodal_message_agent.MultimodalMessageAgent._generate_voice_message')
    @patch('agents.multimodal_message_agent.MultimodalMessageAgent._generate_text_message')
    def test_generate_multimodal_message_complete(self, mock_text, mock_voice, mock_image):
        """Test complete multimodal message generation"""
        # Mock all generation methods
        mock_text.return_value = {
            "message_text": "Hi Jensen! Congrats on NVIDIA's record revenue!",
            "message_voice_script": "Voice script here",
            "message_image_concept": "Image concept here",
            "personalization_score": 0.95,
            "predicted_response_rate": 0.52,
            "tone_analysis": "Professional"
        }
        
        mock_voice.return_value = (b"audio_content", "/path/to/audio.wav", 15.5)
        mock_image.return_value = (b"image_content", "/path/to/image.png", "Image description")
        
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        result = agent.generate_multimodal_message(
            self.sample_message_input, 
            include_voice=True, 
            include_image=True
        )
        
        assert isinstance(result, MultimodalOutput)
        assert result.personalization_score == 0.95
        assert result.predicted_response_rate == 0.52
        assert result.voice_audio_content == b"audio_content"
        assert result.voice_audio_path == "/path/to/audio.wav"
        assert result.generated_image_content == b"image_content"
        assert result.generated_image_path == "/path/to/image.png"
        assert result.audio_duration == 15.5

    @patch('agents.multimodal_message_agent.MultimodalMessageAgent._generate_text_message')
    def test_generate_multimodal_message_text_only(self, mock_text):
        """Test multimodal message generation with text only"""
        mock_text.return_value = {
            "message_text": "Test message",
            "message_voice_script": "Voice script",
            "message_image_concept": "Image concept",
            "personalization_score": 0.8,
            "predicted_response_rate": 0.4,
            "tone_analysis": "Professional"
        }
        
        agent = MultimodalMessageAgent(api_keys=self.api_keys, output_dir=self.test_output_dir)
        result = agent.generate_multimodal_message(
            self.sample_message_input,
            include_voice=False,
            include_image=False
        )
        
        assert isinstance(result, MultimodalOutput)
        assert result.voice_audio_content is None
        assert result.generated_image_content is None
        assert result.message_text == "Test message"

    def test_multimodal_output_dataclass(self):
        """Test MultimodalOutput dataclass"""
        output = MultimodalOutput(
            message_text="Test message",
            message_voice_script="Voice script",
            message_image_concept="Image concept",
            personalization_score=0.9,
            predicted_response_rate=0.5,
            generation_timestamp="2024-01-01T00:00:00",
            message_length=12,
            tone_analysis="Professional",
            voice_audio_content=b"audio",
            voice_audio_path="/path/to/audio.wav",
            generated_image_content=b"image",
            generated_image_path="/path/to/image.png",
            image_description="Test image",
            audio_duration=10.5
        )
        
        assert output.message_text == "Test message"
        assert output.personalization_score == 0.9
        assert output.voice_audio_content == b"audio"
        assert output.generated_image_content == b"image"
        assert output.audio_duration == 10.5

    def teardown_method(self):
        """Cleanup test environment"""
        # Clean up test output directory
        test_dir = Path(self.test_output_dir)
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
