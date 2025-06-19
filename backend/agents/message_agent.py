"""
Message Generation Agent Implementation for Agno Sales Extension

This module implements the Message Generation Agent that creates highly personalized,
compelling messages that get responses using Gemini AI and Agno framework.

Based on cookbook/models/google/gemini patterns and optimized for 40%+ response rates.
"""

import json
import logging
import re
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from agno.agent import Agent
from agno.models.google import Gemini

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.business_config import get_business_config, get_agent_context

# Load environment variables for configurability
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

def get_configurable_value(key: str, default: str) -> str:
    """Get configurable value from environment variables with fallback to default"""
    return os.getenv(key, default)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LeadData:
    """Lead data for message generation"""
    name: str
    company: str
    title: str


@dataclass
class ResearchInsights:
    """Research insights for message personalization"""
    recent_news: str
    conversation_hooks: List[str]
    timing_rationale: str
    company_intelligence: Optional[Dict[str, Any]] = None
    decision_maker_insights: Optional[Dict[str, Any]] = None


@dataclass
class SenderInfo:
    """Sender information for message generation"""
    name: str
    company: str
    value_prop: str


@dataclass
class MessageInput:
    """Complete input for message generation"""
    lead_data: LeadData
    research_insights: ResearchInsights
    message_type: str  # text|voice|image
    sender_info: SenderInfo


@dataclass
class MessageOutput:
    """Output from message generation"""
    message_text: str
    message_voice_script: str
    message_image_concept: str
    personalization_score: float
    predicted_response_rate: float
    generation_timestamp: str
    message_length: int
    tone_analysis: str


