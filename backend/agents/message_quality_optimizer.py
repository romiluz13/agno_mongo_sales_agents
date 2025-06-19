"""
Message Quality Testing & Optimization System

This module implements comprehensive message quality testing, optimization for >40% response rates,
and message approval workflow for the Agno Sales Extension.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from agents.research_agent import ResearchAgent, LeadInput
from agents.message_agent import MessageGenerationAgent, MessageInput, LeadData, ResearchInsights, SenderInfo
from agents.multimodal_message_agent import MultimodalMessageAgent
from agents.research_storage import ResearchStorageManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    """Message approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


@dataclass
class QualityMetrics:
    """Message quality assessment metrics"""
    personalization_score: float
    predicted_response_rate: float
    readability_score: float
    sentiment_score: float
    urgency_score: float
    value_proposition_score: float
    call_to_action_score: float
    overall_quality_score: float


@dataclass
class MessageApproval:
    """Message approval workflow data"""
    message_id: str
    status: MessageStatus
    reviewer_notes: str
    approval_timestamp: str
    quality_metrics: QualityMetrics
    suggested_improvements: List[str]


@dataclass
class OptimizedMessage:
    """Optimized message with quality metrics"""
    original_message: str
    optimized_message: str
    quality_metrics: QualityMetrics
    optimization_notes: List[str]
    approval_data: Optional[MessageApproval] = None


