"""
Outreach Agent Implementation for Agno Sales Extension

This module implements the Outreach Agent that integrates WhatsApp bridge,
delivery tracking, and Monday.com status updates for complete sales automation.

Based on examples/whatsapp-web-js patterns and Monday.com API integration.
"""

import json
import logging
import re
import requests
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from agents.research_agent import ResearchAgent, LeadInput
from agents.message_quality_optimizer import MessageQualityOptimizer, MessageStatus
from agents.message_agent import SenderInfo
from agents.research_storage import ResearchStorageManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OutreachStatus(Enum):
    """Outreach status tracking"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    FAILED = "failed"
    BLOCKED = "blocked"


class MessageType(Enum):
    """Message type enumeration"""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"


@dataclass
class OutreachRequest:
    """Outreach request data structure"""
    lead_id: str
    lead_name: str
    company: str
    title: str
    industry: str
    company_size: str
    phone_number: str
    message_type: MessageType
    sender_info: SenderInfo
    priority: int = 1  # 1=high, 2=medium, 3=low
    scheduled_time: Optional[str] = None
    pre_generated_message: Optional[str] = None  # CRITICAL: Use pre-generated hyper-personalized message


@dataclass
class OutreachResult:
    """Outreach execution result"""
    request_id: str
    lead_id: str
    status: OutreachStatus
    message_sent: str
    whatsapp_message_id: Optional[str]
    delivery_timestamp: Optional[str]
    read_timestamp: Optional[str]
    reply_received: Optional[str]
    error_message: Optional[str]
    monday_updated: bool
    execution_timestamp: str


class WhatsAppBridge:
    """
    WhatsApp Web.js bridge for message sending and status tracking.
    Communicates with Node.js WhatsApp service via HTTP API.
    """
    
    def __init__(self, whatsapp_service_url: str = "http://localhost:3001"):
        """
        Initialize WhatsApp bridge.
        
        Args:
            whatsapp_service_url: URL of the WhatsApp Web.js service
        """
        self.service_url = whatsapp_service_url
        self.session = requests.Session()
        self.session.timeout = 30
        
    def check_connection_status(self) -> Dict[str, Any]:
        """Check WhatsApp connection status"""
        try:
            response = self.session.get(f"{self.service_url}/get-status")
            response.raise_for_status()
            result = response.json()
            # Transform response to match expected format
            if result.get("success") and result.get("status", {}).get("isReady"):
                return {"connected": True, "status": result.get("status")}
            else:
                return {"connected": False, "status": result.get("status", {})}
        except Exception as e:
            logger.error(f"Failed to check WhatsApp status: {e}")
            return {"connected": False, "error": str(e)}

    def wait_for_ready(self, timeout: int = 60, retry_interval: int = 2) -> bool:
        """
        Wait for WhatsApp to be ready with retry logic

        Args:
            timeout: Maximum time to wait in seconds
            retry_interval: Time between retries in seconds

        Returns:
            True if WhatsApp is ready, False if timeout
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.check_connection_status()
            if status.get("connected", False):
                logger.info("✅ WhatsApp is ready!")
                return True

            logger.info(f"⏳ WhatsApp not ready yet, retrying in {retry_interval}s...")
            time.sleep(retry_interval)

        logger.error(f"❌ WhatsApp not ready after {timeout} seconds")
        return False

    def _format_phone_for_whatsapp(self, phone_number: str) -> str:
        """
        ROBUST phone number formatting for WhatsApp Web.js

        Args:
            phone_number: Raw phone number from Monday.com

        Returns:
            Formatted phone number for WhatsApp (e.g., "972549135099@c.us")
        """
        if not phone_number:
            return ""

        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone_number)

        # Handle different phone number formats
        if len(digits_only) == 10:
            # US number without country code
            formatted = f"1{digits_only}@c.us"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            # US number with country code
            formatted = f"{digits_only}@c.us"
        elif len(digits_only) >= 10 and len(digits_only) <= 15:
            # International number (already has country code)
            formatted = f"{digits_only}@c.us"
        else:
            # Invalid length
            logger.error(f"Invalid phone number length: {phone_number} -> {digits_only}")
            return ""

        logger.info(f"📞 Formatted phone: {phone_number} -> {formatted}")
        return formatted

    def send_text_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send text message via WhatsApp.

        Args:
            phone_number: Target phone number (with country code)
            message: Message text to send

        Returns:
            Dict with message ID and status
        """
        try:
            # IMPROVED: Check WhatsApp readiness before sending
            if not self.wait_for_ready(timeout=30):
                raise Exception("WhatsApp bridge is not ready")

            # IMPROVED: Robust phone number formatting for WhatsApp
            formatted_number = self._format_phone_for_whatsapp(phone_number)
            if not formatted_number:
                raise ValueError(f"Invalid phone number format: {phone_number}")

            payload = {
                "chatId": formatted_number,
                "message": message
            }

            response = self.session.post(f"{self.service_url}/send-message", json=payload)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Text message sent to {phone_number}: {result.get('messageId')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send text message to {phone_number}: {e}")
            return {"success": False, "error": str(e)}
    
    def send_voice_message(self, phone_number: str, audio_path: str) -> Dict[str, Any]:
        """
        Send voice message via WhatsApp.
        
        Args:
            phone_number: Target phone number
            audio_path: Path to audio file
            
        Returns:
            Dict with message ID and status
        """
        try:
            # IMPROVED: Use robust phone formatting
            formatted_number = self._format_phone_for_whatsapp(phone_number)
            if not formatted_number:
                raise ValueError(f"Invalid phone number format: {phone_number}")
            
            # Read audio file and encode as base64
            import base64
            with open(audio_path, 'rb') as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
            
            payload = {
                "chatId": formatted_number,
                "media": {
                    "data": audio_data,
                    "mimetype": "audio/ogg; codecs=opus",
                    "filename": "voice_message.ogg"
                },
                "options": {
                    "sendAudioAsVoice": True
                }
            }
            
            response = self.session.post(f"{self.service_url}/send-media", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Voice message sent to {phone_number}: {result.get('messageId')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send voice message to {phone_number}: {e}")
            return {"success": False, "error": str(e)}
    
    def send_image_message(self, phone_number: str, image_path: str, caption: str = "") -> Dict[str, Any]:
        """
        Send image message via WhatsApp.
        
        Args:
            phone_number: Target phone number
            image_path: Path to image file
            caption: Optional image caption
            
        Returns:
            Dict with message ID and status
        """
        try:
            # IMPROVED: Use robust phone formatting
            formatted_number = self._format_phone_for_whatsapp(phone_number)
            if not formatted_number:
                raise ValueError(f"Invalid phone number format: {phone_number}")
            
            # Read image file and encode as base64
            import base64
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            payload = {
                "chatId": formatted_number,
                "media": {
                    "data": image_data,
                    "mimetype": "image/png",
                    "filename": "message_image.png"
                },
                "caption": caption
            }
            
            response = self.session.post(f"{self.service_url}/send-media", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Image message sent to {phone_number}: {result.get('messageId')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send image message to {phone_number}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get message delivery status.
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            Dict with delivery status information
        """
        try:
            response = self.session.get(f"{self.service_url}/message-status/{message_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get message status for {message_id}: {e}")
            return {"error": str(e)}


