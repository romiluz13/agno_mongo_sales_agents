"""
Status Tracking System Implementation for Agno Sales Extension

This module implements comprehensive status tracking including delivery confirmation,
read receipts monitoring, automatic Monday.com updates, and interaction history storage.

Following Task 6.2 requirements from docs/08-DETAILED-TASK-BREAKDOWN.md
"""

import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

from agents.outreach_agent import OutreachStatus, WhatsAppBridge, MondayStatusUpdater
from agents.research_storage import ResearchStorageManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Types of interactions to track"""
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"
    REPLY_RECEIVED = "reply_received"
    STATUS_UPDATE = "status_update"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class InteractionRecord:
    """Individual interaction record for history storage"""
    interaction_id: str
    lead_id: str
    lead_name: str
    company: str
    interaction_type: InteractionType
    timestamp: datetime
    details: Dict[str, Any]
    whatsapp_message_id: Optional[str] = None
    monday_item_id: Optional[str] = None
    status_before: Optional[str] = None
    status_after: Optional[str] = None


@dataclass
class DeliveryConfirmation:
    """Delivery confirmation tracking data"""
    message_id: str
    lead_id: str
    sent_timestamp: datetime
    delivered_timestamp: Optional[datetime] = None
    read_timestamp: Optional[datetime] = None
    reply_timestamp: Optional[datetime] = None
    delivery_status: OutreachStatus = OutreachStatus.SENT
    confirmation_attempts: int = 0
    last_check_timestamp: Optional[datetime] = None


@dataclass
class StatusTrackingMetrics:
    """Status tracking performance metrics"""
    total_messages_tracked: int
    delivery_confirmations: int
    read_receipts: int
    replies_received: int
    monday_updates_successful: int
    monday_updates_failed: int
    average_delivery_time: Optional[float] = None
    average_read_time: Optional[float] = None


class InteractionHistoryManager:
    """
    Manages interaction history storage in MongoDB with comprehensive tracking
    """
    
    def __init__(self, storage_manager: ResearchStorageManager):
        """
        Initialize interaction history manager.
        
        Args:
            storage_manager: MongoDB storage manager instance
        """
        self.storage_manager = storage_manager
        self.collection_name = "interaction_history"
        self.collection = None
        
        if storage_manager.database is not None:
            self.collection = storage_manager.database[self.collection_name]
            self._create_indexes()
    
    def _create_indexes(self):
        """Create indexes for efficient querying"""
        try:
            if self.collection is not None:
                # Create indexes for common queries
                self.collection.create_index("lead_id")
                self.collection.create_index("interaction_type")
                self.collection.create_index("timestamp")
                self.collection.create_index("whatsapp_message_id")
                self.collection.create_index([("lead_id", 1), ("timestamp", -1)])

                logger.info("✅ Interaction history indexes created successfully")
        except Exception as e:
            logger.warning(f"⚠️ Could not create interaction history indexes: {e}")
    
    def record_interaction(self, interaction: InteractionRecord) -> bool:
        """
        Record an interaction in the history.
        
        Args:
            interaction: InteractionRecord to store
            
        Returns:
            Success status
        """
        try:
            if self.collection is None:
                logger.error("Database collection not available")
                return False
            
            # Convert to dict for storage
            interaction_dict = asdict(interaction)
            interaction_dict['timestamp'] = interaction.timestamp.isoformat()
            interaction_dict['interaction_type'] = interaction.interaction_type.value  # Convert enum to string
            
            # Store in MongoDB
            result = self.collection.insert_one(interaction_dict)
            
            if result.inserted_id:
                logger.info(f"✅ Interaction recorded: {interaction.interaction_type.value} for {interaction.lead_name}")
                return True
            else:
                logger.error(f"❌ Failed to record interaction for {interaction.lead_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to record interaction: {e}")
            return False
    
    def get_lead_history(self, lead_id: str, limit: int = 50) -> List[InteractionRecord]:
        """
        Get interaction history for a specific lead.
        
        Args:
            lead_id: Lead identifier
            limit: Maximum number of records to return
            
        Returns:
            List of interaction records
        """
        try:
            if self.collection is None:
                return []
            
            cursor = self.collection.find(
                {"lead_id": lead_id}
            ).sort("timestamp", -1).limit(limit)
            
            interactions = []
            for doc in cursor:
                doc.pop('_id', None)  # Remove MongoDB _id
                doc['timestamp'] = datetime.fromisoformat(doc['timestamp'])
                doc['interaction_type'] = InteractionType(doc['interaction_type'])
                interactions.append(InteractionRecord(**doc))
            
            return interactions
            
        except Exception as e:
            logger.error(f"❌ Failed to get lead history: {e}")
            return []
    
    def get_recent_interactions(self, hours: int = 24) -> List[InteractionRecord]:
        """
        Get recent interactions within specified hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent interaction records
        """
        try:
            if self.collection is None:
                return []
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            cursor = self.collection.find(
                {"timestamp": {"$gte": cutoff_time.isoformat()}}
            ).sort("timestamp", -1)
            
            interactions = []
            for doc in cursor:
                doc.pop('_id', None)
                doc['timestamp'] = datetime.fromisoformat(doc['timestamp'])
                doc['interaction_type'] = InteractionType(doc['interaction_type'])
                interactions.append(InteractionRecord(**doc))
            
            return interactions
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent interactions: {e}")
            return []


class DeliveryTracker:
    """
    Tracks message delivery confirmations and read receipts
    """
    
    def __init__(self, whatsapp_bridge: WhatsAppBridge):
        """
        Initialize delivery tracker.
        
        Args:
            whatsapp_bridge: WhatsApp bridge instance
        """
        self.whatsapp_bridge = whatsapp_bridge
        self.pending_confirmations: Dict[str, DeliveryConfirmation] = {}
        self.tracking_active = False
        self.tracking_thread = None
    
    def add_message_for_tracking(self, message_id: str, lead_id: str) -> bool:
        """
        Add a message for delivery tracking.
        
        Args:
            message_id: WhatsApp message ID
            lead_id: Lead identifier
            
        Returns:
            Success status
        """
        try:
            confirmation = DeliveryConfirmation(
                message_id=message_id,
                lead_id=lead_id,
                sent_timestamp=datetime.now(timezone.utc),
                delivery_status=OutreachStatus.SENT
            )
            
            self.pending_confirmations[message_id] = confirmation
            logger.info(f"✅ Added message {message_id} for delivery tracking")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add message for tracking: {e}")
            return False
    
    def check_delivery_status(self, message_id: str) -> Optional[DeliveryConfirmation]:
        """
        Check delivery status for a specific message.
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            Updated delivery confirmation or None
        """
        try:
            if message_id not in self.pending_confirmations:
                return None
            
            confirmation = self.pending_confirmations[message_id]
            confirmation.confirmation_attempts += 1
            confirmation.last_check_timestamp = datetime.now(timezone.utc)
            
            # Get status from WhatsApp
            status_info = self.whatsapp_bridge.get_message_status(message_id)
            
            if status_info.get("error"):
                logger.warning(f"⚠️ Error checking status for {message_id}: {status_info['error']}")
                return confirmation
            
            # Update delivery status
            current_time = datetime.now(timezone.utc)
            
            if status_info.get("delivered") and not confirmation.delivered_timestamp:
                confirmation.delivered_timestamp = current_time
                confirmation.delivery_status = OutreachStatus.DELIVERED
                logger.info(f"📬 Message {message_id} delivered")
            
            if status_info.get("read") and not confirmation.read_timestamp:
                confirmation.read_timestamp = current_time
                confirmation.delivery_status = OutreachStatus.READ
                logger.info(f"👁️ Message {message_id} read")
            
            # Check for replies (this would need to be implemented in WhatsApp bridge)
            if status_info.get("replied") and not confirmation.reply_timestamp:
                confirmation.reply_timestamp = current_time
                confirmation.delivery_status = OutreachStatus.REPLIED
                logger.info(f"💬 Reply received for message {message_id}")
            
            return confirmation
            
        except Exception as e:
            logger.error(f"❌ Failed to check delivery status: {e}")
            return None
    
    def start_tracking(self, check_interval: int = 30):
        """
        Start background delivery tracking.
        
        Args:
            check_interval: Seconds between status checks
        """
        if self.tracking_active:
            logger.warning("⚠️ Delivery tracking already active")
            return
        
        self.tracking_active = True
        self.tracking_thread = threading.Thread(
            target=self._tracking_loop,
            args=(check_interval,),
            daemon=True
        )
        self.tracking_thread.start()
        logger.info(f"🔄 Started delivery tracking with {check_interval}s interval")
    
    def stop_tracking(self):
        """Stop background delivery tracking"""
        self.tracking_active = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=5)
        logger.info("⏹️ Stopped delivery tracking")
    
    def _tracking_loop(self, check_interval: int):
        """Background tracking loop"""
        while self.tracking_active:
            try:
                # Check all pending confirmations
                for message_id in list(self.pending_confirmations.keys()):
                    confirmation = self.check_delivery_status(message_id)
                    
                    # Remove from tracking if delivered/read or too old
                    if confirmation:
                        age_hours = (datetime.now(timezone.utc) - confirmation.sent_timestamp).total_seconds() / 3600
                        
                        if (confirmation.delivery_status in [OutreachStatus.READ, OutreachStatus.REPLIED] or 
                            age_hours > 48 or  # Stop tracking after 48 hours
                            confirmation.confirmation_attempts > 100):  # Max attempts
                            
                            logger.info(f"📋 Removing {message_id} from tracking (status: {confirmation.delivery_status.value})")
                            del self.pending_confirmations[message_id]
                
                # Sleep between checks
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in tracking loop: {e}")
                time.sleep(check_interval)


class StatusTrackingSystem:
    """
    Comprehensive status tracking system that coordinates delivery tracking,
    Monday.com updates, and interaction history storage.
    """
    
    def __init__(self, api_keys: Dict[str, str], mongodb_connection: str, whatsapp_service_url: str = "http://localhost:3001"):
        """
        Initialize the status tracking system.
        
        Args:
            api_keys: Dictionary containing API keys
            mongodb_connection: MongoDB connection string
            whatsapp_service_url: WhatsApp service URL
        """
        self.api_keys = api_keys
        
        # Initialize components
        self.storage_manager = ResearchStorageManager(mongodb_connection)
        self.storage_manager.connect()
        
        self.whatsapp_bridge = WhatsAppBridge(whatsapp_service_url)
        self.monday_updater = MondayStatusUpdater(api_keys.get('MONDAY_API_KEY', ''))
        
        self.history_manager = InteractionHistoryManager(self.storage_manager)
        self.delivery_tracker = DeliveryTracker(self.whatsapp_bridge)
        
        # Metrics tracking
        self.metrics = StatusTrackingMetrics(
            total_messages_tracked=0,
            delivery_confirmations=0,
            read_receipts=0,
            replies_received=0,
            monday_updates_successful=0,
            monday_updates_failed=0
        )
        
        logger.info("✅ Status Tracking System initialized successfully")

    def track_message_sent(self, message_id: str, lead_id: str, lead_name: str, company: str, message_content: str) -> bool:
        """
        Start tracking a sent message.
        
        Args:
            message_id: WhatsApp message ID
            lead_id: Lead identifier
            lead_name: Lead name
            company: Company name
            message_content: Message content
            
        Returns:
            Success status
        """
        try:
            # Record interaction
            interaction = InteractionRecord(
                interaction_id=f"sent_{message_id}_{int(time.time())}",
                lead_id=lead_id,
                lead_name=lead_name,
                company=company,
                interaction_type=InteractionType.MESSAGE_SENT,
                timestamp=datetime.now(timezone.utc),
                details={
                    "message_content": message_content[:200],  # Truncate for storage
                    "message_id": message_id
                },
                whatsapp_message_id=message_id,
                monday_item_id=lead_id,
                status_before="queued",
                status_after="sent"
            )
            
            # Store interaction history
            history_success = self.history_manager.record_interaction(interaction)
            
            # Add to delivery tracking
            tracking_success = self.delivery_tracker.add_message_for_tracking(message_id, lead_id)
            
            # Update metrics
            if tracking_success:
                self.metrics.total_messages_tracked += 1
            
            logger.info(f"📤 Started tracking message {message_id} for {lead_name}")
            return history_success and tracking_success
            
        except Exception as e:
            logger.error(f"❌ Failed to start message tracking: {e}")
            return False

    def update_delivery_status(self, message_id: str, new_status: OutreachStatus) -> bool:
        """
        Update delivery status and trigger appropriate actions.
        
        Args:
            message_id: WhatsApp message ID
            new_status: New delivery status
            
        Returns:
            Success status
        """
        try:
            # Get delivery confirmation
            confirmation = self.delivery_tracker.check_delivery_status(message_id)
            if not confirmation:
                logger.warning(f"⚠️ No tracking record found for message {message_id}")
                return False
            
            # Update Monday.com status
            monday_success = self.monday_updater.update_lead_status(
                confirmation.lead_id,
                new_status,
                f"Message status: {new_status.value}"
            )
            
            # Record interaction
            interaction_type = {
                OutreachStatus.DELIVERED: InteractionType.MESSAGE_DELIVERED,
                OutreachStatus.READ: InteractionType.MESSAGE_READ,
                OutreachStatus.REPLIED: InteractionType.REPLY_RECEIVED
            }.get(new_status, InteractionType.STATUS_UPDATE)
            
            interaction = InteractionRecord(
                interaction_id=f"status_{message_id}_{int(time.time())}",
                lead_id=confirmation.lead_id,
                lead_name="",  # Would need to be passed or looked up
                company="",    # Would need to be passed or looked up
                interaction_type=interaction_type,
                timestamp=datetime.now(timezone.utc),
                details={
                    "previous_status": confirmation.delivery_status.value,
                    "new_status": new_status.value,
                    "message_id": message_id
                },
                whatsapp_message_id=message_id,
                monday_item_id=confirmation.lead_id,
                status_before=confirmation.delivery_status.value,
                status_after=new_status.value
            )
            
            history_success = self.history_manager.record_interaction(interaction)
            
            # Update metrics
            if monday_success:
                self.metrics.monday_updates_successful += 1
            else:
                self.metrics.monday_updates_failed += 1
            
            if new_status == OutreachStatus.DELIVERED:
                self.metrics.delivery_confirmations += 1
            elif new_status == OutreachStatus.READ:
                self.metrics.read_receipts += 1
            elif new_status == OutreachStatus.REPLIED:
                self.metrics.replies_received += 1
            
            logger.info(f"📊 Updated status for {message_id}: {new_status.value}")
            return monday_success and history_success
            
        except Exception as e:
            logger.error(f"❌ Failed to update delivery status: {e}")
            return False

    def start_automatic_tracking(self, check_interval: int = 30):
        """
        Start automatic status tracking.
        
        Args:
            check_interval: Seconds between status checks
        """
        self.delivery_tracker.start_tracking(check_interval)
        logger.info(f"🚀 Started automatic status tracking")

    def stop_automatic_tracking(self):
        """Stop automatic status tracking"""
        self.delivery_tracker.stop_tracking()
        logger.info("⏹️ Stopped automatic status tracking")

    def get_tracking_metrics(self) -> StatusTrackingMetrics:
        """Get current tracking metrics"""
        return self.metrics

    def get_lead_interaction_history(self, lead_id: str) -> List[InteractionRecord]:
        """Get complete interaction history for a lead"""
        return self.history_manager.get_lead_history(lead_id)

    def get_recent_activity(self, hours: int = 24) -> List[InteractionRecord]:
        """Get recent activity across all leads"""
        return self.history_manager.get_recent_interactions(hours)


# Convenience function
def create_status_tracking_system(api_keys: Dict[str, str], mongodb_connection: str, whatsapp_service_url: str = "http://localhost:3001") -> StatusTrackingSystem:
    """Create and return a configured Status Tracking System instance."""
    return StatusTrackingSystem(api_keys=api_keys, mongodb_connection=mongodb_connection, whatsapp_service_url=whatsapp_service_url)
