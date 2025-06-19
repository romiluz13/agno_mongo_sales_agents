"""
Test suite for Outreach Error Recovery System

Tests WhatsApp disconnection handling, retry logic with exponential backoff,
message queuing for offline scenarios, and failure recovery.
"""

import os
import sys
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.outreach_error_recovery import (
    OutreachErrorRecoverySystem,
    ConnectionMonitor,
    RetryManager,
    MessageQueue,
    ErrorRecord,
    QueuedMessage,
    ErrorType,
    RetryStrategy,
    create_outreach_error_recovery_system
)
from agents.outreach_agent import OutreachRequest, MessageType, SenderInfo


class TestConnectionMonitor:
    """Test cases for Connection Monitor"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_whatsapp_bridge = Mock()
        self.monitor = ConnectionMonitor(self.mock_whatsapp_bridge, check_interval=1)

    def test_connection_monitor_initialization(self):
        """Test connection monitor initializes correctly"""
        assert self.monitor is not None
        assert self.monitor.whatsapp_bridge == self.mock_whatsapp_bridge
        assert self.monitor.check_interval == 1
        assert self.monitor.is_connected is False
        assert self.monitor.monitoring_active is False

    def test_check_connection_success(self):
        """Test successful connection check"""
        # Mock successful connection
        self.mock_whatsapp_bridge.check_connection_status.return_value = {
            "connected": True
        }
        
        result = self.monitor.check_connection()
        
        assert result is True
        assert self.monitor.is_connected is True
        assert self.monitor.last_check_time is not None

    def test_check_connection_failure(self):
        """Test connection check failure"""
        # Mock connection failure
        self.mock_whatsapp_bridge.check_connection_status.return_value = {
            "connected": False,
            "error": "Connection lost"
        }
        
        result = self.monitor.check_connection()
        
        assert result is False
        assert self.monitor.is_connected is False

    def test_check_connection_exception(self):
        """Test connection check with exception"""
        # Mock exception
        self.mock_whatsapp_bridge.check_connection_status.side_effect = Exception("Network error")
        
        result = self.monitor.check_connection()
        
        assert result is False
        assert self.monitor.is_connected is False

    def test_connection_state_change_callback(self):
        """Test connection state change callbacks"""
        callback_called = []
        
        def test_callback(is_connected):
            callback_called.append(is_connected)
        
        self.monitor.add_connection_callback(test_callback)
        
        # Simulate connection
        self.mock_whatsapp_bridge.check_connection_status.return_value = {"connected": True}
        self.monitor.check_connection()
        
        # Simulate disconnection
        self.mock_whatsapp_bridge.check_connection_status.return_value = {"connected": False}
        self.monitor.check_connection()
        
        assert len(callback_called) == 2
        assert callback_called[0] is True
        assert callback_called[1] is False

    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring"""
        # Start monitoring
        self.monitor.start_monitoring()
        assert self.monitor.monitoring_active is True
        assert self.monitor.monitoring_thread is not None
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        assert self.monitor.monitoring_active is False