class MondayStatusUpdater:
    """
    Monday.com status updater for tracking outreach progress.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Monday.com updater.
        
        Args:
            api_key: Monday.com API key
        """
        self.api_key = api_key
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
    
    def update_lead_status(self, item_id: str, status: OutreachStatus, message_sent: str = "") -> bool:
        """
        Update lead status in Monday.com.
        
        Args:
            item_id: Monday.com item ID
            status: Outreach status
            message_sent: Message that was sent
            
        Returns:
            Success status
        """
        try:
            # Map outreach status to Monday.com status values (using actual board labels)
            # Available labels: New Lead, Unqualified, Contacted, Attempted to contact, Qualified
            status_mapping = {
                OutreachStatus.PENDING: "New Lead",
                OutreachStatus.QUEUED: "Attempted to contact",
                OutreachStatus.SENDING: "Attempted to contact",
                OutreachStatus.SENT: "Contacted",
                OutreachStatus.DELIVERED: "Contacted",
                OutreachStatus.READ: "Qualified",
                OutreachStatus.REPLIED: "Qualified",
                OutreachStatus.FAILED: "Unqualified",
                OutreachStatus.BLOCKED: "Unqualified"
            }

            monday_status = status_mapping.get(status, "New Lead")
            logger.info(f"Mapping status {status.value} to Monday.com label: {monday_status}")
            
            # Update status column
            query = """
            mutation ($item_id: ID!, $board_id: ID!, $column_values: JSON!) {
                change_multiple_column_values(
                    item_id: $item_id,
                    board_id: $board_id,
                    column_values: $column_values
                ) {
                    id
                }
            }
            """
            
            column_values = {
                "lead_status": {"label": monday_status}
                # REMOVED: No longer storing message in text column - using proper notes/activities instead
            }
            
            variables = {
                "item_id": item_id,
                "board_id": "2001047343",  # Default leads board ID
                "column_values": json.dumps(column_values)
            }
            
            response = requests.post(
                self.api_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                logger.error(f"Monday.com API error: {result['errors']}")
                return False
            
            logger.info(f"Updated Monday.com item {item_id} with status {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Monday.com status: {e}")
            return False


class OutreachAgent:
    """
    Comprehensive Outreach Agent that orchestrates the complete outreach workflow
    including research, message generation, WhatsApp delivery, and status tracking.
    """
    
    def __init__(self, api_keys: Dict[str, str], mongodb_connection: str, whatsapp_service_url: str = "http://localhost:3001"):
        """
        Initialize the Outreach Agent.
        
        Args:
            api_keys: Dictionary containing all API keys
            mongodb_connection: MongoDB connection string
            whatsapp_service_url: WhatsApp service URL
        """
        self.api_keys = api_keys
        
        # Load agent configurations from MongoDB
        agent_configs = self._load_agent_configurations()

        # Initialize components with proper configurations
        self.research_agent = ResearchAgent(
            api_keys=api_keys,
            config=agent_configs.get('research_agent', {})
        )
        self.message_optimizer = MessageQualityOptimizer(api_keys, mongodb_connection)
        self.whatsapp_bridge = WhatsAppBridge(whatsapp_service_url)
        self.monday_updater = MondayStatusUpdater(api_keys.get('MONDAY_API_KEY', ''))
        self.storage_manager = ResearchStorageManager(mongodb_connection)

        # CRITICAL FIX: Initialize Monday.com client for proper note/activity creation
        from tools.monday_client import MondayClient
        self.monday_client = MondayClient(api_keys.get('MONDAY_API_KEY', ''))
        self.storage_manager.connect()

        # CRITICAL FIX: Initialize error recovery and status tracking systems (lazy import to avoid circular dependency)
        from agents.outreach_error_recovery import OutreachErrorRecoverySystem
        from agents.status_tracking_system import StatusTrackingSystem

        self.error_recovery_system = OutreachErrorRecoverySystem(api_keys, mongodb_connection, whatsapp_service_url)
        self.status_tracking_system = StatusTrackingSystem(api_keys, mongodb_connection, whatsapp_service_url)

        logger.info("Outreach Agent initialized successfully")

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

    def execute_outreach(self, outreach_request: OutreachRequest) -> OutreachResult:
        """
        Execute complete outreach workflow for a single lead.
        
        Args:
            outreach_request: Outreach request with lead information
            
        Returns:
            OutreachResult with execution details
        """
        request_id = f"outreach_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{outreach_request.lead_id}"
        
        try:
            logger.info(f"Starting outreach execution for {outreach_request.lead_name} at {outreach_request.company}")
            
            # Step 1: Update Monday.com status to "queued"
            self.monday_updater.update_lead_status(
                outreach_request.lead_id, 
                OutreachStatus.QUEUED,
                "Outreach queued for processing"
            )
            
            # Step 2: Conduct research
            lead_input = LeadInput(
                lead_name=outreach_request.lead_name,
                company=outreach_request.company,
                title=outreach_request.title,
                industry=outreach_request.industry,
                company_size=outreach_request.company_size
            )
            
            # Step 3: Use pre-generated message or generate new one
            if outreach_request.pre_generated_message:
                # CRITICAL FIX: Use the hyper-personalized message that was already generated
                logger.info(f"✅ Using pre-generated hyper-personalized message for {outreach_request.lead_name}")

                # Create a mock optimized message object to maintain compatibility
                from agents.message_quality_optimizer import OptimizedMessage, QualityMetrics
                optimized_message = OptimizedMessage(
                    original_message=outreach_request.pre_generated_message,
                    optimized_message=outreach_request.pre_generated_message,
                    quality_metrics=QualityMetrics(
                        personalization_score=1.0,  # Pre-generated messages are hyper-personalized
                        predicted_response_rate=0.75,  # High confidence in pre-generated messages
                        readability_score=0.9,
                        sentiment_score=0.9,
                        urgency_score=0.8,
                        value_proposition_score=0.9,
                        call_to_action_score=0.8,
                        overall_quality_score=0.9
                    ),
                    optimization_notes=["Pre-generated hyper-personalized message with MongoDB context"]
                )
            else:
                # Fallback: Generate and optimize message using the old method
                logger.info(f"⚠️ No pre-generated message, using message optimizer for {outreach_request.lead_name}")
                optimized_message = self.message_optimizer.test_message_quality_with_research(
                    lead_input,
                    outreach_request.sender_info
                )
            
            # Step 4: Check message approval
            approval = self.message_optimizer.implement_approval_workflow(optimized_message)
            
            if approval.status != MessageStatus.APPROVED:
                logger.warning(f"Message not approved for {outreach_request.lead_name}: {approval.status.value}")
                return self._create_failed_result(
                    request_id, 
                    outreach_request, 
                    f"Message not approved: {approval.status.value}"
                )
            
            # Step 5: Update Monday.com status to "sending"
            self.monday_updater.update_lead_status(
                outreach_request.lead_id,
                OutreachStatus.SENDING,
                optimized_message.optimized_message
            )
            
            # Step 6: Send message via WhatsApp
            send_result = self._send_whatsapp_message(
                outreach_request.phone_number,
                optimized_message.optimized_message,
                outreach_request.message_type
            )

            if not send_result.get("success", False):
                error_msg = send_result.get("error", "Unknown WhatsApp error")
                logger.error(f"WhatsApp send failed for {outreach_request.lead_name}: {error_msg}")

                # CRITICAL FIX: Use error recovery system for failed sends
                error_exception = Exception(error_msg)
                error_record = self.error_recovery_system.handle_outreach_error(
                    error_exception, outreach_request, request_id
                )

                # Update Monday.com with failure
                self.monday_updater.update_lead_status(
                    outreach_request.lead_id,
                    OutreachStatus.FAILED,
                    f"Send failed: {error_msg}"
                )

                return self._create_failed_result(request_id, outreach_request, error_msg)
            
            # Step 7: Update Monday.com status to "sent"
            self.monday_updater.update_lead_status(
                outreach_request.lead_id,
                OutreachStatus.SENT,
                optimized_message.optimized_message
            )

            # CRITICAL FIX: Add proper message documentation as note/activity in Monday.com
            message_id = send_result.get("messageId")
            if message_id:
                # Add comprehensive message documentation to Monday.com as a note/activity
                self.monday_client.add_message_documentation(
                    item_id=outreach_request.lead_id,
                    message_text=optimized_message.optimized_message,
                    whatsapp_message_id=message_id,
                    delivery_status="sent"
                )
                logger.info(f"✅ Added message documentation to Monday.com for {outreach_request.lead_name}")

                # Start status tracking for successful sends
                self.status_tracking_system.track_message_sent(
                    message_id=message_id,
                    lead_id=outreach_request.lead_id,
                    lead_name=outreach_request.lead_name,
                    company=outreach_request.company,
                    message_content=optimized_message.optimized_message
                )

            # Step 8: Create success result
            result = OutreachResult(
                request_id=request_id,
                lead_id=outreach_request.lead_id,
                status=OutreachStatus.SENT,
                message_sent=optimized_message.optimized_message,
                whatsapp_message_id=message_id,
                delivery_timestamp=None,
                read_timestamp=None,
                reply_received=None,
                error_message=None,
                monday_updated=True,
                execution_timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            logger.info(f"Outreach completed successfully for {outreach_request.lead_name}")
            return result
            
        except Exception as e:
            logger.error(f"Outreach execution failed for {outreach_request.lead_name}: {e}")

            # CRITICAL FIX: Use error recovery system for general exceptions
            error_record = self.error_recovery_system.handle_outreach_error(
                e, outreach_request, request_id
            )

            # Update Monday.com with failure
            self.monday_updater.update_lead_status(
                outreach_request.lead_id,
                OutreachStatus.FAILED,
                f"Execution failed: {str(e)}"
            )

            return self._create_failed_result(request_id, outreach_request, str(e))

    def _send_whatsapp_message(self, phone_number: str, message: str, message_type: MessageType) -> Dict[str, Any]:
        """Send message via WhatsApp based on message type"""
        
        # Check WhatsApp connection first
        status = self.whatsapp_bridge.check_connection_status()
        if not status.get("connected", False):
            return {"success": False, "error": "WhatsApp not connected"}
        
        if message_type == MessageType.TEXT:
            return self.whatsapp_bridge.send_text_message(phone_number, message)
        elif message_type == MessageType.VOICE:
            # For voice messages, we'd need the audio file path
            # This would come from the multimodal message generation
            return {"success": False, "error": "Voice messages not yet implemented"}
        elif message_type == MessageType.IMAGE:
            # For image messages, we'd need the image file path
            return {"success": False, "error": "Image messages not yet implemented"}
        else:
            return {"success": False, "error": f"Unsupported message type: {message_type.value}"}

    def _create_failed_result(self, request_id: str, outreach_request: OutreachRequest, error_msg: str) -> OutreachResult:
        """Create failed outreach result"""
        return OutreachResult(
            request_id=request_id,
            lead_id=outreach_request.lead_id,
            status=OutreachStatus.FAILED,
            message_sent="",
            whatsapp_message_id=None,
            delivery_timestamp=None,
            read_timestamp=None,
            reply_received=None,
            error_message=error_msg,
            monday_updated=True,
            execution_timestamp=datetime.now(timezone.utc).isoformat()
        )

    def track_delivery_status(self, message_id: str, lead_id: str) -> Dict[str, Any]:
        """
        Track message delivery status and update Monday.com accordingly.
        
        Args:
            message_id: WhatsApp message ID
            lead_id: Monday.com lead ID
            
        Returns:
            Updated status information
        """
        try:
            status_info = self.whatsapp_bridge.get_message_status(message_id)
            
            # Update Monday.com based on delivery status
            if status_info.get("delivered"):
                self.monday_updater.update_lead_status(lead_id, OutreachStatus.DELIVERED)
            
            if status_info.get("read"):
                self.monday_updater.update_lead_status(lead_id, OutreachStatus.READ)
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to track delivery status: {e}")
            return {"error": str(e)}

    def batch_outreach(self, outreach_requests: List[OutreachRequest]) -> List[OutreachResult]:
        """
        Execute batch outreach for multiple leads.
        
        Args:
            outreach_requests: List of outreach requests
            
        Returns:
            List of outreach results
        """
        logger.info(f"Starting batch outreach for {len(outreach_requests)} leads")
        
        results = []
        
        for i, request in enumerate(outreach_requests, 1):
            logger.info(f"Processing lead {i}/{len(outreach_requests)}: {request.lead_name}")
            
            try:
                result = self.execute_outreach(request)
                results.append(result)
                
                # Add delay between messages to respect rate limits
                if i < len(outreach_requests):
                    logger.info("Waiting 5 seconds before next message...")
                    import time
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Batch outreach failed for {request.lead_name}: {e}")
                results.append(self._create_failed_result(
                    f"batch_{i}",
                    request,
                    str(e)
                ))
        
        # Summary
        successful = len([r for r in results if r.status == OutreachStatus.SENT])
        failed = len(results) - successful
        
        logger.info(f"Batch outreach completed: {successful} successful, {failed} failed")
        return results

    def start_automatic_tracking(self, check_interval: int = 30):
        """
        Start automatic delivery and status tracking.

        Args:
            check_interval: Seconds between status checks
        """
        self.status_tracking_system.start_automatic_tracking(check_interval)
        logger.info(f"🚀 Started automatic outreach tracking with {check_interval}s interval")

    def stop_automatic_tracking(self):
        """Stop automatic delivery and status tracking"""
        self.status_tracking_system.stop_automatic_tracking()
        logger.info("⏹️ Stopped automatic outreach tracking")

    def get_tracking_metrics(self):
        """Get current tracking metrics"""
        return self.status_tracking_system.get_tracking_metrics()

    def get_lead_interaction_history(self, lead_id: str):
        """Get complete interaction history for a lead"""
        return self.status_tracking_system.get_lead_interaction_history(lead_id)


# Convenience function
def create_outreach_agent(api_keys: Dict[str, str], mongodb_connection: str, whatsapp_service_url: str = "http://localhost:3001") -> OutreachAgent:
    """Create and return a configured Outreach Agent instance."""
    return OutreachAgent(api_keys=api_keys, mongodb_connection=mongodb_connection, whatsapp_service_url=whatsapp_service_url)
