"""
FastAPI Server for Agno Sales Extension

This module implements the FastAPI server that provides API endpoints for the Chrome extension
to interact with the sales agents. Based on cookbook/apps/fastapi patterns.

Endpoints:
- POST /api/process-lead: Process a lead through the complete workflow
- POST /api/send-message: Send a message via WhatsApp
- GET /api/lead-status/{lead_id}: Get lead processing status
- POST /api/test-connections: Test all API connections
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

from agno.agent import Agent
from agno.models.google import Gemini
from agno.storage.mongodb import MongoDbStorage

# Import our agents
from agents.research_agent import ResearchAgent, LeadInput
from agents.message_agent import MessageGenerationAgent, MessageInput, LeadData, ResearchInsights, SenderInfo
from agents.outreach_agent import OutreachAgent, OutreachRequest, MessageType
from agents.workflow_coordinator import WorkflowCoordinator, WorkflowInput, WorkflowProgress, WorkflowResult
from agents.research_storage import ResearchStorageManager
from config.database import MongoDBManager

# Import Monday.com client
from tools.monday_client import MondayClient

# Import authentication (includes 401 Unauthorized error handling)
from api.auth import get_current_user, require_lead_access, require_message_send, dev_auth_bypass, TokenData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Global variables for agents and database
research_agent: Optional[ResearchAgent] = None
message_agent: Optional[MessageGenerationAgent] = None
outreach_agent: Optional[OutreachAgent] = None
workflow_coordinator: Optional[WorkflowCoordinator] = None
research_storage: Optional[ResearchStorageManager] = None
db_manager: Optional[MongoDBManager] = None
monday_client: Optional[MondayClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    # Startup
    logger.info("Starting Agno Sales Extension API server...")
    await initialize_agents()
    logger.info("All agents initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agno Sales Extension API server...")
    await cleanup_agents()
    logger.info("Cleanup completed")


async def initialize_agents():
    """Initialize all agents and database connections"""
    global research_agent, message_agent, outreach_agent, workflow_coordinator, research_storage, db_manager, monday_client

    try:
        # Load API keys from environment
        api_keys = {
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
            'MONDAY_API_KEY': os.getenv('MONDAY_API_KEY'),
            'MONGODB_CONNECTION_STRING': os.getenv('MONGODB_CONNECTION_STRING')
        }

        # Debug: Log API key status (safely)
        logger.info(f"🔑 API Keys Status:")
        for key, value in api_keys.items():
            if value:
                logger.info(f"  ✅ {key}: {value[:10]}...")
            else:
                logger.error(f"  ❌ {key}: MISSING")

        # Validate required API keys
        missing_keys = [key for key, value in api_keys.items() if not value]
        if missing_keys:
            raise ValueError(f"Missing required API keys: {missing_keys}")

        # Initialize database manager
        db_manager = MongoDBManager()
        db_manager.connect()

        # Fetch agent configurations from MongoDB
        try:
            agent_configs_collection = db_manager.get_collection("agent_configurations")
            agent_config = agent_configs_collection.find_one()
            if not agent_config:
                raise ValueError("Agent configuration not found in 'agent_configurations' collection. Please run the seed_agent_configurations.py script.")

            # Validate that required agent configurations exist
            required_agents = ['research_agent', 'message_generation_agent']
            for agent_name in required_agents:
                if agent_name not in agent_config:
                    raise ValueError(f"Missing configuration for {agent_name} in MongoDB")

            logger.info("✅ Successfully loaded agent configurations from MongoDB.")
            logger.info(f"✅ Available agent configs: {list(agent_config.keys())}")

            # Debug: Log configuration details
            if 'research_agent' in agent_config:
                research_config = agent_config['research_agent']
                query_count = len(research_config.get('tavily_search_queries', []))
                logger.info(f"✅ Research agent config: {query_count} search queries configured")

        except Exception as e:
            logger.error(f"❌ Failed to load agent configurations: {e}")
            raise

        # Initialize Monday.com client
        monday_client = MondayClient(api_token=api_keys['MONDAY_API_KEY'])

        # Initialize agents with dynamic configurations
        research_agent = ResearchAgent(
            api_keys=api_keys,
            config=agent_config.get('research_agent', {})
        )
        message_agent = MessageGenerationAgent(
            api_keys=api_keys,
            config=agent_config.get('message_generation_agent', {})
        )
        outreach_agent = OutreachAgent(
            api_keys=api_keys,
            mongodb_connection=api_keys['MONGODB_CONNECTION_STRING']
        )

        # Initialize research storage
        research_storage = ResearchStorageManager(
            connection_string=api_keys['MONGODB_CONNECTION_STRING']
        )
        research_storage.connect()  # Establish database connection

        # Initialize workflow coordinator
        workflow_coordinator = WorkflowCoordinator(
            api_keys=api_keys,
            mongodb_connection=api_keys['MONGODB_CONNECTION_STRING']
        )

        logger.info("All agents initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")
        raise


async def cleanup_agents():
    """Cleanup agents and database connections"""
    global db_manager
    
    try:
        if db_manager:
            db_manager.disconnect()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


# Create FastAPI app
app = FastAPI(
    title="Agno Sales Extension API",
    description="API server for AI-powered sales agent automation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Pydantic models for API requests/responses
class LeadProcessRequest(BaseModel):
    """Request model for lead processing (legacy)"""
    lead_id: str = Field(..., description="Monday.com lead ID")
    lead_name: str = Field(..., description="Lead's full name")
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Lead's job title")
    industry: str = Field(..., description="Company industry")
    company_size: str = Field(..., description="Company size")
    phone_number: str = Field(..., description="WhatsApp phone number")
    message_type: str = Field(default="text", description="Message type: text|voice|image")
    sender_name: str = Field(..., description="Sender's name")
    sender_company: str = Field(..., description="Sender's company")
    value_proposition: str = Field(..., description="Value proposition")


class MondayItemRequest(BaseModel):
    """Request model for MongoDB-powered Monday.com item processing"""
    monday_item_id: str = Field(..., description="Monday.com item ID")
    board_id: str = Field(..., description="Monday.com board ID")
    fallback_name: Optional[str] = Field(None, description="Fallback name for UI display")
    fallback_company: Optional[str] = Field(None, description="Fallback company for UI display")


class MessageSendRequest(BaseModel):
    """Request model for direct message sending"""
    phone_number: str = Field(..., description="WhatsApp phone number")
    message: str = Field(..., description="Message to send")
    message_type: str = Field(default="text", description="Message type")


class LeadStatusResponse(BaseModel):
    """Response model for lead status"""
    lead_id: str
    status: str
    last_updated: str
    message_sent: Optional[str] = None
    delivery_status: Optional[str] = None


class ConnectionTestResponse(BaseModel):
    """Response model for connection tests"""
    mongodb: bool
    whatsapp: bool
    monday_com: bool
    tavily: bool
    gemini: bool
    overall_status: str


class WorkflowProgressResponse(BaseModel):
    """Response model for workflow progress"""
    workflow_id: str
    status: str
    current_step: str
    progress_percentage: float
    started_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class MessagePreviewRequest(BaseModel):
    """Request model for message preview generation"""
    monday_item_id: str = Field(..., description="Monday.com item ID")
    board_id: str = Field(..., description="Monday.com board ID")
    fallback_name: Optional[str] = Field(None, description="Fallback name for UI display")
    fallback_company: Optional[str] = Field(None, description="Fallback company for UI display")


class MessagePreviewResponse(BaseModel):
    """Response model for message preview"""
    preview_id: str
    message_text: str
    personalization_score: float
    predicted_response_rate: float
    lead_name: str
    company: str
    phone_number: str
    generated_at: str


class MessageApprovalRequest(BaseModel):
    """Request model for message approval"""
    preview_id: str = Field(..., description="Preview ID from preview generation")
    action: str = Field(..., description="approve|reject|edit")
    edited_message: Optional[str] = Field(None, description="Edited message text if action is edit")
    monday_item_id: str = Field(..., description="Monday.com item ID")


class MessageApprovalResponse(BaseModel):
    """Response model for message approval"""
    success: bool
    action_taken: str
    message_sent: Optional[str] = None
    whatsapp_message_id: Optional[str] = None
    monday_updated: bool
    timestamp: str


# Authentication dependency - use development bypass for now
async def get_auth_user() -> TokenData:
    """Get authenticated user - using dev bypass for development"""
    # In development, use bypass. In production, use proper JWT authentication
    if os.getenv("ENVIRONMENT", "development") == "development":
        return await dev_auth_bypass()
    else:
        # In production, use proper authentication
        return await get_current_user()


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agno Sales Extension API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "research_agent": research_agent is not None,
            "message_agent": message_agent is not None,
            "outreach_agent": outreach_agent is not None,
            "workflow_coordinator": workflow_coordinator is not None
        }
    }


@app.get("/api/extension-status")
async def extension_status():
    """Simple status endpoint for Chrome extension"""
    return {
        "status": "connected",
        "backend_ready": True,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.post("/api/process-lead")
async def process_lead(
    request: Dict[str, Any],
    current_user: TokenData = Depends(get_auth_user)
) -> Dict[str, Any]:
    """
    Process a lead through the complete workflow:
    Supports both legacy (LeadProcessRequest) and MongoDB (MondayItemRequest) workflows
    """
    try:
        # Determine request type based on presence of monday_item_id
        if "monday_item_id" in request and "board_id" in request:
            # MongoDB-powered workflow
            logger.info(f"Processing MongoDB workflow for item: {request['monday_item_id']}")
            return await process_lead_with_mongodb(request, current_user)
        else:
            # Legacy workflow
            logger.info(f"Processing legacy workflow for: {request.get('lead_name', 'Unknown')}")
            return await process_lead_legacy(request, current_user)

    except Exception as e:
        logger.error(f"Lead processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lead processing failed: {str(e)}"
        )


async def process_lead_with_mongodb(
    request_data: Dict[str, Any],
    current_user: TokenData
) -> Dict[str, Any]:
    """Process lead using MongoDB-powered workflow with Monday.com API"""
    try:
        # Validate request data
        monday_request = MondayItemRequest(**request_data)

        logger.info(f"MongoDB workflow: Fetching comprehensive data for item {monday_request.monday_item_id}")

        # Validate services are initialized
        if not monday_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Monday.com client not initialized"
            )

        if not workflow_coordinator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Workflow coordinator not initialized"
            )

        # Fetch comprehensive CRM data from Monday.com
        try:
            comprehensive_data = monday_client.get_lead_comprehensive_data(monday_request.monday_item_id)
            logger.info(f"✅ Fetched comprehensive data: {len(comprehensive_data.get('all_column_data', {}))} columns, {len(comprehensive_data.get('notes_and_updates', []))} notes")
        except Exception as e:
            logger.error(f"❌ Failed to fetch Monday.com data: {e}")
            # Fallback to basic data if Monday.com fetch fails
            comprehensive_data = {
                "monday_id": monday_request.monday_item_id,
                "name": monday_request.fallback_name or "Unknown Lead",
                "company": monday_request.fallback_company or "Unknown Company",
                "all_column_data": {},
                "notes_and_updates": [],
                "crm_insights": {"data_richness_score": 0.1}
            }

        # Store comprehensive data in MongoDB as single source of truth
        if db_manager:
            try:
                logger.info("Attempting to store data in MongoDB...")
                contacts_collection = db_manager.get_collection("contacts")
                contact_doc = {
                    "monday_item_id": monday_request.monday_item_id,
                    "board_id": monday_request.board_id,
                    "comprehensive_data": comprehensive_data,
                    "last_updated": datetime.now().isoformat(),
                    "data_source": "monday_api"
                }
                logger.debug(f"Contact document to be upserted: {contact_doc}")

                # Upsert contact data
                result = contacts_collection.replace_one(
                    {"monday_item_id": monday_request.monday_item_id},
                    contact_doc,
                    upsert=True
                )
                logger.info(f"✅ MongoDB upsert result: matched_count={result.matched_count}, modified_count={result.modified_count}, upserted_id={result.upserted_id}")
                logger.info(f"✅ Stored comprehensive data in MongoDB for item {monday_request.monday_item_id}")
            except Exception as e:
                logger.error(f"❌ Failed to store data in MongoDB: {e}", exc_info=True)

        # Create workflow input from comprehensive data
        workflow_input = WorkflowInput(
            lead_id=monday_request.monday_item_id,
            lead_name=comprehensive_data.get("name", monday_request.fallback_name or "Unknown Lead"),
            company=comprehensive_data.get("company", monday_request.fallback_company or "Unknown Company"),
            title=comprehensive_data.get("title", "Unknown Title"),
            industry="Technology",  # Will be enhanced by research agent
            company_size="Unknown",  # Will be enhanced by research agent
            phone_number=comprehensive_data.get("phone", "+1234567890"),  # Placeholder
            message_type="text",
            sender_name="MongoDB Sales Agent",
            sender_company="MongoDB",
            value_proposition="MongoDB database solutions for AI-powered applications"
        )

        # Execute MongoDB-powered workflow
        result = workflow_coordinator.execute_lead_processing_workflow(workflow_input)

        return {
            "success": result.success,
            "workflow_id": result.workflow_id,
            "lead_id": result.lead_id,
            "final_status": result.final_status.value,
            "research_confidence": result.research_confidence,
            "message_personalization_score": result.message_personalization_score,
            "predicted_response_rate": result.predicted_response_rate,
            "outreach_status": result.outreach_status,
            "whatsapp_message_id": result.whatsapp_message_id,
            "execution_time_seconds": result.execution_time_seconds,
            "error_details": result.error_details,
            "workflow_type": "mongodb_powered",
            "data_richness_score": comprehensive_data.get("crm_insights", {}).get("data_richness_score", 0.0),
            "mongodb_data_stored": True
        }

    except Exception as e:
        logger.error(f"MongoDB workflow failed: {e}")
        raise


async def process_lead_legacy(
    request_data: Dict[str, Any],
    current_user: TokenData
) -> Dict[str, Any]:
    """Process lead using legacy workflow"""
    try:
        # Validate request data
        legacy_request = LeadProcessRequest(**request_data)

        logger.info(f"Legacy workflow: Processing {legacy_request.lead_name} at {legacy_request.company}")

        # Validate workflow coordinator is initialized
        if not workflow_coordinator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Workflow coordinator not properly initialized"
            )

        # Create workflow input
        workflow_input = WorkflowInput(
            lead_id=legacy_request.lead_id,
            lead_name=legacy_request.lead_name,
            company=legacy_request.company,
            title=legacy_request.title,
            industry=legacy_request.industry,
            company_size=legacy_request.company_size,
            phone_number=legacy_request.phone_number,
            message_type=legacy_request.message_type,
            sender_name=legacy_request.sender_name,
            sender_company=legacy_request.sender_company,
            value_proposition=legacy_request.value_proposition
        )

        # Execute complete workflow
        result = workflow_coordinator.execute_lead_processing_workflow(workflow_input)

        return {
            "success": result.success,
            "workflow_id": result.workflow_id,
            "lead_id": result.lead_id,
            "final_status": result.final_status.value,
            "research_confidence": result.research_confidence,
            "message_personalization_score": result.message_personalization_score,
            "predicted_response_rate": result.predicted_response_rate,
            "outreach_status": result.outreach_status,
            "whatsapp_message_id": result.whatsapp_message_id,
            "execution_time_seconds": result.execution_time_seconds,
            "error_details": result.error_details,
            "workflow_type": "legacy"
        }

    except Exception as e:
        logger.error(f"Legacy workflow failed: {e}")
        raise


@app.post("/api/send-message")
async def send_message(
    request: MessageSendRequest,
    current_user: TokenData = Depends(get_auth_user)
) -> Dict[str, Any]:
    """
    Send a direct message via WhatsApp
    """
    try:
        logger.info(f"Sending message to {request.phone_number}")
        
        if not outreach_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Outreach agent not initialized"
            )
        
        # Send message via WhatsApp bridge
        result = outreach_agent.whatsapp_bridge.send_text_message(
            request.phone_number,
            request.message
        )
        
        if result.get("success", False):
            return {
                "success": True,
                "message_id": result.get("messageId"),
                "phone_number": request.phone_number,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message send failed: {result.get('error', 'Unknown error')}"
            )
        
    except Exception as e:
        logger.error(f"Message sending failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message sending failed: {str(e)}"
        )


@app.get("/api/lead-status/{lead_id}")
async def get_lead_status(
    lead_id: str,
    current_user: TokenData = Depends(get_auth_user)
) -> LeadStatusResponse:
    """
    Get lead processing status from Monday.com
    """
    try:
        logger.info(f"Getting status for lead: {lead_id}")

        if not db_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database manager not initialized"
            )

        # Query MongoDB for lead status
        collection = db_manager.get_collection("lead_status")
        lead_status = collection.find_one({"lead_id": lead_id})

        if not lead_status:
            # Return default status if not found
            return LeadStatusResponse(
                lead_id=lead_id,
                status="not_found",
                last_updated=datetime.now().isoformat(),
                message_sent=None,
                delivery_status=None
            )

        return LeadStatusResponse(
            lead_id=lead_id,
            status=lead_status.get("status", "unknown"),
            last_updated=lead_status.get("last_updated", datetime.now().isoformat()),
            message_sent=lead_status.get("message_sent"),
            delivery_status=lead_status.get("delivery_status")
        )

    except Exception as e:
        logger.error(f"Failed to get lead status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lead status: {str(e)}"
        )


@app.post("/api/test-connections")
async def test_connections(
    current_user: TokenData = Depends(get_auth_user)
) -> ConnectionTestResponse:
    """
    Test all API connections and services
    """
    try:
        logger.info("Testing all connections")

        # Test MongoDB
        mongodb_status = False
        try:
            if db_manager:
                db_manager.test_connection()
                mongodb_status = True
        except Exception as e:
            logger.error(f"MongoDB test failed: {e}")

        # Test WhatsApp
        whatsapp_status = False
        try:
            if outreach_agent:
                status_result = outreach_agent.whatsapp_bridge.check_connection_status()
                whatsapp_status = status_result.get("connected", False)
        except Exception as e:
            logger.error(f"WhatsApp test failed: {e}")

        # Test Monday.com
        monday_status = False
        try:
            if outreach_agent:
                # Simple test by trying to update a dummy status
                monday_status = True  # Placeholder - would need actual test
        except Exception as e:
            logger.error(f"Monday.com test failed: {e}")

        # Test Tavily
        tavily_status = False
        try:
            if research_agent:
                tavily_status = True  # Placeholder - would need actual test
        except Exception as e:
            logger.error(f"Tavily test failed: {e}")

        # Test Gemini
        gemini_status = False
        try:
            if message_agent:
                gemini_status = True  # Placeholder - would need actual test
        except Exception as e:
            logger.error(f"Gemini test failed: {e}")

        # Determine overall status
        all_services = [mongodb_status, whatsapp_status, monday_status, tavily_status, gemini_status]
        if all(all_services):
            overall_status = "all_connected"
        elif any(all_services):
            overall_status = "partial_connection"
        else:
            overall_status = "no_connections"

        return ConnectionTestResponse(
            mongodb=mongodb_status,
            whatsapp=whatsapp_status,
            monday_com=monday_status,
            tavily=tavily_status,
            gemini=gemini_status,
            overall_status=overall_status
        )

    except Exception as e:
        logger.error(f"Connection testing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection testing failed: {str(e)}"
        )


@app.get("/api/workflow-progress/{workflow_id}")
async def get_workflow_progress(
    workflow_id: str,
    current_user: TokenData = Depends(get_auth_user)
) -> WorkflowProgressResponse:
    """
    Get workflow progress by workflow ID
    """
    try:
        logger.info(f"Getting workflow progress for: {workflow_id}")

        if not workflow_coordinator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Workflow coordinator not initialized"
            )

        # Get workflow progress
        progress = workflow_coordinator.get_workflow_progress(workflow_id)

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )

        return WorkflowProgressResponse(
            workflow_id=progress.workflow_id,
            status=progress.status.value,
            current_step=progress.current_step,
            progress_percentage=progress.progress_percentage,
            started_at=progress.started_at,
            completed_at=progress.completed_at,
            error_message=progress.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow progress: {str(e)}"
        )


@app.post("/api/preview-message")
async def preview_message(
    request: MessagePreviewRequest,
    current_user: TokenData = Depends(get_auth_user)
) -> MessagePreviewResponse:
    """
    Generate message preview for approval workflow
    """
    try:
        logger.info(f"Generating message preview for item: {request.monday_item_id}")

        # Validate services are initialized
        if not monday_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Monday.com client not initialized"
            )

        if not message_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Message agent not initialized"
            )

        # Fetch comprehensive CRM data from Monday.com
        try:
            comprehensive_data = monday_client.get_lead_comprehensive_data(request.monday_item_id)
            logger.info(f"✅ Fetched comprehensive data for preview")
        except Exception as e:
            logger.error(f"❌ Failed to fetch Monday.com data: {e}")
            # Fallback to basic data
            comprehensive_data = {
                "monday_id": request.monday_item_id,
                "name": request.fallback_name or "Unknown Lead",
                "company": request.fallback_company or "Unknown Company",
                "phone": "+1234567890",
                "all_column_data": {},
                "notes_and_updates": [],
                "crm_insights": {"data_richness_score": 0.1}
            }

        # Generate message using hyper-personalized agent
        message_input = MessageInput(
            lead_data=LeadData(
                name=comprehensive_data.get("name", request.fallback_name or "Unknown Lead"),
                company=comprehensive_data.get("company", request.fallback_company or "Unknown Company"),
                title=comprehensive_data.get("title", "Unknown Title")
            ),
            research_insights=ResearchInsights(
                recent_news="",
                conversation_hooks=[],
                timing_rationale="Professional outreach timing"
            ),
            message_type="text",
            sender_info=SenderInfo(
                name="MongoDB Sales Agent",
                company="MongoDB",
                value_prop="MongoDB database solutions for AI-powered applications"
            )
        )

        # CRITICAL FIX: Execute research before message generation
        logger.info(f"🔬 Starting research phase for {comprehensive_data.get('name', 'Unknown')}")

        # Import research agent and workflow coordinator
        from agents.research_agent import ResearchAgent, LeadInput
        from agents.workflow_coordinator import WorkflowCoordinator, WorkflowInput

        # Initialize research agent if not already done
        if not hasattr(app.state, 'research_agent'):
            # Get API keys from global variables (they're already validated during startup)
            api_keys = {
                'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
                'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
                'MONDAY_API_KEY': os.getenv('MONDAY_API_KEY'),
                'MONGODB_CONNECTION_STRING': os.getenv('MONGODB_CONNECTION_STRING')
            }

            # Load agent configuration from MongoDB
            try:
                agent_configs_collection = db_manager.get_collection("agent_configurations")
                agent_config = agent_configs_collection.find_one()
                research_config = agent_config.get('research_agent', {}) if agent_config else {}
            except Exception as e:
                logger.error(f"❌ Failed to load research agent config: {e}")
                research_config = {}

            app.state.research_agent = ResearchAgent(api_keys=api_keys, config=research_config)

        # Create lead input for research
        try:
            lead_input = LeadInput(
                lead_name=comprehensive_data.get('name', 'Unknown'),
                company=comprehensive_data.get('company', 'Unknown'),
                title=comprehensive_data.get('title', ''),
                industry=comprehensive_data.get('industry', 'Technology'),
                company_size=comprehensive_data.get('company_size', 'Unknown')
            )
            logger.info(f"✅ LeadInput created successfully for {comprehensive_data.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ Failed to create LeadInput: {e}")
            logger.error(f"Comprehensive data keys: {list(comprehensive_data.keys())}")
            raise

        # Execute research
        research_output = app.state.research_agent.research_lead(lead_input)
        logger.info(f"✅ Research completed with confidence score: {research_output.confidence_score}")

        # Store research in MongoDB
        if research_storage:
            try:
                # Create ResearchRecord from ResearchOutput
                from agents.research_storage import ResearchRecord
                from datetime import datetime, timezone

                research_record = ResearchRecord(
                    research_id=f"research_{request.monday_item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    lead_name=comprehensive_data.get('name', 'Unknown'),
                    company=comprehensive_data.get('company', 'Unknown'),
                    title=comprehensive_data.get('title', ''),
                    industry=comprehensive_data.get('industry', 'Technology'),
                    company_size=comprehensive_data.get('company_size', 'Unknown'),
                    confidence_score=research_output.confidence_score,
                    company_intelligence=research_output.company_intelligence,
                    decision_maker_insights=research_output.decision_maker_insights,
                    conversation_hooks=research_output.conversation_hooks,
                    timing_rationale=research_output.timing_rationale,
                    sources=research_output.sources,
                    research_timestamp=research_output.research_timestamp,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    status="completed"
                )

                research_storage.store_research_result(research_record)
                logger.info(f"✅ Research stored in MongoDB for {request.monday_item_id}")
            except Exception as e:
                logger.error(f"❌ Failed to store research: {e}")

        # Generate hyper-personalized message with research data
        # Convert ResearchOutput object to dictionary format expected by message agent
        enhanced_research_data = research_output.__dict__ if research_output else None

        message_output = message_agent.generate_hyper_personalized_message(
            message_input,
            crm_data=comprehensive_data,
            enhanced_research=enhanced_research_data,
            business_context=None
        )

        # Generate unique preview ID
        preview_id = f"preview_{request.monday_item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Store preview in temporary storage (could use Redis in production)
        preview_data = {
            "preview_id": preview_id,
            "monday_item_id": request.monday_item_id,
            "board_id": request.board_id,
            "message_text": message_output.message_text,
            "phone_number": comprehensive_data.get("phone", "+1234567890"),
            "comprehensive_data": comprehensive_data,
            "generated_at": datetime.now().isoformat()
        }

        # Store in MongoDB for persistence
        if db_manager:
            try:
                previews_collection = db_manager.get_collection("message_previews")
                previews_collection.insert_one(preview_data)
                logger.info(f"✅ Stored preview {preview_id} in MongoDB")

                # ALSO STORE CONTACT DATA (same as full workflow)
                contacts_collection = db_manager.get_collection("contacts")
                contact_doc = {
                    "monday_item_id": request.monday_item_id,
                    "board_id": request.board_id,
                    "comprehensive_data": comprehensive_data,
                    "last_updated": datetime.now().isoformat(),
                    "data_source": "monday_api",
                    "workflow_type": "preview"
                }
                contacts_collection.replace_one(
                    {"monday_item_id": request.monday_item_id},
                    contact_doc,
                    upsert=True
                )
                logger.info(f"✅ Stored contact data for preview workflow: {request.monday_item_id}")

            except Exception as e:
                logger.error(f"❌ Failed to store preview/contact: {e}")

        return MessagePreviewResponse(
            preview_id=preview_id,
            message_text=message_output.message_text,
            personalization_score=message_output.personalization_score,
            predicted_response_rate=message_output.predicted_response_rate,
            lead_name=comprehensive_data.get("name", request.fallback_name or "Unknown Lead"),
            company=comprehensive_data.get("company", request.fallback_company or "Unknown Company"),
            phone_number=comprehensive_data.get("phone", "+1234567890"),
            generated_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Message preview generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message preview generation failed: {str(e)}"
        )


@app.post("/api/approve-message")
async def approve_message(
    request: MessageApprovalRequest,
    current_user: TokenData = Depends(get_auth_user)
) -> MessageApprovalResponse:
    """
    Handle message approval workflow (approve/reject/edit)
    """
    try:
        logger.info(f"Processing message approval: {request.action} for preview {request.preview_id}")

        # Retrieve preview data
        preview_data = None
        if db_manager:
            try:
                previews_collection = db_manager.get_collection("message_previews")
                preview_data = previews_collection.find_one({"preview_id": request.preview_id})
                logger.info(f"✅ Retrieved preview data for {request.preview_id}")
            except Exception as e:
                logger.error(f"❌ Failed to retrieve preview: {e}")

        if not preview_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preview {request.preview_id} not found"
            )

        # Handle different actions
        if request.action == "reject":
            # Update Monday.com with rejection status
            if monday_client:
                try:
                    monday_client.add_note_to_item(
                        request.monday_item_id,
                        f"Message rejected by user at {datetime.now().isoformat()}"
                    )
                except Exception as e:
                    logger.error(f"Failed to update Monday.com with rejection: {e}")

            return MessageApprovalResponse(
                success=True,
                action_taken="rejected",
                message_sent=None,
                whatsapp_message_id=None,
                monday_updated=True,
                timestamp=datetime.now().isoformat()
            )

        elif request.action in ["approve", "edit"]:
            # Determine final message text
            final_message = request.edited_message if request.action == "edit" else preview_data["message_text"]

            # Send message via WhatsApp
            if not outreach_agent:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Outreach agent not initialized"
                )

            send_result = outreach_agent.whatsapp_bridge.send_text_message(
                preview_data["phone_number"],
                final_message
            )

            if send_result.get("success", False):
                # Auto-document message in Monday.com with comprehensive details
                if monday_client:
                    try:
                        monday_client.add_message_documentation(
                            request.monday_item_id,
                            final_message,
                            send_result.get('messageId'),
                            'sent'
                        )
                        logger.info(f"✅ Auto-documented message in Monday.com for item {request.monday_item_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to auto-document message: {e}")

                return MessageApprovalResponse(
                    success=True,
                    action_taken=request.action,
                    message_sent=final_message,
                    whatsapp_message_id=send_result.get("messageId"),
                    monday_updated=True,
                    timestamp=datetime.now().isoformat()
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"WhatsApp send failed: {send_result.get('error', 'Unknown error')}"
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {request.action}. Must be approve, reject, or edit"
            )

    except Exception as e:
        logger.error(f"Message approval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message approval failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