class TestRetryManager:
    """Test cases for Retry Manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.retry_manager = RetryManager()

    def test_retry_manager_initialization(self):
        """Test retry manager initializes correctly"""
        assert self.retry_manager is not None
        assert len(self.retry_manager.retry_strategies) > 0
        assert len(self.retry_manager.max_retries) > 0

    def test_should_retry_logic(self):
        """Test retry decision logic"""
        # Should retry for retryable errors
        assert self.retry_manager.should_retry(ErrorType.WHATSAPP_DISCONNECTED, 0) is True
        assert self.retry_manager.should_retry(ErrorType.WHATSAPP_DISCONNECTED, 3) is True
        assert self.retry_manager.should_retry(ErrorType.WHATSAPP_DISCONNECTED, 5) is False
        
        # Should not retry for non-retryable errors
        assert self.retry_manager.should_retry(ErrorType.INVALID_PHONE_NUMBER, 0) is False
        assert self.retry_manager.should_retry(ErrorType.MESSAGE_TOO_LONG, 0) is False

    def test_calculate_retry_delay_exponential(self):
        """Test exponential backoff delay calculation"""
        # Test exponential backoff
        delay1 = self.retry_manager.calculate_retry_delay(ErrorType.WHATSAPP_DISCONNECTED, 1)
        delay2 = self.retry_manager.calculate_retry_delay(ErrorType.WHATSAPP_DISCONNECTED, 2)
        delay3 = self.retry_manager.calculate_retry_delay(ErrorType.WHATSAPP_DISCONNECTED, 3)
        
        # Should increase exponentially (with jitter)
        assert delay1 > 0
        assert delay2 > delay1
        assert delay3 > delay2
        
        # Should be capped at reasonable value (allowing for jitter)
        delay_large = self.retry_manager.calculate_retry_delay(ErrorType.WHATSAPP_DISCONNECTED, 10)
        assert delay_large <= 450  # 300 * 1.5 jitter max

    def test_calculate_retry_delay_linear(self):
        """Test linear backoff delay calculation"""
        # Test linear backoff
        delay1 = self.retry_manager.calculate_retry_delay(ErrorType.WHATSAPP_RATE_LIMITED, 1)
        delay2 = self.retry_manager.calculate_retry_delay(ErrorType.WHATSAPP_RATE_LIMITED, 2)
        
        assert delay1 > 0
        assert delay2 > delay1

    def test_create_error_record(self):
        """Test error record creation"""
        error_record = self.retry_manager.create_error_record(
            ErrorType.WHATSAPP_DISCONNECTED,
            "Connection lost",
            "req_123",
            "lead_456"
        )
        
        assert isinstance(error_record, ErrorRecord)
        assert error_record.error_type == ErrorType.WHATSAPP_DISCONNECTED
        assert error_record.error_message == "Connection lost"
        assert error_record.request_id == "req_123"
        assert error_record.lead_id == "lead_456"
        assert error_record.retry_count == 0
        assert error_record.max_retries > 0


class TestMessageQueue:
    """Test cases for Message Queue"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_storage_manager = Mock()
        self.mock_storage_manager.database = None  # No database for testing
        self.queue = MessageQueue(self.mock_storage_manager)

    def test_message_queue_initialization(self):
        """Test message queue initializes correctly"""
        assert self.queue is not None
        assert self.queue.storage_manager == self.mock_storage_manager
        assert self.queue.get_queue_size() == 0

    def test_enqueue_dequeue_message(self):
        """Test message enqueue and dequeue"""
        # Create test data
        outreach_request = OutreachRequest(
            lead_id="test_lead",
            lead_name="Test Lead",
            company="Test Corp",
            title="CEO",
            industry="Tech",
            company_size="100",
            phone_number="+1234567890",
            message_type=MessageType.TEXT,
            sender_info=SenderInfo("Test", "TestCorp", "Testing")
        )
        
        error_record = ErrorRecord(
            error_id="error_123",
            error_type=ErrorType.WHATSAPP_DISCONNECTED,
            error_message="Test error",
            timestamp=datetime.now(timezone.utc),
            request_id="req_123",
            lead_id="test_lead",
            retry_count=0,
            max_retries=3
        )
        
        # Test enqueue
        result = self.queue.enqueue_message(outreach_request, error_record, priority=1)
        assert result is True
        assert self.queue.get_queue_size() == 1
        
        # Test dequeue
        queued_message = self.queue.dequeue_message()
        assert queued_message is not None
        assert isinstance(queued_message, QueuedMessage)
        assert queued_message.outreach_request.lead_name == "Test Lead"
        assert self.queue.get_queue_size() == 0

    def test_queue_priority_ordering(self):
        """Test queue priority ordering"""
        outreach_request = OutreachRequest(
            lead_id="test_lead",
            lead_name="Test Lead",
            company="Test Corp",
            title="CEO",
            industry="Tech",
            company_size="100",
            phone_number="+1234567890",
            message_type=MessageType.TEXT,
            sender_info=SenderInfo("Test", "TestCorp", "Testing")
        )
        
        error_record = ErrorRecord(
            error_id="error_123",
            error_type=ErrorType.WHATSAPP_DISCONNECTED,
            error_message="Test error",
            timestamp=datetime.now(timezone.utc),
            request_id="req_123",
            lead_id="test_lead",
            retry_count=0,
            max_retries=3
        )
        
        # Enqueue with different priorities
        self.queue.enqueue_message(outreach_request, error_record, priority=3)  # Low
        self.queue.enqueue_message(outreach_request, error_record, priority=1)  # High
        self.queue.enqueue_message(outreach_request, error_record, priority=2)  # Medium
        
        # Should dequeue in priority order (1, 2, 3)
        msg1 = self.queue.dequeue_message()
        msg2 = self.queue.dequeue_message()
        msg3 = self.queue.dequeue_message()
        
        assert msg1.priority == 1
        assert msg2.priority == 2
        assert msg3.priority == 3

    def test_clear_queue(self):
        """Test queue clearing"""
        outreach_request = OutreachRequest(
            lead_id="test_lead",
            lead_name="Test Lead",
            company="Test Corp",
            title="CEO",
            industry="Tech",
            company_size="100",
            phone_number="+1234567890",
            message_type=MessageType.TEXT,
            sender_info=SenderInfo("Test", "TestCorp", "Testing")
        )
        
        error_record = ErrorRecord(
            error_id="error_123",
            error_type=ErrorType.WHATSAPP_DISCONNECTED,
            error_message="Test error",
            timestamp=datetime.now(timezone.utc),
            request_id="req_123",
            lead_id="test_lead",
            retry_count=0,
            max_retries=3
        )
        
        # Add messages
        self.queue.enqueue_message(outreach_request, error_record)
        self.queue.enqueue_message(outreach_request, error_record)
        assert self.queue.get_queue_size() == 2
        
        # Clear queue
        self.queue.clear_queue()
        assert self.queue.get_queue_size() == 0