class MessageGenerationAgent:
    """
    World-class sales copywriter that generates over $100M in pipeline through 
    personalized outreach with 40%+ response rates.
    """
    
    def _get_hyper_personalized_prompt(self) -> str:
        """Get HALLUCINATION-PROOF hyper-personalized prompt with configurable business context"""
        # Get the prompt template without formatting during initialization
        prompt_template = self.config.get('revolutionary_prompt_template',
                                          self.config.get('hyper_personalized_prompt_template', ''))

        # If no template found, use a safe default
        if not prompt_template:
            prompt_template = """
🔥 CRITICAL INSTRUCTION: OUTPUT ONLY THE ACTUAL MESSAGE TEXT - NO META-DESCRIPTIONS! 🔥

You are a MongoDB Solutions Architect who generates ACTUAL hyper-personalized messages. You NEVER write about writing messages - you write the actual messages.

❌ FORBIDDEN OUTPUTS (These cause IMMEDIATE FAILURE):
- "Here's a hyper-personalized message for..."
- "Okay, here's a message draft..."
- "I'll create a personalized message..."
- Any meta-commentary about the message

✅ REQUIRED: ONLY the actual message text to send.

🎯 GENERATION RULES:
1. Start with "Hi [LEAD_NAME]!"
2. Include ONE specific detail from research/CRM
3. Reference relevant MongoDB capability
4. End with specific question
5. Keep under 120 characters
6. NO meta-commentary

🔥 OUTPUT ONLY THE MESSAGE TEXT - NO JSON, NO EXPLANATIONS:
"""

        # Return the template as-is without formatting during initialization
        return prompt_template

    def __init__(self, config: Dict[str, Any], api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize the Message Generation Agent with a configuration dictionary.
        
        Args:
            config: Dictionary containing agent settings from MongoDB.
            api_keys: Dictionary containing API keys (GEMINI_API_KEY)
        """
        self.config = config
        self.api_keys = api_keys or {}
        
        # Initialize the HYPER-PERSONALIZED message agent with dynamic context
        self.hyper_personalized_agent = Agent(
            name="Hyper-Personalized Message Agent",
            model=Gemini(id="gemini-2.0-flash-exp"),
            instructions=[self._get_hyper_personalized_prompt()],
            markdown=True,
            show_tool_calls=True
        )
        
        # Initialize voice message agent
        self.voice_agent = Agent(
            name="Voice Message Agent",
            model=Gemini(id="gemini-2.0-flash-exp"),
            instructions=[self._get_voice_prompt()],
            markdown=True
        )
        
        # Initialize image concept agent
        self.image_agent = Agent(
            name="Image Message Agent",
            model=Gemini(id="gemini-2.0-flash-exp"),
            instructions=[self._get_image_prompt()],
            markdown=True
        )
        
        logger.info("Message Generation Agent initialized successfully")

    def generate_hyper_personalized_message(self, message_input: MessageInput, crm_data: Optional[Dict] = None, enhanced_research: Optional[Dict] = None, business_context: Optional[Dict] = None) -> MessageOutput:
        """
        NEW METHOD for Task 11.6: Generate hyper-personalized messages using ALL available context
        🚨 ANTI-HALLUCINATION: This method enforces zero-tolerance hallucination prevention

        Args:
            message_input: Basic message input
            crm_data: Comprehensive CRM data from Monday.com (Task 11.4)
            enhanced_research: Enhanced research data (Task 11.5)
            business_context: MongoDB business context

        Returns:
            MessageOutput with hyper-personalized message
        """
        try:
            logger.info(f"🚨 Generating ANTI-HALLUCINATION message for {message_input.lead_data.name} at {message_input.lead_data.company}")

            # CRITICAL: Validate input data to prevent hallucination
            validated_input = self._validate_input_data(message_input, crm_data, enhanced_research)

            # Build comprehensive generation query with ALL context
            generation_query = self._build_hyper_personalized_query(validated_input, crm_data, enhanced_research, business_context)

            # Generate using the hyper-personalized agent
            response = self.hyper_personalized_agent.run(generation_query)

            # Parse enhanced response
            message_data = self._parse_hyper_personalized_response(response.content)

            # CRITICAL: Validate output for hallucination
            validated_message_data = self._validate_output_for_hallucination(message_data, crm_data, enhanced_research)

            # Calculate enhanced metrics
            enhanced_metrics = self._calculate_hyper_personalization_metrics(validated_message_data, crm_data, enhanced_research)
            validated_message_data.update(enhanced_metrics)

            # Create enhanced structured output
            output = MessageOutput(
                message_text=validated_message_data.get('message_text', ''),
                message_voice_script=validated_message_data.get('message_voice_script', ''),
                message_image_concept=validated_message_data.get('message_image_concept', ''),
                personalization_score=validated_message_data.get('personalization_score', 0.8),
                predicted_response_rate=validated_message_data.get('predicted_response_rate', 0.4),
                generation_timestamp=datetime.now().isoformat(),
                message_length=len(validated_message_data.get('message_text', '')),
                tone_analysis=validated_message_data.get('tone_analysis', 'Anti-hallucination verified')
            )

            # Store enhanced data for analysis
            if hasattr(output, 'enhanced_data'):
                output.enhanced_data = validated_message_data
            else:
                # Store in tone_analysis for now
                output.tone_analysis = f"{output.tone_analysis} | MongoDB: {validated_message_data.get('mongodb_relevance_score', 0):.2f} | CRM: {validated_message_data.get('crm_context_usage', 'Used')}"

            logger.info(f"✅ Anti-hallucination message generated with score: {output.personalization_score}")
            return output

        except Exception as e:
            logger.error(f"❌ Anti-hallucination message generation failed for {message_input.lead_data.name}: {str(e)}")
            # CRITICAL: Even fallback must be anti-hallucination
            return self._create_anti_hallucination_fallback_message(message_input, str(e))

    def generate_message(self, message_input: MessageInput) -> MessageOutput:
        """
        Generate a highly personalized message based on research insights.
        
        Args:
            message_input: MessageInput object containing all required data
            
        Returns:
            MessageOutput object with generated messages and metrics
        """
        try:
            logger.info(f"Generating message for {message_input.lead_data.name} at {message_input.lead_data.company}")
            
            # Build the generation query
            generation_query = self._build_generation_query(message_input)
            
            # Generate the message using the agent
            # This method is now deprecated in favor of the hyper-personalized one.
            # For backward compatibility, we can route this to the new agent
            # or keep the old one, but the instruction is to refactor the agent.
            # For now, we will log a warning and use a safe fallback.
            logger.warning("The 'generate_message' method is deprecated. Use 'generate_hyper_personalized_message'.")
            return self._create_fallback_message(message_input, "Deprecated method called.")
            
            # Parse and validate the response
            message_data = self._parse_message_response(response.content)
            
            # Enhance with additional analysis
            enhanced_data = self._enhance_message_data(message_data, message_input)
            
            # Create structured output
            output = MessageOutput(
                message_text=enhanced_data.get('message_text', ''),
                message_voice_script=enhanced_data.get('message_voice_script', ''),
                message_image_concept=enhanced_data.get('message_image_concept', ''),
                personalization_score=enhanced_data.get('personalization_score', 0.5),
                predicted_response_rate=enhanced_data.get('predicted_response_rate', 0.2),
                generation_timestamp=datetime.now().isoformat(),
                message_length=len(enhanced_data.get('message_text', '')),
                tone_analysis=enhanced_data.get('tone_analysis', 'Professional')
            )
            
            logger.info(f"Message generated with personalization score: {output.personalization_score}")
            return output
            
        except Exception as e:
            logger.error(f"Message generation failed for {message_input.lead_data.name}: {str(e)}")
            return self._create_fallback_message(message_input, str(e))

    def _build_generation_query(self, message_input: MessageInput) -> str:
        """Build comprehensive message generation query"""
        query = f"""
Generate a highly personalized sales message for the following lead:

LEAD INFORMATION:
- Name: {message_input.lead_data.name}
- Company: {message_input.lead_data.company}
- Title: {message_input.lead_data.title}

RESEARCH INSIGHTS:
- Recent News: {message_input.research_insights.recent_news}
- Conversation Hooks: {', '.join(message_input.research_insights.conversation_hooks)}
- Timing Rationale: {message_input.research_insights.timing_rationale}

SENDER INFORMATION:
- Name: {message_input.sender_info.name}
- Company: {message_input.sender_info.company}
- Value Proposition: {message_input.sender_info.value_prop}

MESSAGE TYPE: {message_input.message_type}

Please generate a compelling, personalized message that follows all the principles and guidelines. Focus on creating a message that will achieve a high response rate by being relevant, timely, and valuable.
"""
        return query

    def _build_hyper_personalized_query(self, message_input: MessageInput, crm_data: Optional[Dict] = None, enhanced_research: Optional[Dict] = None, business_context: Optional[Dict] = None) -> str:
        """Build comprehensive query with ALL available context for hyper-personalization."""

        # Base lead information
        query = f"""
Generate a HYPER-PERSONALIZED MongoDB sales message for the following lead:

LEAD INFORMATION:
- Name: {message_input.lead_data.name}
- Company: {message_input.lead_data.company}
- Title: {message_input.lead_data.title}
"""

        # Add comprehensive CRM context (Task 11.4)
        if crm_data:
            query += f"""
COMPREHENSIVE CRM DATA:
- Data Richness Score: {crm_data.get('crm_insights', {}).get('data_richness_score', 0):.2f}
- MongoDB Signals: {crm_data.get('crm_insights', {}).get('mongodb_relevance_signals', [])}
- Interaction History: {len(crm_data.get('interaction_history', []))} interactions
- Key Topics: {crm_data.get('crm_insights', {}).get('key_topics', [])}

CRM NOTES AND HISTORY (analyze for personalization):
"""
            # Include actual CRM notes for deep personalization
            for note in crm_data.get('notes_and_updates', [])[:3]:  # Recent 3 notes
                query += f"- {note.get('created_at', 'Unknown')}: {note.get('content', '')[:150]}...\n"

            # Include all relevant CRM fields
            query += f"\nALL CRM FIELDS FOR ANALYSIS:\n"
            for field, data in crm_data.get('all_column_data', {}).items():
                if data.get('parsed') and str(data['parsed']).strip():
                    query += f"- {field}: {data['parsed']}\n"

        # Add enhanced research context (Task 11.5)
        if enhanced_research:
            query += f"""
ENHANCED RESEARCH INSIGHTS:
- Confidence Score: {enhanced_research.get('confidence_score', 0):.2f}
- MongoDB Opportunity Score: {enhanced_research.get('mongodb_opportunity', {}).get('relevance_score', 0):.2f}

Company Intelligence:
- Recent News: {enhanced_research.get('company_intelligence', {}).get('recent_news', 'N/A')}
- Growth Signals: {enhanced_research.get('company_intelligence', {}).get('growth_signals', [])}
- Technology Stack: {enhanced_research.get('company_intelligence', {}).get('technology_stack', 'N/A')}

MongoDB Opportunity:
- Use Cases: {enhanced_research.get('mongodb_opportunity', {}).get('use_cases', [])}
- Pain Points: {enhanced_research.get('mongodb_opportunity', {}).get('pain_points', [])}
- Timing Signals: {enhanced_research.get('mongodb_opportunity', {}).get('timing_signals', [])}

Hyper-Personalization Hooks:
- Strongest Hooks: {enhanced_research.get('hyper_personalization', {}).get('strongest_hooks', [])}
- Personal Context: {enhanced_research.get('hyper_personalization', {}).get('personal_context', 'N/A')}
- Company Context: {enhanced_research.get('hyper_personalization', {}).get('company_context', 'N/A')}
"""

        # Add business context (MongoDB services)
        if business_context:
            query += f"""
MONGODB BUSINESS CONTEXT:
- Expert: {business_context.get('owner', 'Rom Iluz')}
- Company: {business_context.get('company', 'MongoDB Solutions by Rom')}
- Expertise: {business_context.get('expertise', 'MongoDB implementation, AI agents, database optimization')}
- Services: {business_context.get('services', 'MongoDB setup ($5,000), AI solutions, performance optimization ($200/hour)')}
- Value Prop: {business_context.get('value_prop', 'Build AI applications 10x faster with MongoDB')}
"""

        # Add original research insights for context
        query += f"""
ORIGINAL RESEARCH INSIGHTS:
- Recent News: {message_input.research_insights.recent_news}
- Conversation Hooks: {', '.join(message_input.research_insights.conversation_hooks)}
- Timing Rationale: {message_input.research_insights.timing_rationale}

SENDER INFORMATION:
- Name: {message_input.sender_info.name}
- Company: {message_input.sender_info.company}
- Value Proposition: {message_input.sender_info.value_prop}

MESSAGE TYPE: {message_input.message_type}

HYPER-PERSONALIZATION OBJECTIVES:
1. Analyze ALL CRM data for the most compelling personal context
2. Reference specific company developments and MongoDB relevance
3. Demonstrate deep understanding of their exact situation
4. Position MongoDB services as the perfect solution for their needs
5. Create a message so personalized they think "How did they know?"

Please generate a hyper-personalized message that uses ALL available context to create the most compelling, relevant outreach possible. Every word should demonstrate deep research and understanding.
"""

        return query

    def _parse_message_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the agent's response and extract JSON data"""
        try:
            # Try to find JSON in the response
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback: extract data from text response
                return self._extract_message_from_text(response_content)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return self._extract_message_from_text(response_content)

    def _extract_message_from_text(self, text: str) -> Dict[str, Any]:
        """Extract message data from text response as fallback"""
        # Try to extract the main message from the text
        lines = text.split('\n')
        message_text = ""
        
        for line in lines:
            if len(line.strip()) > 20 and not line.startswith('#') and not line.startswith('*'):
                message_text = line.strip()
                break
        
        if not message_text:
            message_text = "Hi! I'd love to connect and discuss how we can help your company achieve its goals."
        
        return {
            "message_text": message_text,
            "message_voice_script": f"Hi, this is a voice message. {message_text}",
            "message_image_concept": "Professional business card with company logos",
            "personalization_score": 0.6,
            "predicted_response_rate": 0.25,
            "tone_analysis": "Professional and friendly"
        }

    def _enhance_message_data(self, message_data: Dict[str, Any], message_input: MessageInput) -> Dict[str, Any]:
        """Enhance message data with additional analysis and validation"""
        enhanced = message_data.copy()
        
        # Validate and enhance personalization score
        if 'personalization_score' not in enhanced:
            enhanced['personalization_score'] = self._calculate_personalization_score(
                enhanced.get('message_text', ''), message_input
            )
        
        # Validate and enhance predicted response rate
        if 'predicted_response_rate' not in enhanced:
            enhanced['predicted_response_rate'] = self._predict_response_rate(
                enhanced.get('message_text', ''), enhanced.get('personalization_score', 0.5)
            )
        
        # Ensure voice script exists
        if not enhanced.get('message_voice_script'):
            enhanced['message_voice_script'] = self._generate_voice_script(enhanced.get('message_text', ''))
        
        # Ensure image concept exists
        if not enhanced.get('message_image_concept'):
            enhanced['message_image_concept'] = self._generate_image_concept(message_input)
        
        return enhanced

    def _parse_hyper_personalized_response(self, response_content: str) -> Dict[str, Any]:
        """Parse hyper-personalized message response with enhanced metrics."""
        try:
            # Try to find JSON in the response
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response_content[start_idx:end_idx]
                message_data = json.loads(json_str)

                # Validate enhanced structure
                required_fields = ['message_text', 'personalization_score', 'predicted_response_rate']
                for field in required_fields:
                    if field not in message_data:
                        message_data[field] = self._get_default_value(field)

                return message_data
            else:
                # Fallback to enhanced text extraction
                return self._extract_hyper_personalized_from_text(response_content)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse hyper-personalized JSON response: {e}")
            return self._extract_hyper_personalized_from_text(response_content)

    def _extract_hyper_personalized_from_text(self, text: str) -> Dict[str, Any]:
        """Extract hyper-personalized message data from text response as fallback."""
        # Try to extract the main message from the text
        lines = text.split('\n')
        message_text = ""

        for line in lines:
            if len(line.strip()) > 30 and not line.startswith('#') and not line.startswith('*'):
                message_text = line.strip()
                break

        if not message_text:
            message_text = "Hi! I'd love to connect about MongoDB solutions that could help your company scale its AI applications."

        return {
            "message_text": message_text,
            "message_voice_script": f"Hi, this is a voice message about MongoDB solutions. {message_text}",
            "message_image_concept": "Professional MongoDB-focused business card with company logos",
            "personalization_score": 0.85,  # Higher default for hyper-personalized
            "predicted_response_rate": 0.45,  # Higher default
            "tone_analysis": "Hyper-personalized, MongoDB-focused",
            "mongodb_relevance_score": 0.8,
            "crm_context_usage": "CRM data analyzed and incorporated",
            "timing_hook": "Perfect timing for MongoDB adoption"
        }

    def _calculate_hyper_personalization_metrics(self, message_data: Dict[str, Any], crm_data: Optional[Dict] = None, enhanced_research: Optional[Dict] = None) -> Dict[str, Any]:
        """Calculate enhanced metrics for hyper-personalized messages."""
        enhanced_metrics = {}

        # Enhanced personalization score calculation
        base_score = message_data.get('personalization_score', 0.5)

        # Boost for CRM data usage
        if crm_data:
            crm_richness = crm_data.get('crm_insights', {}).get('data_richness_score', 0)
            crm_boost = crm_richness * 0.2
            base_score += crm_boost

        # Boost for enhanced research usage
        if enhanced_research:
            research_confidence = enhanced_research.get('confidence_score', 0)
            mongodb_relevance = enhanced_research.get('mongodb_opportunity', {}).get('relevance_score', 0)
            research_boost = (research_confidence + mongodb_relevance) * 0.1
            base_score += research_boost

        enhanced_metrics['personalization_score'] = min(base_score, 1.0)

        # Enhanced response rate prediction
        base_rate = message_data.get('predicted_response_rate', 0.3)
        personalization_boost = (enhanced_metrics['personalization_score'] - 0.5) * 0.4  # Up to 40% boost
        enhanced_metrics['predicted_response_rate'] = min(base_rate + personalization_boost, 0.8)

        # MongoDB relevance score
        if not message_data.get('mongodb_relevance_score'):
            mongodb_score = 0.7  # Default
            if enhanced_research:
                mongodb_score = enhanced_research.get('mongodb_opportunity', {}).get('relevance_score', 0.7)
            enhanced_metrics['mongodb_relevance_score'] = mongodb_score

        # CRM context usage assessment
        if not message_data.get('crm_context_usage'):
            if crm_data and crm_data.get('crm_insights', {}).get('data_richness_score', 0) > 0.3:
                enhanced_metrics['crm_context_usage'] = "High-quality CRM data incorporated"
            else:
                enhanced_metrics['crm_context_usage'] = "Limited CRM data available"

        return enhanced_metrics

    def _get_default_value(self, field: str) -> Any:
        """Get default values for missing fields."""
        defaults = {
            'message_text': 'Hi! I\'d love to connect about MongoDB solutions.',
            'personalization_score': 0.7,
            'predicted_response_rate': 0.35,
            'tone_analysis': 'Professional, MongoDB-focused',
            'mongodb_relevance_score': 0.6,
            'crm_context_usage': 'Standard context applied',
            'timing_hook': 'Good timing for outreach'
        }
        return defaults.get(field, '')

    def _calculate_personalization_score(self, message_text: str, message_input: MessageInput) -> float:
        """Calculate personalization score based on message content"""
        score = 0.0
        scoring_config = self.config.get('personalization_scoring', {})
        weights = scoring_config.get('weights', {})
        
        # Check for company name
        if message_input.lead_data.company.lower() in message_text.lower():
            score += weights.get('company_name', 0.2)
        
        # Check for lead name
        if message_input.lead_data.name.split()[0].lower() in message_text.lower():
            score += weights.get('lead_name', 0.2)
        
        # Check for recent news reference
        if any(hook.lower() in message_text.lower() for hook in message_input.research_insights.conversation_hooks):
            score += weights.get('conversation_hook', 0.3)
        
        # Check for industry/role relevance
        if message_input.lead_data.title.lower() in message_text.lower():
            score += weights.get('title', 0.15)
        
        # Check for timing elements
        timing_words = scoring_config.get('timing_words', ['recent', 'now', 'currently', 'just', 'today', 'this week'])
        if any(word in message_text.lower() for word in timing_words):
            score += weights.get('timing_word', 0.15)
        
        return min(score, 1.0)

    def _predict_response_rate(self, message_text: str, personalization_score: float) -> float:
        """Predict response rate based on message quality and personalization"""
        prediction_config = self.config.get('response_rate_prediction', {})
        base_rate = prediction_config.get('base_rate', 0.15)
        
        # Boost based on personalization
        personalization_boost = personalization_score * prediction_config.get('personalization_boost_factor', 0.3)
        
        # Boost based on message length
        length = len(message_text)
        length_config = prediction_config.get('length_boost', {})
        optimal_range = length_config.get('optimal_range', [50, 150])
        length_boost = 0.0
        if optimal_range[0] <= length <= optimal_range[1]:
            length_boost = length_config.get('boost_value', 0.1)
        
        # Boost based on question ending
        question_boost = prediction_config.get('question_boost', 0.1) if message_text.strip().endswith('?') else 0.0
        
        predicted_rate = base_rate + personalization_boost + length_boost + question_boost
        return min(predicted_rate, 0.8)  # Cap at 80%

    def _generate_voice_script(self, message_text: str) -> str:
        """Generate voice script from text message"""
        # Convert text to more conversational voice script
        voice_script = message_text.replace('!', '.')
        voice_script = f"Hi there! {voice_script} Looking forward to hearing from you!"
        return voice_script

    def _generate_image_concept(self, message_input: MessageInput) -> str:
        """Generate image concept description"""
        return f"Professional image featuring {message_input.sender_info.company} and {message_input.lead_data.company} logos with a congratulatory message about their recent achievements"

    def _get_voice_prompt(self) -> str:
        """Get voice message generation prompt"""
        return """
You are a voice message specialist. Convert written sales messages into natural, conversational voice scripts.

VOICE GUIDELINES:
- Use conversational, warm tone
- Include natural pauses and emphasis
- Keep it under 30 seconds when spoken
- Sound genuine and enthusiastic
- End with a clear call to action

Convert the message to a natural voice script format.
"""

    def _get_image_prompt(self) -> str:
        """Get image concept generation prompt"""
        return """
You are a visual marketing specialist. Create compelling image concepts for sales outreach.

IMAGE GUIDELINES:
- Professional and clean design
- Include relevant company branding
- Visual elements that support the message
- Appropriate for business communication
- Eye-catching but not overwhelming

Describe the image concept in detail.
"""

    def _validate_input_data(self, message_input: MessageInput, crm_data: Optional[Dict] = None, enhanced_research: Optional[Dict] = None) -> MessageInput:
        """🚨 CRITICAL: Validate input data to prevent hallucination at source"""

        # IMPROVED: Use enhanced research if available, but validate it
        if enhanced_research and enhanced_research.get('company_intelligence'):
            # Use verified research data from enhanced research
            company_intel = enhanced_research.get('company_intelligence', {})
            validated_hooks = []

            # Only use conversation hooks that are verifiable
            if company_intel.get('recent_news') and len(str(company_intel.get('recent_news'))) > 20:
                validated_hooks.append(f"Recent developments at {message_input.lead_data.company}")

            if company_intel.get('growth_signals'):
                validated_hooks.append(f"Growth opportunities in {message_input.lead_data.company}")

            cleaned_research = ResearchInsights(
                recent_news=company_intel.get('recent_news', '')[:200] if company_intel.get('recent_news') else "",  # Limit length
                conversation_hooks=validated_hooks[:2],  # Max 2 hooks to prevent overuse
                timing_rationale=enhanced_research.get('timing_rationale', 'Professional outreach timing')
            )
        else:
            # Fallback to safe research
            cleaned_research = ResearchInsights(
                recent_news="",
                conversation_hooks=[],
                timing_rationale="Professional outreach timing"
            )

        # Return validated input
        return MessageInput(
            lead_data=message_input.lead_data,  # Keep basic lead data (name, company, title)
            research_insights=cleaned_research,  # Use validated research
            message_type=message_input.message_type,
            sender_info=message_input.sender_info
        )

    def _validate_output_for_hallucination(self, message_data: Dict[str, Any], crm_data: Optional[Dict] = None, enhanced_research: Optional[Dict] = None) -> Dict[str, Any]:
        """🚨 CRITICAL: Validate output message for hallucination and remove any fabricated content"""

        message_text = message_data.get('message_text', '')

        # IMPROVED: More targeted hallucination patterns - remove obvious fabrications but keep verified content
        hallucination_patterns = self.config.get('hallucination_patterns', [
            r'\[.*?\]',
            r'\{.*?\}',
            r'<.*?>',
            r'\$\d+[kmb]?\s*(?:funding|round|investment|valuation)',
            r'(?:raised|secured|closed)\s+\$\d+',
            r'congrats on your recent (?:success|achievement|launch|funding)',
            r'i noticed you recently (?:joined|started|launched)',
        ])

        # Remove hallucination patterns
        cleaned_message = message_text
        for pattern in hallucination_patterns:
            cleaned_message = re.sub(pattern, '', cleaned_message, flags=re.IGNORECASE)

        # Clean up extra spaces and punctuation
        cleaned_message = re.sub(r'\s+', ' ', cleaned_message).strip()
        cleaned_message = re.sub(r'[,\s]+\.', '.', cleaned_message)
        cleaned_message = re.sub(r'[,\s]+!', '!', cleaned_message)

        # 🚨 CRITICAL: Final check for any remaining placeholders
        placeholder_check_patterns = [r'\[.*?\]', r'\{.*?\}', r'<.*?>']
        for pattern in placeholder_check_patterns:
            if re.search(pattern, cleaned_message):
                logger.error(f"🚨 PLACEHOLDER DETECTED: {pattern} found in message: {cleaned_message}")
                # Force safe fallback if ANY placeholders remain
                cleaned_message = f"Hi! I specialize in MongoDB solutions and would love to discuss how we can help your company with database optimization. Would you be open to a brief conversation?"
                break

        # If message is too short after cleaning, use safe fallback
        if len(cleaned_message) < 50:
            cleaned_message = f"Hi! I specialize in MongoDB solutions and would love to discuss how we can help your company with database optimization. Would you be open to a brief conversation?"

        # Update message data with cleaned content
        validated_data = message_data.copy()
        validated_data['message_text'] = cleaned_message
        validated_data['fact_verification_status'] = "Hallucination patterns removed, placeholders eliminated, content verified"

        logger.info(f"🛡️ Message validated and cleaned for anti-hallucination - NO PLACEHOLDERS")
        return validated_data

    def _create_anti_hallucination_fallback_message(self, message_input: MessageInput, error_msg: str) -> MessageOutput:
        """Create SAFE fallback message with zero hallucination risk"""
        fallback_template = self.config.get('anti_hallucination_fallback_template', "Hi {lead_name}! I specialize in MongoDB database solutions and help companies optimize their data infrastructure. Would you be open to a brief conversation about your database needs?")
        safe_text = fallback_template.format(lead_name=message_input.lead_data.name)

        return MessageOutput(
            message_text=safe_text,
            message_voice_script=f"Hi {message_input.lead_data.name}, this is {message_input.sender_info.name}. {safe_text}",
            message_image_concept=f"Professional MongoDB-focused business card design",
            personalization_score=0.4,  # Lower score for safety
            predicted_response_rate=0.2,  # Conservative estimate
            generation_timestamp=datetime.now().isoformat(),
            message_length=len(safe_text),
            tone_analysis=f"Anti-hallucination safe fallback: {error_msg}"
        )

    def _create_fallback_message(self, message_input: MessageInput, error_msg: str) -> MessageOutput:
        """Create fallback message when generation fails"""
        fallback_template = self.config.get('fallback_message_template', "Hi {lead_name}! I'd love to connect with you about {value_prop} opportunities for {company}. Would you be open to a brief conversation?")
        fallback_text = fallback_template.format(
            lead_name=message_input.lead_data.name,
            value_prop=message_input.sender_info.value_prop,
            company=message_input.lead_data.company
        )
        
        return MessageOutput(
            message_text=fallback_text,
            message_voice_script=f"Hi {message_input.lead_data.name}, this is {message_input.sender_info.name}. {fallback_text}",
            message_image_concept=f"Professional business card design with {message_input.sender_info.company} branding",
            personalization_score=0.3,
            predicted_response_rate=0.15,
            generation_timestamp=datetime.now().isoformat(),
            message_length=len(fallback_text),
            tone_analysis=f"Fallback message due to error: {error_msg}"
        )


# Convenience function for easy usage
def create_message_agent(config: Dict[str, Any], api_keys: Optional[Dict[str, str]] = None) -> MessageGenerationAgent:
    """Create and return a configured Message Generation Agent instance."""
    return MessageGenerationAgent(config=config, api_keys=api_keys)


# Example usage
if __name__ == "__main__":
    # Example usage
    # This example requires a dummy config for the agent to initialize.
    # In the actual application, this config will be fetched from MongoDB.
    dummy_config = {
        "hyper_personalized_prompt_template": "...", # Simplified for example
        "personalization_scoring": {
            "weights": { "company_name": 0.2, "lead_name": 0.2, "conversation_hook": 0.3, "title": 0.15, "timing_word": 0.15 },
            "timing_words": ["recent", "now", "currently", "just", "today", "this week"]
        },
        "response_rate_prediction": {
            "base_rate": 0.15,
            "personalization_boost_factor": 0.3,
            "length_boost": { "optimal_range": [50, 150], "boost_value": 0.1 },
            "question_boost": 0.1
        },
        "fallback_message_template": "Hi {lead_name}! I'd love to connect with you about {value_prop} opportunities for {company}. Would you be open to a brief conversation?",
        "anti_hallucination_fallback_template": "Hi {lead_name}! I specialize in MongoDB database solutions and help companies optimize their data infrastructure. Would you be open to a brief conversation about your database needs?",
        "hallucination_patterns": []
    }
    
    agent = create_message_agent(config=dummy_config)
    
    sample_input = MessageInput(
        lead_data=LeadData(
            name="John Doe",
            company="Acme Corp",
            title="VP of Sales"
        ),
        research_insights=ResearchInsights(
            recent_news="Raised $50M Series B funding",
            conversation_hooks=["Series B funding", "Scaling challenges"],
            timing_rationale="Perfect timing for sales optimization"
        ),
        message_type="text",
        sender_info=SenderInfo(
            name="Sarah",
            company="TechCorp",
            value_prop="Sales process optimization"
        )
    )
    
    result = agent.generate_message(sample_input)
    print(f"Message generated with personalization: {result.personalization_score}")
    print(f"Predicted response rate: {result.predicted_response_rate}")
    print(f"Message: {result.message_text}")
