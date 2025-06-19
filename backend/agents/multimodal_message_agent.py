"""
Multimodal Message Generation Agent Implementation

This module implements advanced multimodal capabilities for the Message Generation Agent,
including voice generation, image creation, and audio processing using Gemini AI.

Based on cookbook/models/google/gemini/audio_input_output.py and image_generation.py patterns.
"""

import json
import logging
import base64
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from pathlib import Path

from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import Audio, Image as AgnoImage
from agno.utils.audio import write_audio_to_file
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MultimodalOutput:
    """Enhanced output with multimodal capabilities"""
    message_text: str
    message_voice_script: str
    message_image_concept: str
    personalization_score: float
    predicted_response_rate: float
    generation_timestamp: str
    message_length: int
    tone_analysis: str
    # Multimodal enhancements
    voice_audio_content: Optional[bytes] = None
    voice_audio_path: Optional[str] = None
    generated_image_content: Optional[bytes] = None
    generated_image_path: Optional[str] = None
    image_description: Optional[str] = None
    audio_duration: Optional[float] = None


class MultimodalMessageAgent:
    """
    Advanced Message Generation Agent with multimodal capabilities including
    voice generation, image creation, and audio processing.
    """
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None, output_dir: str = "tmp"):
        """
        Initialize the Multimodal Message Agent.
        
        Args:
            api_keys: Dictionary containing API keys
            output_dir: Directory for saving generated media files
        """
        self.api_keys = api_keys or {}
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize text message agent
        self.text_agent = Agent(
            name="Text Message Agent",
            model=Gemini(id="gemini-2.0-flash-exp"),
            instructions=[self._get_text_message_prompt()],
            markdown=True,
            show_tool_calls=True
        )
        
        # Initialize voice generation agent (using OpenAI for voice capabilities)
        try:
            from agno.models.openai import OpenAIChat
            self.voice_agent = Agent(
                name="Voice Message Agent",
                model=OpenAIChat(
                    id="gpt-4o-audio-preview",
                    modalities=["text", "audio"],
                    audio={"voice": "alloy", "format": "wav"}
                ),
                instructions=[self._get_voice_message_prompt()],
                markdown=True
            )
            self.voice_enabled = True
        except ImportError:
            logger.warning("OpenAI not available for voice generation, using text-only voice scripts")
            self.voice_agent = self.text_agent
            self.voice_enabled = False
        
        # Initialize image generation agent
        self.image_agent = Agent(
            name="Image Generation Agent",
            model=Gemini(
                id="gemini-2.0-flash-exp-image-generation",
                response_modalities=["Text", "Image"]
            ),
            instructions=[self._get_image_generation_prompt()],
            show_tool_calls=True
        )
        
        logger.info("Multimodal Message Agent initialized successfully")

    def generate_multimodal_message(self, message_input, include_voice: bool = True, include_image: bool = True) -> MultimodalOutput:
        """
        Generate a complete multimodal message with text, voice, and image components.
        
        Args:
            message_input: MessageInput object containing lead and research data
            include_voice: Whether to generate voice content
            include_image: Whether to generate image content
            
        Returns:
            MultimodalOutput with all generated content
        """
        try:
            logger.info(f"Generating multimodal message for {message_input.lead_data.name}")
            
            # Step 1: Generate base text message
            text_result = self._generate_text_message(message_input)
            
            # Step 2: Generate voice content if requested
            voice_content = None
            voice_path = None
            audio_duration = None
            
            if include_voice:
                voice_content, voice_path, audio_duration = self._generate_voice_message(
                    text_result['message_text'], 
                    message_input
                )
            
            # Step 3: Generate image content if requested
            image_content = None
            image_path = None
            image_description = None
            
            if include_image:
                image_content, image_path, image_description = self._generate_image_message(
                    text_result['message_text'],
                    message_input
                )
            
            # Create comprehensive output with proper type conversion
            output = MultimodalOutput(
                message_text=text_result.get('message_text', ''),
                message_voice_script=text_result.get('message_voice_script', ''),
                message_image_concept=text_result.get('message_image_concept', ''),
                personalization_score=self._ensure_float(text_result.get('personalization_score', 0.5)),
                predicted_response_rate=self._ensure_float(text_result.get('predicted_response_rate', 0.2)),
                generation_timestamp=datetime.now().isoformat(),
                message_length=len(text_result.get('message_text', '')),
                tone_analysis=str(text_result.get('tone_analysis', 'Professional')),
                voice_audio_content=voice_content,
                voice_audio_path=voice_path,
                generated_image_content=image_content,
                generated_image_path=image_path,
                image_description=image_description,
                audio_duration=audio_duration
            )
            
            logger.info(f"Multimodal message generated successfully with {len([x for x in [voice_content, image_content] if x])} media components")
            return output
            
        except Exception as e:
            logger.error(f"Multimodal message generation failed: {str(e)}")
            return self._create_fallback_multimodal_output(message_input, str(e))

    def _generate_text_message(self, message_input) -> Dict[str, Any]:
        """Generate the base text message"""
        query = self._build_text_generation_query(message_input)
        response = self.text_agent.run(query)
        return self._parse_text_response(response.content, message_input)

    def _generate_voice_message(self, message_text: str, message_input) -> tuple[Optional[bytes], Optional[str], Optional[float]]:
        """Generate voice audio from the text message"""
        if not self.voice_enabled:
            logger.info("Voice generation not available, skipping")
            return None, None, None
        
        try:
            # Create voice-optimized script
            voice_script = self._create_voice_script(message_text, message_input)
            
            # Generate audio using voice agent
            response = self.voice_agent.run(voice_script)
            
            if hasattr(response, 'response_audio') and response.response_audio:
                # Save audio to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_filename = f"voice_message_{message_input.lead_data.company.replace(' ', '_')}_{timestamp}.wav"
                audio_path = self.output_dir / audio_filename
                
                write_audio_to_file(
                    audio=response.response_audio.content,
                    filename=str(audio_path)
                )
                
                # Estimate duration (rough calculation)
                audio_duration = len(voice_script.split()) * 0.6  # ~0.6 seconds per word
                
                logger.info(f"Voice message generated: {audio_path}")
                return response.response_audio.content, str(audio_path), audio_duration
            
        except Exception as e:
            logger.warning(f"Voice generation failed: {e}")
        
        return None, None, None

    def _generate_image_message(self, message_text: str, message_input) -> tuple[Optional[bytes], Optional[str], Optional[str]]:
        """Generate image content for the message"""
        try:
            # Create image generation prompt
            image_prompt = self._create_image_prompt(message_text, message_input)
            
            # Generate image using image agent
            response = self.image_agent.run(image_prompt)
            
            # Get generated images
            images = self.image_agent.get_images()
            
            if images and isinstance(images, list) and len(images) > 0:
                image_response = images[0]
                image_bytes = image_response.content
                
                # Save image to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"message_image_{message_input.lead_data.company.replace(' ', '_')}_{timestamp}.png"
                image_path = self.output_dir / image_filename
                
                # Convert and save image
                image = Image.open(BytesIO(image_bytes))
                image.save(image_path)
                
                # Create description
                image_description = f"Generated image for {message_input.lead_data.company} outreach message"
                
                logger.info(f"Image generated: {image_path}")
                return image_bytes, str(image_path), image_description
            
        except Exception as e:
            logger.warning(f"Image generation failed: {e}")
        
        return None, None, None

    def _build_text_generation_query(self, message_input) -> str:
        """Build text message generation query"""
        return f"""
Generate a highly personalized sales message for:

LEAD: {message_input.lead_data.name} ({message_input.lead_data.title}) at {message_input.lead_data.company}
RECENT NEWS: {message_input.research_insights.recent_news}
HOOKS: {', '.join(message_input.research_insights.conversation_hooks)}
SENDER: {message_input.sender_info.name} from {message_input.sender_info.company}
VALUE PROP: {message_input.sender_info.value_prop}

Return JSON with message_text, message_voice_script, message_image_concept, personalization_score, predicted_response_rate, and tone_analysis.
"""

    def _create_voice_script(self, message_text: str, message_input) -> str:
        """Create optimized voice script from text message"""
        return f"""
Create a natural, conversational voice message based on this text:

"{message_text}"

Make it sound warm, professional, and conversational. The speaker is {message_input.sender_info.name} from {message_input.sender_info.company} reaching out to {message_input.lead_data.name} at {message_input.lead_data.company}.

Keep it under 30 seconds when spoken naturally.
"""

    def _create_image_prompt(self, message_text: str, message_input) -> str:
        """Create image generation prompt"""
        return f"""
Create a professional business outreach image that includes:

1. {message_input.lead_data.company} company branding elements
2. {message_input.sender_info.company} company branding
3. Visual representation of: {message_input.research_insights.recent_news}
4. Professional, clean design suitable for business communication
5. Congratulatory or positive messaging theme

Style: Modern, professional, business-appropriate
Colors: Corporate blues, whites, subtle accent colors
Layout: Clean, uncluttered, easy to read
"""

    def _parse_text_response(self, response_content: str, message_input) -> Dict[str, Any]:
        """Parse text response with fallback"""
        try:
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback parsing
        return {
            "message_text": f"Hi {message_input.lead_data.name}! Congrats on {message_input.lead_data.company}'s recent achievements. Would love to discuss {message_input.sender_info.value_prop} opportunities.",
            "message_voice_script": f"Hi {message_input.lead_data.name}, this is {message_input.sender_info.name} from {message_input.sender_info.company}.",
            "message_image_concept": f"Professional image featuring {message_input.lead_data.company} and {message_input.sender_info.company} branding",
            "personalization_score": 0.7,
            "predicted_response_rate": 0.3,
            "tone_analysis": "Professional and friendly"
        }

    def _get_text_message_prompt(self) -> str:
        """Get text message generation prompt"""
        return """
You are a world-class sales copywriter. Create highly personalized, compelling messages that achieve 40%+ response rates.

PRINCIPLES:
1. RELEVANCE: Every word relevant to their situation
2. TIMING: Reference recent events
3. VALUE: Lead with insights, not product
4. BREVITY: Maximum 3 sentences
5. CURIOSITY: End with compelling question

Return JSON format with all required fields.
"""

    def _get_voice_message_prompt(self) -> str:
        """Get voice message generation prompt"""
        return """
You are creating a warm, professional voice message for sales outreach.

VOICE GUIDELINES:
- Conversational and natural tone
- Enthusiastic but not pushy
- Clear pronunciation and pacing
- Under 30 seconds when spoken
- Include natural pauses

Create a voice message that sounds genuine and builds rapport.
"""

    def _get_image_generation_prompt(self) -> str:
        """Get image generation prompt"""
        return """
Create professional business outreach images that:
- Include relevant company branding
- Support the message content
- Use clean, modern design
- Appropriate for business communication
- Eye-catching but professional
"""

    def _ensure_float(self, value) -> float:
        """Ensure value is a float, handling string conversions"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                # Try to extract numeric value from string
                import re
                numbers = re.findall(r'\d+\.?\d*', value)
                if numbers:
                    return float(numbers[0])
                return 0.5  # Default fallback
            else:
                return 0.5  # Default fallback
        except:
            return 0.5  # Default fallback

    def _create_fallback_multimodal_output(self, message_input, error_msg: str) -> MultimodalOutput:
        """Create fallback output when generation fails"""
        fallback_text = f"Hi {message_input.lead_data.name}! I'd love to connect about {message_input.sender_info.value_prop} opportunities for {message_input.lead_data.company}."
        
        return MultimodalOutput(
            message_text=fallback_text,
            message_voice_script=f"Hi {message_input.lead_data.name}, this is {message_input.sender_info.name}. {fallback_text}",
            message_image_concept=f"Professional business card with {message_input.sender_info.company} branding",
            personalization_score=0.3,
            predicted_response_rate=0.15,
            generation_timestamp=datetime.now().isoformat(),
            message_length=len(fallback_text),
            tone_analysis=f"Fallback message due to error: {error_msg}",
            voice_audio_content=None,
            voice_audio_path=None,
            generated_image_content=None,
            generated_image_path=None,
            image_description=None,
            audio_duration=None
        )


# Convenience function
def create_multimodal_message_agent(api_keys: Optional[Dict[str, str]] = None, output_dir: str = "tmp") -> MultimodalMessageAgent:
    """Create and return a configured Multimodal Message Agent instance."""
    return MultimodalMessageAgent(api_keys=api_keys, output_dir=output_dir)


# Example usage
if __name__ == "__main__":
    from agents.message_agent import MessageInput, LeadData, ResearchInsights, SenderInfo
    
    # Example usage
    agent = create_multimodal_message_agent()
    
    sample_input = MessageInput(
        lead_data=LeadData(
            name="Jensen Huang",
            company="NVIDIA",
            title="CEO"
        ),
        research_insights=ResearchInsights(
            recent_news="NVIDIA reports record Q3 revenue growth",
            conversation_hooks=["Record revenue", "AI chip demand", "Data center expansion"],
            timing_rationale="Perfect timing for AI infrastructure discussions"
        ),
        message_type="multimodal",
        sender_info=SenderInfo(
            name="Sarah",
            company="CloudScale",
            value_prop="AI infrastructure optimization"
        )
    )
    
    result = agent.generate_multimodal_message(sample_input)
    print(f"Multimodal message generated with personalization: {result.personalization_score}")
    print(f"Voice audio: {'Generated' if result.voice_audio_content else 'Not generated'}")
    print(f"Image: {'Generated' if result.generated_image_content else 'Not generated'}")
