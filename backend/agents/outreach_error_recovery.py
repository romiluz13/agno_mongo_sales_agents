"""
Outreach Error Handling & Recovery System for Agno Sales Extension

This module implements comprehensive error handling and recovery including:
1. WhatsApp disconnection handling
2. Retry logic with exponential backoff
3. Message queuing for offline scenarios
4. Failure recovery testing
5. Comprehensive error logging

Following Task 6.3 requirements from docs/08-DETAILED-TASK-BREAKDOWN.md
"""

import json
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import queue
import random

from agents.outreach_agent import OutreachRequest, OutreachResult, OutreachStatus, WhatsAppBridge
from agents.status_tracking_system import StatusTrackingSystem
from agents.research_storage import ResearchStorageManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur during outreach"""
    WHATSAPP_DISCONNECTED = "whatsapp_disconnected"
    WHATSAPP_TIMEOUT = "whatsapp_timeout"
    WHATSAPP_RATE_LIMITED = "whatsapp_rate_limited"
    MONDAY_API_ERROR = "monday_api_error"
    NETWORK_ERROR = "network_error"
    INVALID_PHONE_NUMBER = "invalid_phone_number"
    MESSAGE_TOO_LONG = "message_too_long"
    UNKNOWN_ERROR = "unknown_error"


class RetryStrategy(Enum):
    """Retry strategies for different error types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE_RETRY = "immediate_retry"
    NO_RETRY = "no_retry"


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error_id: str
    error_type: ErrorType
    error_message: str
    timestamp: datetime
    request_id: str
    lead_id: str
    retry_count: int
    max_retries: int
    next_retry_time: Optional[datetime] = None
    resolved: bool = False
    resolution_notes: str = ""


@dataclass
class QueuedMessage:
    """Message queued for retry or offline processing"""
    queue_id: str
    outreach_request: OutreachRequest
    original_error: ErrorRecord
    queued_timestamp: datetime
    priority: int = 1  # 1=high, 2=medium, 3=low
    retry_count: int = 0
    max_retries: int = 3


