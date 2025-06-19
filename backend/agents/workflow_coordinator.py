"""
Workflow Coordinator for Agno Sales Extension

This module implements the workflow coordinator that orchestrates the complete
lead processing pipeline using Agno Team patterns. Coordinates Research Agent,
Message Agent, and Outreach Agent in a systematic workflow.

Based on cookbook/teams patterns and docs/03-AGENT-SPECIFICATIONS.md.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from agno.agent import Agent
from agno.team import Team
from agno.models.google import Gemini
from agno.storage.mongodb import MongoDbStorage

# Import our agents
from agents.research_agent import ResearchAgent, LeadInput, ResearchOutput
from agents.message_agent import MessageGenerationAgent, MessageInput, LeadData, ResearchInsights, SenderInfo, MessageOutput
from agents.outreach_agent import OutreachAgent, OutreachRequest, OutreachResult, MessageType
from agents.research_storage import ResearchDataProcessor, ResearchStorageManager
from config.database import MongoDBManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RESEARCH_IN_PROGRESS = "research_in_progress"
    RESEARCH_COMPLETE = "research_complete"
    MESSAGE_GENERATION_IN_PROGRESS = "message_generation_in_progress"
    MESSAGE_GENERATION_COMPLETE = "message_generation_complete"
    OUTREACH_IN_PROGRESS = "outreach_in_progress"
    OUTREACH_COMPLETE = "outreach_complete"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowInput:
    """Input for the complete workflow"""
    lead_id: str
    lead_name: str
    company: str
    title: str
    industry: str
    company_size: str
    phone_number: str
    message_type: str
    sender_name: str
    sender_company: str
    value_proposition: str
    priority: int = 1


@dataclass
class WorkflowProgress:
    """Progress tracking for workflow execution"""
    workflow_id: str
    status: WorkflowStatus
    current_step: str
    progress_percentage: float
    research_output: Optional[ResearchOutput] = None
    message_output: Optional[MessageOutput] = None
    outreach_result: Optional[OutreachResult] = None
    error_message: Optional[str] = None
    started_at: str = ""
    completed_at: Optional[str] = None
    total_steps: int = 3


@dataclass
class WorkflowResult:
    """Final result of workflow execution"""
    workflow_id: str
    success: bool
    lead_id: str
    final_status: WorkflowStatus
    research_confidence: float
    message_personalization_score: float
    predicted_response_rate: float
    outreach_status: str
    whatsapp_message_id: Optional[str]
    execution_time_seconds: float
    error_details: Optional[str] = None


class SalesAgentTeam:
    """
    Sales Agent Team using Agno Team patterns for coordinated lead processing.
    Implements the complete workflow: Research → Message Generation → Outreach
    """
    
    def __init__(self, api_keys: Dict[str, str], mongodb_connection: str):
        """
        Initialize the Sales Agent Team.

        Args:
            api_keys: Dictionary containing all API keys
            mongodb_connection: MongoDB connection string
        """
        self.api_keys = api_keys
        self.mongodb_connection = mongodb_connection

        # Load agent configurations from MongoDB
        agent_configs = self._load_agent_configurations()

        # Initialize individual agents with proper configurations
        self.research_agent = ResearchAgent(
            api_keys=api_keys,
            config=agent_configs.get('research_agent', {})
        )
        self.message_agent = MessageGenerationAgent(
            api_keys=api_keys,
            config=agent_configs.get('message_generation_agent', {})
        )
        self.outreach_agent = OutreachAgent(api_keys, mongodb_connection)

        # Initialize database manager for progress tracking
        self.db_manager = MongoDBManager()
        self.db_manager.connect()

        # Initialize research storage for MongoDB single source of truth
        self.research_storage = ResearchStorageManager(mongodb_connection)
        self.research_storage.connect()
        self.research_processor = ResearchDataProcessor()
        
        # Create the coordinated team
        self.team = Team(
            name="Sales Agent Team",
            mode="coordinate",
            model=Gemini(id="gemini-2.0-flash-exp"),
            members=[
                self._create_research_wrapper(),
                self._create_message_wrapper(),
                self._create_outreach_wrapper()
            ],
            instructions=[
                "You are the coordinator of a high-performance sales agent team.",
                "Process leads systematically through: Research → Message Generation → Outreach",
                "Ensure high-quality output at each stage before proceeding to the next",
                "Handle errors gracefully and provide detailed progress updates",
                "Only proceed to the next step if the previous step was successful",
                "Maintain detailed tracking of progress and results"
            ],
            success_criteria="Lead successfully processed through complete workflow with high-quality research, personalized message, and successful outreach delivery",
            show_tool_calls=True,
            show_members_responses=True,
            markdown=True,
            enable_agentic_context=True
        )
        
        logger.info("Sales Agent Team initialized successfully")

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

    def _create_research_wrapper(self) -> Agent:
        """Create wrapper agent for research functionality"""
        return Agent(
            name="Research Coordinator",
            role="Conduct comprehensive lead and company research",
            model=Gemini(id="gemini-2.0-flash-exp"),
            instructions=[
                "You coordinate research activities for sales leads",
                "Gather comprehensive intelligence about leads and companies",
                "Provide actionable insights for personalized outreach",
                "Ensure research confidence score is above 0.7 before proceeding"
            ],
            markdown=True
        )
    
    def _create_message_wrapper(self) -> Agent:
        """Create wrapper agent for message generation functionality"""
        return Agent(
            name="Message Coordinator",
            role="Generate highly personalized sales messages",
            model=Gemini(id="gemini-2.0-flash-exp"),
            instructions=[
                "You coordinate message generation for sales outreach",
                "Create compelling, personalized messages based on research insights",
                "Ensure personalization score is above 0.8 and predicted response rate above 0.4",
                "Generate messages optimized for high response rates"
            ],
            markdown=True
        )
    
    def _create_outreach_wrapper(self) -> Agent:
        """Create wrapper agent for outreach functionality"""
        return Agent(
            name="Outreach Coordinator", 
            role="Execute outreach via WhatsApp and track delivery",
            model=Gemini(id="gemini-2.0-flash-exp"),
            instructions=[
                "You coordinate outreach execution and delivery tracking",
                "Send messages via WhatsApp and monitor delivery status",
                "Update Monday.com with progress and results",
                "Handle delivery failures and retry logic"
            ],
            markdown=True
        )


class WorkflowCoordinator:
    """
    Workflow Coordinator that manages the complete lead processing pipeline
    with progress tracking and error handling.
    """
    
    def __init__(self, api_keys: Dict[str, str], mongodb_connection: str):
        """
        Initialize the Workflow Coordinator.
        
        Args:
            api_keys: Dictionary containing all API keys
            mongodb_connection: MongoDB connection string
        """
        self.api_keys = api_keys
        self.mongodb_connection = mongodb_connection
        
        # Initialize the sales agent team
        self.sales_team = SalesAgentTeam(api_keys, mongodb_connection)

        # Initialize database for progress tracking
        self.db_manager = MongoDBManager()
        self.db_manager.connect()

        # Initialize research storage for MongoDB single source of truth
        self.research_storage = ResearchStorageManager(mongodb_connection)
        self.research_storage.connect()
        self.research_processor = ResearchDataProcessor()
        
        logger.info("Workflow Coordinator initialized successfully")
    
    def execute_lead_processing_workflow(
        self, 
        workflow_input: WorkflowInput,
        progress_callback: Optional[Callable[[WorkflowProgress], None]] = None
    ) -> WorkflowResult:
        """
        Execute the complete lead processing workflow with progress tracking.
        
        Args:
            workflow_input: Input data for the workflow
            progress_callback: Optional callback for progress updates
            
        Returns:
            WorkflowResult with execution details
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{workflow_input.lead_id}"
        start_time = datetime.now(timezone.utc)
        
        # Initialize progress tracking
        progress = WorkflowProgress(
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            current_step="Initializing workflow",
            progress_percentage=0.0,
            started_at=start_time.isoformat()
        )
        
        try:
            logger.info(f"Starting workflow {workflow_id} for lead {workflow_input.lead_name}")
            
            # Step 1: Research Phase
            progress.status = WorkflowStatus.RESEARCH_IN_PROGRESS
            progress.current_step = "Conducting research"
            progress.progress_percentage = 10.0
            self._update_progress(progress, progress_callback)
            
            research_result = self._execute_research_phase(workflow_input)
            
            progress.research_output = research_result
            progress.status = WorkflowStatus.RESEARCH_COMPLETE
            progress.current_step = "Research completed"
            progress.progress_percentage = 33.0
            self._update_progress(progress, progress_callback)
            
            # Step 2: Message Generation Phase
            progress.status = WorkflowStatus.MESSAGE_GENERATION_IN_PROGRESS
            progress.current_step = "Generating personalized message"
            progress.progress_percentage = 40.0
            self._update_progress(progress, progress_callback)
            
            message_result = self._execute_message_generation_phase(workflow_input, research_result)
            
            progress.message_output = message_result
            progress.status = WorkflowStatus.MESSAGE_GENERATION_COMPLETE
            progress.current_step = "Message generation completed"
            progress.progress_percentage = 66.0
            self._update_progress(progress, progress_callback)
            
            # Step 3: Outreach Phase
            progress.status = WorkflowStatus.OUTREACH_IN_PROGRESS
            progress.current_step = "Executing outreach"
            progress.progress_percentage = 75.0
            self._update_progress(progress, progress_callback)
            
            outreach_result = self._execute_outreach_phase(workflow_input, message_result)
            
            progress.outreach_result = outreach_result
            progress.status = WorkflowStatus.OUTREACH_COMPLETE
            progress.current_step = "Outreach completed"
            progress.progress_percentage = 90.0
            self._update_progress(progress, progress_callback)
            
            # Finalize workflow
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()
            
            progress.status = WorkflowStatus.COMPLETED
            progress.current_step = "Workflow completed successfully"
            progress.progress_percentage = 100.0
            progress.completed_at = end_time.isoformat()
            self._update_progress(progress, progress_callback)
            
            # Create final result
            result = WorkflowResult(
                workflow_id=workflow_id,
                success=True,
                lead_id=workflow_input.lead_id,
                final_status=WorkflowStatus.COMPLETED,
                research_confidence=research_result.confidence_score,
                message_personalization_score=message_result.personalization_score,
                predicted_response_rate=message_result.predicted_response_rate,
                outreach_status=outreach_result.status.value,
                whatsapp_message_id=outreach_result.whatsapp_message_id,
                execution_time_seconds=execution_time
            )
            
            logger.info(f"Workflow {workflow_id} completed successfully in {execution_time:.2f} seconds")
            return result
            
        except Exception as e:
            # Handle workflow failure
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()
            
            error_msg = str(e)
            logger.error(f"Workflow {workflow_id} failed: {error_msg}")
            
            progress.status = WorkflowStatus.FAILED
            progress.current_step = f"Workflow failed: {error_msg}"
            progress.error_message = error_msg
            progress.completed_at = end_time.isoformat()
            self._update_progress(progress, progress_callback)
            
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                lead_id=workflow_input.lead_id,
                final_status=WorkflowStatus.FAILED,
                research_confidence=0.0,
                message_personalization_score=0.0,
                predicted_response_rate=0.0,
                outreach_status="failed",
                whatsapp_message_id=None,
                execution_time_seconds=execution_time,
                error_details=error_msg
            )

    def _execute_research_phase(self, workflow_input: WorkflowInput) -> ResearchOutput:
        """Execute the research phase of the workflow with MongoDB storage and CRM context"""
        logger.info(f"Executing research phase for {workflow_input.lead_name}")

        # Create lead input for research
        lead_input = LeadInput(
            lead_name=workflow_input.lead_name,
            company=workflow_input.company,
            title=workflow_input.title,
            industry=workflow_input.industry,
            company_size=workflow_input.company_size
        )

        # CRITICAL FIX: Get comprehensive CRM data for context-aware research
        comprehensive_crm_data = self._get_comprehensive_contact_data(workflow_input.lead_id)

        # Get business context for enhanced research
        business_context = {
            'owner': 'Rom Iluz',
            'company': 'MongoDB Solutions by Rom',
            'expertise': 'MongoDB Atlas Vector Search implementation, conversation intelligence architectures, real-time AI data pipelines',
            'services': 'MongoDB Atlas Vector Search setup ($15,000), AI conversation intelligence platforms ($500/hour), real-time analytics pipelines',
            'value_prop': 'Transform conversation data into AI-powered insights with MongoDB\'s purpose-built vector search and real-time aggregation capabilities'
        }

        # Execute ENHANCED research with CRM context
        if comprehensive_crm_data and comprehensive_crm_data.get('comprehensive_data'):
            logger.info(f"🎯 Using ENHANCED research with comprehensive CRM data for {workflow_input.lead_name}")
            research_result = self.sales_team.research_agent.research_lead_enhanced(
                lead_input=lead_input,
                crm_data=comprehensive_crm_data.get('comprehensive_data'),
                business_context=business_context
            )
        else:
            logger.warning(f"⚠️ No comprehensive CRM data found, using basic research for {workflow_input.lead_name}")
            research_result = self.sales_team.research_agent.research_lead(lead_input)

        # CRITICAL: Store research data in MongoDB for single source of truth
        try:
            logger.info(f"Storing research data in MongoDB for {workflow_input.lead_name}")

            # Process research data for storage
            processed_record = self.research_processor.process_research_data(
                research_result.__dict__,
                {
                    'lead_name': workflow_input.lead_name,
                    'company': workflow_input.company,
                    'title': workflow_input.title,
                    'industry': workflow_input.industry,
                    'company_size': workflow_input.company_size,
                    'lead_id': workflow_input.lead_id
                }
            )

            # Store in MongoDB
            storage_success = self.research_storage.store_research_result(processed_record)

            if storage_success:
                logger.info(f"✅ Research data stored in MongoDB: {processed_record.research_id}")
            else:
                logger.warning(f"⚠️ Failed to store research data in MongoDB")

        except Exception as e:
            logger.error(f"❌ Failed to store research data: {e}")

        # Validate research quality
        if research_result.confidence_score < 0.5:
            logger.warning(f"Low research confidence score: {research_result.confidence_score}")

        logger.info(f"Research completed with confidence: {research_result.confidence_score}")
        return research_result

    def _execute_message_generation_phase(
        self,
        workflow_input: WorkflowInput,
        research_result: ResearchOutput
    ) -> MessageOutput:
        """Execute the message generation phase of the workflow with MongoDB enhancement"""
        logger.info(f"Executing message generation phase for {workflow_input.lead_name}")

        # Check if we have comprehensive MongoDB contact data
        comprehensive_crm_data = self._get_comprehensive_contact_data(workflow_input.lead_id)

        # CRITICAL: Get research data from MongoDB (single source of truth)
        mongodb_research_data = self._get_research_data_from_mongodb(workflow_input.lead_id, workflow_input.company)

        # Create message input
        message_input = MessageInput(
            lead_data=LeadData(
                name=workflow_input.lead_name,
                company=workflow_input.company,
                title=workflow_input.title
            ),
            research_insights=ResearchInsights(
                recent_news=research_result.company_intelligence.get('recent_news', ''),
                conversation_hooks=research_result.conversation_hooks,
                timing_rationale=research_result.timing_rationale,
                company_intelligence=research_result.company_intelligence,
                decision_maker_insights=research_result.decision_maker_insights
            ),
            message_type=workflow_input.message_type,
            sender_info=SenderInfo(
                name=workflow_input.sender_name,
                company=workflow_input.sender_company,
                value_prop=workflow_input.value_proposition
            )
        )

        # Use hyper-personalized generation if we have comprehensive data from MongoDB
        if comprehensive_crm_data and comprehensive_crm_data.get('comprehensive_data'):
            logger.info(f"Using HYPER-PERSONALIZED message generation with COMPLETE MongoDB data")

            # Prepare business context for MongoDB sales
            business_context = {
                'owner': 'Rom Iluz',
                'company': 'MongoDB Solutions by Rom',
                'expertise': 'MongoDB Atlas Vector Search implementation, conversation intelligence architectures, real-time AI data pipelines',
                'services': 'MongoDB Atlas Vector Search setup ($15,000), AI conversation intelligence platforms ($500/hour), real-time analytics pipelines',
                'value_prop': 'Transform conversation data into AI-powered insights with MongoDB\'s purpose-built vector search and real-time aggregation capabilities'
            }

            # Use MongoDB research data if available, otherwise use current research
            enhanced_research_data = mongodb_research_data.__dict__ if mongodb_research_data else research_result.__dict__

            # Generate hyper-personalized message with ALL MongoDB data
            message_result = self.sales_team.message_agent.generate_hyper_personalized_message(
                message_input=message_input,
                crm_data=comprehensive_crm_data.get('comprehensive_data'),
                enhanced_research=enhanced_research_data,
                business_context=business_context
            )

            logger.info(f"HYPER-PERSONALIZED message generated with MongoDB data, score: {message_result.personalization_score}")
        else:
            logger.info(f"Using ANTI-HALLUCINATION message generation (limited MongoDB data)")
            # CRITICAL: Always use anti-hallucination method, even with limited data
            message_result = self.sales_team.message_agent.generate_hyper_personalized_message(
                message_input=message_input,
                crm_data=None,  # No comprehensive data available
                enhanced_research=None,  # No enhanced research available
                business_context=None  # Use default business context
            )

        # Enhanced validation for MongoDB workflow
        if message_result.personalization_score < 0.8:
            logger.warning(f"Personalization score below target: {message_result.personalization_score}")

        if message_result.predicted_response_rate < 0.4:
            logger.warning(f"Response rate below target: {message_result.predicted_response_rate}")

        logger.info(f"Message generated with personalization: {message_result.personalization_score}")
        return message_result

    def _get_comprehensive_contact_data(self, lead_id: str) -> Optional[Dict]:
        """Retrieve comprehensive contact data from MongoDB"""
        try:
            if not self.db_manager:
                return None

            contacts_collection = self.db_manager.get_collection("contacts")
            contact_data = contacts_collection.find_one({"monday_item_id": lead_id})

            if contact_data:
                logger.info(f"✅ Found comprehensive contact data for {lead_id}")
                return contact_data
            else:
                logger.info(f"⚠️ No comprehensive contact data found for {lead_id}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to retrieve contact data: {e}")
            return None

    def _get_research_data_from_mongodb(self, lead_id: str, company: str) -> Optional[Any]:
        """Retrieve research data from MongoDB (single source of truth)"""
        try:
            if not self.research_storage:
                return None

            # Try to get research by lead ID first
            research_data = self.research_storage.get_research_result(lead_id)

            if not research_data:
                # Fallback: search by company name
                research_results = self.research_storage.get_research_by_company(company, limit=1)
                if research_results:
                    research_data = research_results[0]

            if research_data:
                logger.info(f"✅ Found research data in MongoDB for {lead_id}")
                return research_data
            else:
                logger.info(f"⚠️ No research data found in MongoDB for {lead_id}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to retrieve research data: {e}")
            return None

    def _execute_outreach_phase(
        self,
        workflow_input: WorkflowInput,
        message_result: MessageOutput
    ) -> OutreachResult:
        """Execute the outreach phase of the workflow"""
        logger.info(f"Executing outreach phase for {workflow_input.lead_name}")

        # Create outreach request with pre-generated message
        outreach_request = OutreachRequest(
            lead_id=workflow_input.lead_id,
            lead_name=workflow_input.lead_name,
            company=workflow_input.company,
            title=workflow_input.title,
            industry=workflow_input.industry,
            company_size=workflow_input.company_size,
            phone_number=workflow_input.phone_number,
            message_type=MessageType(workflow_input.message_type),
            sender_info=SenderInfo(
                name=workflow_input.sender_name,
                company=workflow_input.sender_company,
                value_prop=workflow_input.value_proposition
            ),
            priority=workflow_input.priority,
            pre_generated_message=message_result.message_text  # CRITICAL FIX: Pass the hyper-personalized message
        )

        # Execute outreach
        outreach_result = self.sales_team.outreach_agent.execute_outreach(outreach_request)

        logger.info(f"Outreach completed with status: {outreach_result.status.value}")
        return outreach_result

    def _update_progress(
        self,
        progress: WorkflowProgress,
        callback: Optional[Callable[[WorkflowProgress], None]]
    ):
        """Update progress tracking and call callback if provided"""
        try:
            # Store progress in MongoDB with safe serialization
            collection = self.db_manager.get_collection("workflow_progress")

            # Create a safe dict for MongoDB storage
            progress_dict = {
                'workflow_id': progress.workflow_id,
                'status': progress.status.value,
                'current_step': progress.current_step,
                'progress_percentage': progress.progress_percentage,
                'started_at': progress.started_at,
                'completed_at': progress.completed_at,
                'total_steps': progress.total_steps,
                'error_message': progress.error_message
            }

            # Only add complex objects if they exist and are simple
            if progress.research_output and hasattr(progress.research_output, 'confidence_score'):
                progress_dict['research_confidence'] = progress.research_output.confidence_score

            if progress.message_output and hasattr(progress.message_output, 'personalization_score'):
                progress_dict['message_personalization'] = progress.message_output.personalization_score

            if progress.outreach_result and hasattr(progress.outreach_result, 'status'):
                progress_dict['outreach_status'] = progress.outreach_result.status.value if hasattr(progress.outreach_result.status, 'value') else str(progress.outreach_result.status)

            collection.update_one(
                {"workflow_id": progress.workflow_id},
                {"$set": progress_dict},
                upsert=True
            )

            # Call progress callback if provided
            if callback:
                callback(progress)

            logger.debug(f"Progress updated: {progress.current_step} ({progress.progress_percentage}%)")

        except Exception as e:
            logger.error(f"Failed to update progress: {e}")

    def get_workflow_progress(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """Get current workflow progress by ID"""
        try:
            collection = self.db_manager.get_collection("workflow_progress")
            progress_doc = collection.find_one({"workflow_id": workflow_id})

            if progress_doc:
                # Convert status string back to enum
                progress_doc['status'] = WorkflowStatus(progress_doc['status'])

                # Remove MongoDB _id field
                progress_doc.pop('_id', None)

                return WorkflowProgress(**progress_doc)

            return None

        except Exception as e:
            logger.error(f"Failed to get workflow progress: {e}")
            return None


# Convenience function for easy usage
def create_workflow_coordinator(api_keys: Dict[str, str], mongodb_connection: str) -> WorkflowCoordinator:
    """Create and return a configured Workflow Coordinator instance."""
    return WorkflowCoordinator(api_keys=api_keys, mongodb_connection=mongodb_connection)


# Example usage
if __name__ == "__main__":
    # Example usage
    import os

    api_keys = {
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        'MONDAY_API_KEY': os.getenv('MONDAY_API_KEY'),
        'MONGODB_CONNECTION_STRING': os.getenv('MONGODB_CONNECTION_STRING')
    }

    coordinator = create_workflow_coordinator(api_keys, api_keys['MONGODB_CONNECTION_STRING'])

    sample_input = WorkflowInput(
        lead_id="test-lead-123",
        lead_name="John Doe",
        company="Acme Corp",
        title="VP of Sales",
        industry="Technology",
        company_size="100-500",
        phone_number="+1234567890",
        message_type="text",
        sender_name="Sarah Smith",
        sender_company="Our Company",
        value_proposition="AI-powered sales automation"
    )

    def progress_callback(progress: WorkflowProgress):
        print(f"Progress: {progress.current_step} ({progress.progress_percentage}%)")

    result = coordinator.execute_lead_processing_workflow(sample_input, progress_callback)
    print(f"Workflow completed: {result.success}")
    print(f"Final status: {result.final_status.value}")