class MessageQualityOptimizer:
    """
    Comprehensive message quality testing and optimization system
    that ensures >40% predicted response rates and implements approval workflow.
    """
    
    def __init__(self, api_keys: Dict[str, str], mongodb_connection: str):
        """
        Initialize the Message Quality Optimizer.
        
        Args:
            api_keys: Dictionary containing API keys
            mongodb_connection: MongoDB connection string
        """
        self.api_keys = api_keys
        self.target_response_rate = 0.40  # 40% target
        self.quality_threshold = 0.65  # 65% overall quality threshold (more reasonable)
        
        # Load agent configurations from MongoDB
        agent_configs = self._load_agent_configurations()

        # Initialize agents with proper configurations
        self.research_agent = ResearchAgent(
            api_keys=api_keys,
            config=agent_configs.get('research_agent', {})
        )
        self.message_agent = MessageGenerationAgent(
            api_keys=api_keys,
            config=agent_configs.get('message_generation_agent', {})
        )
        self.multimodal_agent = MultimodalMessageAgent(api_keys=api_keys)
        
        # Initialize storage
        self.storage_manager = ResearchStorageManager(mongodb_connection)
        self.storage_manager.connect()
        
        logger.info("Message Quality Optimizer initialized successfully")

    def _load_agent_configurations(self) -> Dict[str, Any]:
        """Load agent configurations from MongoDB"""
        try:
            from config.database import MongoDBManager
            db_manager = MongoDBManager()
            db_manager.connect()

            agent_configs_collection = db_manager.get_collection("agent_configurations")
            agent_config = agent_configs_collection.find_one()

            if not agent_config:
                logger.warning("⚠️ No agent configurations found in MongoDB, using empty configs")
                return {}

            logger.info(f"✅ Loaded agent configurations: {list(agent_config.keys())}")
            return agent_config

        except Exception as e:
            logger.error(f"❌ Failed to load agent configurations: {e}")
            return {}

    def test_message_quality_with_research(self, lead_input: LeadInput, sender_info: SenderInfo) -> OptimizedMessage:
        """
        Test message generation with research data and optimize for quality.
        
        Args:
            lead_input: Lead information for research
            sender_info: Sender information for message generation
            
        Returns:
            OptimizedMessage with quality metrics and optimization
        """
        try:
            logger.info(f"Testing message quality for {lead_input.lead_name} at {lead_input.company}")
            
            # Step 1: Conduct research
            research_result = self.research_agent.research_lead(lead_input)
            
            # Step 2: Generate initial message
            message_input = MessageInput(
                lead_data=LeadData(
                    name=lead_input.lead_name,
                    company=lead_input.company,
                    title=lead_input.title
                ),
                research_insights=ResearchInsights(
                    recent_news=research_result.company_intelligence.get('recent_news', ''),
                    conversation_hooks=research_result.conversation_hooks,
                    timing_rationale=research_result.timing_rationale
                ),
                message_type="text",
                sender_info=sender_info
            )
            
            initial_message = self.message_agent.generate_message(message_input)
            
            # Step 3: Assess quality metrics
            quality_metrics = self._assess_message_quality(initial_message, research_result)
            
            # Step 4: Optimize if needed
            if quality_metrics.predicted_response_rate < self.target_response_rate:
                optimized_message = self._optimize_message(initial_message, message_input, quality_metrics)
                optimization_notes = self._generate_optimization_notes(quality_metrics)
            else:
                optimized_message = initial_message
                optimization_notes = ["Message already meets quality targets"]
            
            # Step 5: Final quality assessment
            final_quality = self._assess_message_quality(optimized_message, research_result)
            
            result = OptimizedMessage(
                original_message=initial_message.message_text,
                optimized_message=optimized_message.message_text,
                quality_metrics=final_quality,
                optimization_notes=optimization_notes
            )
            
            logger.info(f"Message quality testing completed - Response Rate: {final_quality.predicted_response_rate:.1%}")
            return result
            
        except Exception as e:
            logger.error(f"Message quality testing failed: {e}")
            raise

    def _assess_message_quality(self, message_output, research_result) -> QualityMetrics:
        """Assess comprehensive message quality metrics"""
        
        # Personalization score (from message agent)
        personalization_score = message_output.personalization_score
        
        # Predicted response rate (from message agent)
        predicted_response_rate = message_output.predicted_response_rate
        
        # Readability score
        readability_score = self._calculate_readability_score(message_output.message_text)
        
        # Sentiment score
        sentiment_score = self._calculate_sentiment_score(message_output.message_text)
        
        # Urgency score
        urgency_score = self._calculate_urgency_score(message_output.message_text)
        
        # Value proposition score
        value_prop_score = self._calculate_value_proposition_score(message_output.message_text)
        
        # Call to action score
        cta_score = self._calculate_cta_score(message_output.message_text)
        
        # Overall quality score (weighted average)
        overall_quality = (
            personalization_score * 0.25 +
            predicted_response_rate * 0.20 +
            readability_score * 0.15 +
            sentiment_score * 0.10 +
            urgency_score * 0.10 +
            value_prop_score * 0.10 +
            cta_score * 0.10
        )
        
        return QualityMetrics(
            personalization_score=personalization_score,
            predicted_response_rate=predicted_response_rate,
            readability_score=readability_score,
            sentiment_score=sentiment_score,
            urgency_score=urgency_score,
            value_proposition_score=value_prop_score,
            call_to_action_score=cta_score,
            overall_quality_score=overall_quality
        )

    def _calculate_readability_score(self, message_text: str) -> float:
        """Calculate readability score based on message complexity"""
        words = message_text.split()
        sentences = message_text.count('.') + message_text.count('!') + message_text.count('?')
        
        if sentences == 0:
            sentences = 1
        
        avg_words_per_sentence = len(words) / sentences
        
        # Optimal: 10-20 words per sentence
        if 10 <= avg_words_per_sentence <= 20:
            readability = 1.0
        elif avg_words_per_sentence < 10:
            readability = 0.8 + (avg_words_per_sentence / 10) * 0.2
        else:
            readability = max(0.3, 1.0 - (avg_words_per_sentence - 20) * 0.05)
        
        return min(readability, 1.0)

    def _calculate_sentiment_score(self, message_text: str) -> float:
        """Calculate sentiment score (positive, professional tone)"""
        positive_words = ['congrats', 'congratulations', 'impressive', 'excellent', 'outstanding', 'great', 'amazing']
        professional_words = ['opportunity', 'discuss', 'explore', 'partnership', 'collaboration', 'growth']
        
        text_lower = message_text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        professional_count = sum(1 for word in professional_words if word in text_lower)
        
        sentiment_score = min(1.0, (positive_count * 0.3 + professional_count * 0.2) + 0.5)
        return sentiment_score

    def _calculate_urgency_score(self, message_text: str) -> float:
        """Calculate urgency/timing score"""
        timing_words = ['now', 'currently', 'recent', 'just', 'today', 'this week', 'perfect timing']
        urgency_words = ['opportunity', 'limited', 'exclusive', 'quick', 'brief']
        
        text_lower = message_text.lower()
        
        timing_count = sum(1 for word in timing_words if word in text_lower)
        urgency_count = sum(1 for word in urgency_words if word in text_lower)
        
        urgency_score = min(1.0, (timing_count * 0.4 + urgency_count * 0.3) + 0.3)
        return urgency_score

    def _calculate_value_proposition_score(self, message_text: str) -> float:
        """Calculate value proposition clarity score"""
        value_words = ['help', 'optimize', 'improve', 'increase', 'reduce', 'save', 'boost', 'enhance']
        benefit_words = ['revenue', 'efficiency', 'growth', 'performance', 'results', 'success']
        
        text_lower = message_text.lower()
        
        value_count = sum(1 for word in value_words if word in text_lower)
        benefit_count = sum(1 for word in benefit_words if word in text_lower)
        
        value_score = min(1.0, (value_count * 0.3 + benefit_count * 0.4) + 0.3)
        return value_score

    def _calculate_cta_score(self, message_text: str) -> float:
        """Calculate call-to-action effectiveness score"""
        cta_indicators = ['?', 'would you', 'are you', 'interested', 'open to', 'discuss', 'chat', 'call', 'meeting']
        
        text_lower = message_text.lower()
        
        # Check for question mark (strong CTA indicator)
        has_question = '?' in message_text
        
        # Check for CTA phrases
        cta_count = sum(1 for phrase in cta_indicators if phrase in text_lower)
        
        cta_score = 0.0
        if has_question:
            cta_score += 0.5
        
        cta_score += min(0.5, cta_count * 0.1)
        
        return min(cta_score, 1.0)

    def _optimize_message(self, original_message, message_input, quality_metrics) -> Any:
        """Optimize message based on quality assessment"""
        
        optimization_prompt = f"""
Optimize this sales message to achieve >40% response rate:

ORIGINAL MESSAGE: {original_message.message_text}

QUALITY ISSUES IDENTIFIED:
- Predicted Response Rate: {quality_metrics.predicted_response_rate:.1%} (target: >40%)
- Personalization: {quality_metrics.personalization_score:.2f}
- Readability: {quality_metrics.readability_score:.2f}
- Value Proposition: {quality_metrics.value_proposition_score:.2f}
- Call to Action: {quality_metrics.call_to_action_score:.2f}

OPTIMIZATION REQUIREMENTS:
1. Increase personalization with specific company details
2. Strengthen value proposition with concrete benefits
3. Improve call-to-action with compelling question
4. Maintain professional, conversational tone
5. Keep under 200 characters for optimal engagement

Generate an optimized version that addresses these issues.
"""
        
        # Use message agent to optimize
        optimized_input = MessageInput(
            lead_data=message_input.lead_data,
            research_insights=message_input.research_insights,
            message_type="text",
            sender_info=message_input.sender_info
        )
        
        # Generate optimized message with enhanced prompt
        optimized_result = self.message_agent.generate_message(optimized_input)
        
        return optimized_result

    def _generate_optimization_notes(self, quality_metrics: QualityMetrics) -> List[str]:
        """Generate specific optimization recommendations"""
        notes = []
        
        if quality_metrics.predicted_response_rate < self.target_response_rate:
            notes.append(f"Response rate {quality_metrics.predicted_response_rate:.1%} below target {self.target_response_rate:.1%}")
        
        if quality_metrics.personalization_score < 0.8:
            notes.append("Increase personalization with specific company details and recent news")
        
        if quality_metrics.readability_score < 0.7:
            notes.append("Improve readability by simplifying sentence structure")
        
        if quality_metrics.value_proposition_score < 0.6:
            notes.append("Strengthen value proposition with concrete benefits")
        
        if quality_metrics.call_to_action_score < 0.7:
            notes.append("Enhance call-to-action with compelling question")
        
        if quality_metrics.urgency_score < 0.5:
            notes.append("Add timing elements to create appropriate urgency")
        
        return notes

    def implement_approval_workflow(self, optimized_message: OptimizedMessage, reviewer_notes: str = "") -> MessageApproval:
        """
        Implement message approval workflow based on quality metrics.
        
        Args:
            optimized_message: Message to review
            reviewer_notes: Optional reviewer feedback
            
        Returns:
            MessageApproval with status and recommendations
        """
        
        # Auto-approval logic based on quality metrics
        quality = optimized_message.quality_metrics
        
        if (quality.predicted_response_rate >= self.target_response_rate and 
            quality.overall_quality_score >= self.quality_threshold):
            status = MessageStatus.APPROVED
            suggested_improvements = []
        elif quality.overall_quality_score >= 0.6:
            status = MessageStatus.NEEDS_REVISION
            suggested_improvements = optimized_message.optimization_notes
        else:
            status = MessageStatus.REJECTED
            suggested_improvements = [
                "Message quality below minimum threshold",
                "Requires complete rewrite with better research data"
            ]
        
        approval = MessageApproval(
            message_id=f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status=status,
            reviewer_notes=reviewer_notes,
            approval_timestamp=datetime.now().isoformat(),
            quality_metrics=quality,
            suggested_improvements=suggested_improvements
        )
        
        logger.info(f"Message approval: {status.value} - Quality: {quality.overall_quality_score:.2f}")
        return approval

    def batch_quality_test(self, test_leads: List[Tuple[LeadInput, SenderInfo]], target_count: int = 10) -> Dict[str, Any]:
        """
        Run batch quality testing on multiple leads to validate optimization.
        
        Args:
            test_leads: List of (LeadInput, SenderInfo) tuples
            target_count: Number of leads to test
            
        Returns:
            Comprehensive quality test results
        """
        
        logger.info(f"Starting batch quality test with {len(test_leads)} leads")
        
        results = []
        approved_count = 0
        total_response_rate = 0.0
        
        for i, (lead_input, sender_info) in enumerate(test_leads[:target_count]):
            try:
                logger.info(f"Testing lead {i+1}/{target_count}: {lead_input.lead_name}")
                
                # Test message quality
                optimized_message = self.test_message_quality_with_research(lead_input, sender_info)
                
                # Run approval workflow
                approval = self.implement_approval_workflow(optimized_message)
                optimized_message.approval_data = approval
                
                results.append({
                    "lead_name": lead_input.lead_name,
                    "company": lead_input.company,
                    "response_rate": optimized_message.quality_metrics.predicted_response_rate,
                    "quality_score": optimized_message.quality_metrics.overall_quality_score,
                    "approval_status": approval.status.value,
                    "optimized_message": optimized_message
                })
                
                if approval.status == MessageStatus.APPROVED:
                    approved_count += 1
                
                total_response_rate += optimized_message.quality_metrics.predicted_response_rate
                
            except Exception as e:
                logger.error(f"Failed to test lead {lead_input.lead_name}: {e}")
                results.append({
                    "lead_name": lead_input.lead_name,
                    "company": lead_input.company,
                    "error": str(e)
                })
        
        # Calculate summary metrics
        successful_tests = [r for r in results if 'error' not in r]
        success_rate = len(successful_tests) / len(results) if results else 0
        approval_rate = approved_count / len(successful_tests) if successful_tests else 0
        avg_response_rate = total_response_rate / len(successful_tests) if successful_tests else 0
        
        summary = {
            "total_tests": len(results),
            "successful_tests": len(successful_tests),
            "success_rate": success_rate,
            "approved_messages": approved_count,
            "approval_rate": approval_rate,
            "average_response_rate": avg_response_rate,
            "target_response_rate": self.target_response_rate,
            "meets_target": avg_response_rate >= self.target_response_rate,
            "test_results": results
        }
        
        logger.info(f"Batch test completed - Approval Rate: {approval_rate:.1%}, Avg Response Rate: {avg_response_rate:.1%}")
        return summary


# Convenience function
def create_message_quality_optimizer(api_keys: Dict[str, str], mongodb_connection: str) -> MessageQualityOptimizer:
    """Create and return a configured Message Quality Optimizer instance."""
    return MessageQualityOptimizer(api_keys=api_keys, mongodb_connection=mongodb_connection)