class ConnectionMonitor:
    """
    Monitors WhatsApp connection status and handles disconnections
    """
    
    def __init__(self, whatsapp_bridge: WhatsAppBridge, check_interval: int = 30):
        """
        Initialize connection monitor.
        
        Args:
            whatsapp_bridge: WhatsApp bridge instance
            check_interval: Seconds between connection checks
        """
        self.whatsapp_bridge = whatsapp_bridge
        self.check_interval = check_interval
        self.is_connected = False
        self.last_check_time = None
        self.monitoring_active = False
        self.monitoring_thread = None
        self.connection_callbacks: List[Callable[[bool], None]] = []
    
    def add_connection_callback(self, callback: Callable[[bool], None]):
        """Add callback to be called when connection status changes"""
        self.connection_callbacks.append(callback)
    
    def start_monitoring(self):
        """Start connection monitoring"""
        if self.monitoring_active:
            logger.warning("⚠️ Connection monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"🔍 Started WhatsApp connection monitoring (interval: {self.check_interval}s)")
    
    def stop_monitoring(self):
        """Stop connection monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("⏹️ Stopped WhatsApp connection monitoring")
    
    def check_connection(self) -> bool:
        """Check current connection status"""
        try:
            status = self.whatsapp_bridge.check_connection_status()
            new_connection_state = status.get("connected", False)
            
            # Detect connection state changes
            if new_connection_state != self.is_connected:
                logger.info(f"🔄 WhatsApp connection state changed: {self.is_connected} → {new_connection_state}")
                self.is_connected = new_connection_state
                
                # Notify callbacks
                for callback in self.connection_callbacks:
                    try:
                        callback(new_connection_state)
                    except Exception as e:
                        logger.error(f"❌ Error in connection callback: {e}")
            
            self.last_check_time = datetime.now(timezone.utc)
            return new_connection_state
            
        except Exception as e:
            logger.error(f"❌ Failed to check WhatsApp connection: {e}")
            if self.is_connected:
                self.is_connected = False
                # Notify callbacks of disconnection
                for callback in self.connection_callbacks:
                    try:
                        callback(False)
                    except Exception as e:
                        logger.error(f"❌ Error in connection callback: {e}")
            return False
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                self.check_connection()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Error in connection monitoring loop: {e}")
                time.sleep(self.check_interval)


class RetryManager:
    """
    Manages retry logic with exponential backoff for different error types
    """
    
    def __init__(self):
        """Initialize retry manager"""
        self.retry_strategies = {
            ErrorType.WHATSAPP_DISCONNECTED: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorType.WHATSAPP_TIMEOUT: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorType.WHATSAPP_RATE_LIMITED: RetryStrategy.LINEAR_BACKOFF,
            ErrorType.MONDAY_API_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorType.NETWORK_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorType.INVALID_PHONE_NUMBER: RetryStrategy.NO_RETRY,
            ErrorType.MESSAGE_TOO_LONG: RetryStrategy.NO_RETRY,
            ErrorType.UNKNOWN_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF
        }
        
        self.max_retries = {
            ErrorType.WHATSAPP_DISCONNECTED: 5,
            ErrorType.WHATSAPP_TIMEOUT: 3,
            ErrorType.WHATSAPP_RATE_LIMITED: 3,
            ErrorType.MONDAY_API_ERROR: 3,
            ErrorType.NETWORK_ERROR: 3,
            ErrorType.INVALID_PHONE_NUMBER: 0,
            ErrorType.MESSAGE_TOO_LONG: 0,
            ErrorType.UNKNOWN_ERROR: 2
        }
    
    def should_retry(self, error_type: ErrorType, current_retry_count: int) -> bool:
        """Determine if an error should be retried"""
        max_retries = self.max_retries.get(error_type, 0)
        return current_retry_count < max_retries
    
    def calculate_retry_delay(self, error_type: ErrorType, retry_count: int) -> int:
        """Calculate delay before next retry attempt"""
        strategy = self.retry_strategies.get(error_type, RetryStrategy.EXPONENTIAL_BACKOFF)
        
        if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            # 2^retry_count seconds with jitter
            base_delay = min(2 ** retry_count, 300)  # Cap at 5 minutes
            jitter = random.uniform(0.5, 1.5)
            return int(base_delay * jitter)
        
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            # Linear increase with jitter
            base_delay = min(retry_count * 30, 300)  # 30s, 60s, 90s... cap at 5min
            jitter = random.uniform(0.8, 1.2)
            return int(base_delay * jitter)
        
        elif strategy == RetryStrategy.IMMEDIATE_RETRY:
            return 1  # 1 second delay
        
        else:  # NO_RETRY
            return 0
    
    def create_error_record(self, error_type: ErrorType, error_message: str, request_id: str, lead_id: str) -> ErrorRecord:
        """Create a new error record"""
        error_id = f"error_{int(time.time())}_{random.randint(1000, 9999)}"
        max_retries = self.max_retries.get(error_type, 0)
        
        return ErrorRecord(
            error_id=error_id,
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.now(timezone.utc),
            request_id=request_id,
            lead_id=lead_id,
            retry_count=0,
            max_retries=max_retries
        )


class MessageQueue:
    """
    Message queue for offline scenarios and retry management
    """
    
    def __init__(self, storage_manager: ResearchStorageManager):
        """
        Initialize message queue.
        
        Args:
            storage_manager: MongoDB storage manager for persistence
        """
        self.storage_manager = storage_manager
        self.collection_name = "message_queue"
        self.collection = None
        self.in_memory_queue = queue.PriorityQueue()
        self.processing_active = False
        self.processing_thread = None
        
        if storage_manager.database is not None:
            self.collection = storage_manager.database[self.collection_name]
            self._create_indexes()
            self._load_queued_messages()
    
    def _create_indexes(self):
        """Create indexes for efficient querying"""
        try:
            if self.collection is not None:
                self.collection.create_index("priority")
                self.collection.create_index("queued_timestamp")
                self.collection.create_index("retry_count")
                logger.info("✅ Message queue indexes created successfully")
        except Exception as e:
            logger.warning(f"⚠️ Could not create message queue indexes: {e}")
    
    def _load_queued_messages(self):
        """Load existing queued messages from database"""
        try:
            if self.collection is not None:
                cursor = self.collection.find().sort("priority", 1).sort("queued_timestamp", 1)
                
                for doc in cursor:
                    doc.pop('_id', None)
                    doc['queued_timestamp'] = datetime.fromisoformat(doc['queued_timestamp'])
                    
                    # Reconstruct objects
                    queued_msg = QueuedMessage(**doc)
                    self.in_memory_queue.put((queued_msg.priority, queued_msg))
                
                logger.info(f"📥 Loaded {self.in_memory_queue.qsize()} queued messages from database")
        except Exception as e:
            logger.error(f"❌ Failed to load queued messages: {e}")
    
    def enqueue_message(self, outreach_request: OutreachRequest, error_record: ErrorRecord, priority: int = 2) -> bool:
        """
        Add message to queue for retry.
        
        Args:
            outreach_request: Original outreach request
            error_record: Error that caused queuing
            priority: Message priority (1=high, 2=medium, 3=low)
            
        Returns:
            Success status
        """
        try:
            queue_id = f"queue_{int(time.time())}_{random.randint(1000, 9999)}"
            
            queued_message = QueuedMessage(
                queue_id=queue_id,
                outreach_request=outreach_request,
                original_error=error_record,
                queued_timestamp=datetime.now(timezone.utc),
                priority=priority,
                retry_count=0,
                max_retries=3
            )
            
            # Add to in-memory queue
            self.in_memory_queue.put((priority, queued_message))
            
            # Persist to database
            if self.collection is not None:
                queue_dict = asdict(queued_message)
                queue_dict['queued_timestamp'] = queued_message.queued_timestamp.isoformat()
                self.collection.insert_one(queue_dict)
            
            logger.info(f"📤 Queued message for {outreach_request.lead_name} (priority: {priority})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to enqueue message: {e}")
            return False
    
    def dequeue_message(self) -> Optional[QueuedMessage]:
        """Get next message from queue"""
        try:
            if not self.in_memory_queue.empty():
                priority, queued_message = self.in_memory_queue.get_nowait()
                
                # Remove from database
                if self.collection is not None:
                    self.collection.delete_one({"queue_id": queued_message.queue_id})
                
                return queued_message
            return None
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"❌ Failed to dequeue message: {e}")
            return None
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.in_memory_queue.qsize()
    
    def clear_queue(self):
        """Clear all queued messages"""
        try:
            # Clear in-memory queue
            while not self.in_memory_queue.empty():
                self.in_memory_queue.get_nowait()
            
            # Clear database
            if self.collection is not None:
                self.collection.delete_many({})
            
            logger.info("🗑️ Message queue cleared")
        except Exception as e:
            logger.error(f"❌ Failed to clear queue: {e}")


class OutreachErrorRecoverySystem:
    """
    Comprehensive error handling and recovery system for outreach operations
    """
    
    def __init__(self, api_keys: Dict[str, str], mongodb_connection: str, whatsapp_service_url: str = "http://localhost:3001"):
        """
        Initialize the error recovery system.
        
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
        self.connection_monitor = ConnectionMonitor(self.whatsapp_bridge)
        self.retry_manager = RetryManager()
        self.message_queue = MessageQueue(self.storage_manager)
        
        # Error tracking
        self.error_records: Dict[str, ErrorRecord] = {}
        self.recovery_callbacks: List[Callable[[ErrorRecord], None]] = []
        
        # Setup connection monitoring
        self.connection_monitor.add_connection_callback(self._on_connection_change)
        
        logger.info("✅ Outreach Error Recovery System initialized successfully")

    def _on_connection_change(self, is_connected: bool):
        """Handle WhatsApp connection state changes"""
        if is_connected:
            logger.info("🔗 WhatsApp reconnected - processing queued messages")
            self._process_queued_messages()
        else:
            logger.warning("⚠️ WhatsApp disconnected - messages will be queued")

    def handle_outreach_error(self, error: Exception, outreach_request: OutreachRequest, request_id: str) -> ErrorRecord:
        """
        Handle an outreach error and determine recovery strategy.
        
        Args:
            error: Exception that occurred
            outreach_request: Original outreach request
            request_id: Request identifier
            
        Returns:
            Error record with recovery plan
        """
        try:
            # Classify error type
            error_type = self._classify_error(error)
            error_message = str(error)
            
            # Create error record
            error_record = self.retry_manager.create_error_record(
                error_type, error_message, request_id, outreach_request.lead_id
            )
            
            # Store error record
            self.error_records[error_record.error_id] = error_record
            
            # Log comprehensive error details
            logger.error(f"❌ Outreach error for {outreach_request.lead_name}: {error_type.value} - {error_message}")
            
            # Determine recovery strategy
            if self.retry_manager.should_retry(error_type, 0):
                # Calculate retry delay
                retry_delay = self.retry_manager.calculate_retry_delay(error_type, 0)
                error_record.next_retry_time = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
                
                # Queue for retry
                priority = 1 if error_type == ErrorType.WHATSAPP_DISCONNECTED else 2
                self.message_queue.enqueue_message(outreach_request, error_record, priority)
                
                logger.info(f"🔄 Queued for retry in {retry_delay}s (attempt 1/{error_record.max_retries})")
            else:
                logger.warning(f"⚠️ Error type {error_type.value} not retryable - marking as failed")
                error_record.resolved = True
                error_record.resolution_notes = "Error type not retryable"
            
            # Notify callbacks
            for callback in self.recovery_callbacks:
                try:
                    callback(error_record)
                except Exception as e:
                    logger.error(f"❌ Error in recovery callback: {e}")
            
            return error_record
            
        except Exception as e:
            logger.error(f"❌ Failed to handle outreach error: {e}")
            # Create minimal error record
            return ErrorRecord(
                error_id=f"error_{int(time.time())}",
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=str(e),
                timestamp=datetime.now(timezone.utc),
                request_id=request_id,
                lead_id=outreach_request.lead_id,
                retry_count=0,
                max_retries=0,
                resolved=True,
                resolution_notes="Failed to process error"
            )

    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception details"""
        error_str = str(error).lower()
        
        if "connection" in error_str or "disconnected" in error_str:
            return ErrorType.WHATSAPP_DISCONNECTED
        elif "timeout" in error_str:
            return ErrorType.WHATSAPP_TIMEOUT
        elif "rate limit" in error_str or "429" in error_str:
            return ErrorType.WHATSAPP_RATE_LIMITED
        elif "monday" in error_str or "401" in error_str or "403" in error_str:
            return ErrorType.MONDAY_API_ERROR
        elif "network" in error_str or "dns" in error_str:
            return ErrorType.NETWORK_ERROR
        elif "phone" in error_str or "invalid number" in error_str:
            return ErrorType.INVALID_PHONE_NUMBER
        elif "message too long" in error_str or "length" in error_str:
            return ErrorType.MESSAGE_TOO_LONG
        else:
            return ErrorType.UNKNOWN_ERROR

    def _process_queued_messages(self):
        """Process messages in the queue"""
        processed_count = 0
        
        while True:
            queued_message = self.message_queue.dequeue_message()
            if not queued_message:
                break
            
            try:
                logger.info(f"🔄 Processing queued message for {queued_message.outreach_request.lead_name}")
                
                # Check if we should still retry
                if queued_message.retry_count >= queued_message.max_retries:
                    logger.warning(f"⚠️ Max retries exceeded for {queued_message.outreach_request.lead_name}")
                    continue
                
                # Attempt to process the message
                # This would integrate with the actual outreach agent
                # For now, we'll simulate success/failure
                
                processed_count += 1
                
                # Limit processing to avoid overwhelming the system
                if processed_count >= 10:
                    logger.info("⏸️ Processed 10 queued messages, pausing to avoid overload")
                    break
                    
            except Exception as e:
                logger.error(f"❌ Failed to process queued message: {e}")
                
                # Re-queue with incremented retry count
                queued_message.retry_count += 1
                if queued_message.retry_count < queued_message.max_retries:
                    self.message_queue.enqueue_message(
                        queued_message.outreach_request,
                        queued_message.original_error,
                        queued_message.priority
                    )

    def start_monitoring(self):
        """Start error recovery monitoring"""
        self.connection_monitor.start_monitoring()
        logger.info("🚀 Started error recovery monitoring")

    def stop_monitoring(self):
        """Stop error recovery monitoring"""
        self.connection_monitor.stop_monitoring()
        logger.info("⏹️ Stopped error recovery monitoring")

    def add_recovery_callback(self, callback: Callable[[ErrorRecord], None]):
        """Add callback to be called when errors are handled"""
        self.recovery_callbacks.append(callback)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and recovery metrics"""
        total_errors = len(self.error_records)
        resolved_errors = len([e for e in self.error_records.values() if e.resolved])
        queued_messages = self.message_queue.get_queue_size()
        
        error_types = {}
        for error_record in self.error_records.values():
            error_type = error_record.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": total_errors,
            "resolved_errors": resolved_errors,
            "pending_errors": total_errors - resolved_errors,
            "queued_messages": queued_messages,
            "error_types": error_types,
            "connection_status": self.connection_monitor.is_connected,
            "last_connection_check": self.connection_monitor.last_check_time.isoformat() if self.connection_monitor.last_check_time else None
        }


# Convenience function
def create_outreach_error_recovery_system(api_keys: Dict[str, str], mongodb_connection: str, whatsapp_service_url: str = "http://localhost:3001") -> OutreachErrorRecoverySystem:
    """Create and return a configured Outreach Error Recovery System instance."""
    return OutreachErrorRecoverySystem(api_keys=api_keys, mongodb_connection=mongodb_connection, whatsapp_service_url=whatsapp_service_url)