class TestOutreachErrorRecoverySystem:
    """Test cases for Outreach Error Recovery System"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_keys = {
            'MONDAY_API_KEY': 'test_monday_key'
        }
        self.mongodb_connection = "mongodb://localhost:27017"

    @patch('agents.outreach_error_recovery.ResearchStorageManager')
    @patch('agents.outreach_error_recovery.WhatsAppBridge')
    def test_error_recovery_system_initialization(self, mock_whatsapp, mock_storage):
        """Test error recovery system initializes correctly"""
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_instance.connect.return_value = True
        mock_storage_instance.database = None
        mock_storage.return_value = mock_storage_instance
        
        system = OutreachErrorRecoverySystem(self.api_keys, self.mongodb_connection)
        
        assert system is not None
        assert system.api_keys == self.api_keys
        assert system.connection_monitor is not None
        assert system.retry_manager is not None
        assert system.message_queue is not None

    @patch('agents.outreach_error_recovery.ResearchStorageManager')
    @patch('agents.outreach_error_recovery.WhatsAppBridge')
    def test_error_classification(self, mock_whatsapp, mock_storage):
        """Test error classification logic"""
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_instance.connect.return_value = True
        mock_storage_instance.database = None
        mock_storage.return_value = mock_storage_instance
        
        system = OutreachErrorRecoverySystem(self.api_keys, self.mongodb_connection)
        
        # Test different error types
        assert system._classify_error(Exception("Connection lost")) == ErrorType.WHATSAPP_DISCONNECTED
        assert system._classify_error(Exception("Request timeout")) == ErrorType.WHATSAPP_TIMEOUT
        assert system._classify_error(Exception("Rate limit exceeded")) == ErrorType.WHATSAPP_RATE_LIMITED
        assert system._classify_error(Exception("Invalid phone number")) == ErrorType.INVALID_PHONE_NUMBER
        assert system._classify_error(Exception("Unknown issue")) == ErrorType.UNKNOWN_ERROR

    @patch('agents.outreach_error_recovery.ResearchStorageManager')
    @patch('agents.outreach_error_recovery.WhatsAppBridge')
    def test_handle_outreach_error(self, mock_whatsapp, mock_storage):
        """Test outreach error handling"""
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_instance.connect.return_value = True
        mock_storage_instance.database = None
        mock_storage.return_value = mock_storage_instance
        
        system = OutreachErrorRecoverySystem(self.api_keys, self.mongodb_connection)
        
        # Create test data
        outreach_request = OutreachRequest(
            lead_id="test_lead",
            lead_name="Test Lead",
            company="Test Corp",
            title="CEO",
            industry="Tech",
            company_size="100",
            phone_number="+1234567890",
            message_type=MessageType.TEXT,
            sender_info=SenderInfo("Test", "TestCorp", "Testing")
        )
        
        # Test retryable error
        error = Exception("Connection lost")
        error_record = system.handle_outreach_error(error, outreach_request, "req_123")
        
        assert isinstance(error_record, ErrorRecord)
        assert error_record.error_type == ErrorType.WHATSAPP_DISCONNECTED
        assert error_record.lead_id == "test_lead"
        assert error_record.next_retry_time is not None
        
        # Test non-retryable error
        error = Exception("Invalid phone number")
        error_record = system.handle_outreach_error(error, outreach_request, "req_124")
        
        assert error_record.error_type == ErrorType.INVALID_PHONE_NUMBER
        assert error_record.resolved is True

    @patch('agents.outreach_error_recovery.ResearchStorageManager')
    @patch('agents.outreach_error_recovery.WhatsAppBridge')
    def test_get_error_statistics(self, mock_whatsapp, mock_storage):
        """Test error statistics retrieval"""
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_instance.connect.return_value = True
        mock_storage_instance.database = None
        mock_storage.return_value = mock_storage_instance
        
        system = OutreachErrorRecoverySystem(self.api_keys, self.mongodb_connection)
        
        stats = system.get_error_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_errors' in stats
        assert 'resolved_errors' in stats
        assert 'pending_errors' in stats
        assert 'queued_messages' in stats
        assert 'error_types' in stats
        assert 'connection_status' in stats

    def test_create_error_recovery_system_function(self):
        """Test convenience function for creating error recovery system"""
        with patch('agents.outreach_error_recovery.ResearchStorageManager'), \
             patch('agents.outreach_error_recovery.WhatsAppBridge'):
            
            system = create_outreach_error_recovery_system(self.api_keys, self.mongodb_connection)
            assert isinstance(system, OutreachErrorRecoverySystem)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
