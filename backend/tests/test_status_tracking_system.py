"""
Test suite for Status Tracking System

Tests delivery confirmation, read receipts tracking, automatic Monday.com updates,
and interaction history storage functionality.
"""

import os
import sys
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.status_tracking_system import (
    StatusTrackingSystem,
    InteractionHistoryManager,
    DeliveryTracker,
    InteractionRecord,
    DeliveryConfirmation,
    InteractionType,
    StatusTrackingMetrics,
    create_status_tracking_system
)
from agents.outreach_agent import OutreachStatus


class TestInteractionHistoryManager:
    """Test cases for Interaction History Manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_storage_manager = Mock()
        self.mock_collection = Mock()
        self.mock_storage_manager.database = {"interaction_history": self.mock_collection}
        
        self.sample_interaction = InteractionRecord(
            interaction_id="test_123",
            lead_id="lead_456",
            lead_name="John Doe",
            company="Acme Corp",
            interaction_type=InteractionType.MESSAGE_SENT,
            timestamp=datetime.now(timezone.utc),
            details={"message_content": "Test message"},
            whatsapp_message_id="wa_123",
            monday_item_id="monday_456"
        )

    def test_history_manager_initialization(self):
        """Test history manager initializes correctly"""
        manager = InteractionHistoryManager(self.mock_storage_manager)
        
        assert manager is not None
        assert manager.storage_manager == self.mock_storage_manager
        assert manager.collection_name == "interaction_history"

    def test_record_interaction_success(self):
        """Test successful interaction recording"""
        manager = InteractionHistoryManager(self.mock_storage_manager)
        manager.collection = self.mock_collection
        
        # Mock successful insert
        mock_result = Mock()
        mock_result.inserted_id = "test_object_id"
        self.mock_collection.insert_one.return_value = mock_result
        
        result = manager.record_interaction(self.sample_interaction)
        
        assert result is True
        self.mock_collection.insert_one.assert_called_once()

    def test_record_interaction_failure(self):
        """Test interaction recording failure"""
        manager = InteractionHistoryManager(self.mock_storage_manager)
        manager.collection = None  # Simulate no collection
        
        result = manager.record_interaction(self.sample_interaction)
        
        assert result is False

    def test_get_lead_history(self):
        """Test getting lead interaction history"""
        manager = InteractionHistoryManager(self.mock_storage_manager)
        manager.collection = self.mock_collection
        
        # Mock database response
        mock_doc = {
            "interaction_id": "test_123",
            "lead_id": "lead_456",
            "lead_name": "John Doe",
            "company": "Acme Corp",
            "interaction_type": "message_sent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {"message_content": "Test message"},
            "whatsapp_message_id": "wa_123",
            "monday_item_id": "monday_456",
            "status_before": None,
            "status_after": None
        }
        
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([mock_doc]))
        self.mock_collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        result = manager.get_lead_history("lead_456")
        
        assert len(result) == 1
        assert isinstance(result[0], InteractionRecord)
        assert result[0].lead_id == "lead_456"

    def test_get_recent_interactions(self):
        """Test getting recent interactions"""
        manager = InteractionHistoryManager(self.mock_storage_manager)
        manager.collection = self.mock_collection
        
        # Mock empty response
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([]))
        self.mock_collection.find.return_value.sort.return_value = mock_cursor
        
        result = manager.get_recent_interactions(24)
        
        assert isinstance(result, list)
        self.mock_collection.find.assert_called_once()


class TestDeliveryTracker:
    """Test cases for Delivery Tracker"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_whatsapp_bridge = Mock()
        self.tracker = DeliveryTracker(self.mock_whatsapp_bridge)

    def test_delivery_tracker_initialization(self):
        """Test delivery tracker initializes correctly"""
        assert self.tracker is not None
        assert self.tracker.whatsapp_bridge == self.mock_whatsapp_bridge
        assert self.tracker.pending_confirmations == {}
        assert self.tracker.tracking_active is False

    def test_add_message_for_tracking(self):
        """Test adding message for tracking"""
        result = self.tracker.add_message_for_tracking("msg_123", "lead_456")
        
        assert result is True
        assert "msg_123" in self.tracker.pending_confirmations
        
        confirmation = self.tracker.pending_confirmations["msg_123"]
        assert confirmation.message_id == "msg_123"
        assert confirmation.lead_id == "lead_456"
        assert confirmation.delivery_status == OutreachStatus.SENT

    def test_check_delivery_status_delivered(self):
        """Test checking delivery status - delivered"""
        # Add message for tracking
        self.tracker.add_message_for_tracking("msg_123", "lead_456")
        
        # Mock WhatsApp response - delivered
        self.mock_whatsapp_bridge.get_message_status.return_value = {
            "delivered": True,
            "read": False,
            "replied": False
        }
        
        result = self.tracker.check_delivery_status("msg_123")
        
        assert result is not None
        assert result.delivery_status == OutreachStatus.DELIVERED
        assert result.delivered_timestamp is not None
        assert result.confirmation_attempts == 1

    def test_check_delivery_status_read(self):
        """Test checking delivery status - read"""
        # Add message for tracking
        self.tracker.add_message_for_tracking("msg_123", "lead_456")
        
        # Mock WhatsApp response - read
        self.mock_whatsapp_bridge.get_message_status.return_value = {
            "delivered": True,
            "read": True,
            "replied": False
        }
        
        result = self.tracker.check_delivery_status("msg_123")
        
        assert result is not None
        assert result.delivery_status == OutreachStatus.READ
        assert result.read_timestamp is not None

    def test_check_delivery_status_replied(self):
        """Test checking delivery status - replied"""
        # Add message for tracking
        self.tracker.add_message_for_tracking("msg_123", "lead_456")
        
        # Mock WhatsApp response - replied
        self.mock_whatsapp_bridge.get_message_status.return_value = {
            "delivered": True,
            "read": True,
            "replied": True
        }
        
        result = self.tracker.check_delivery_status("msg_123")
        
        assert result is not None
        assert result.delivery_status == OutreachStatus.REPLIED
        assert result.reply_timestamp is not None

    def test_check_delivery_status_error(self):
        """Test checking delivery status with error"""
        # Add message for tracking
        self.tracker.add_message_for_tracking("msg_123", "lead_456")
        
        # Mock WhatsApp error response
        self.mock_whatsapp_bridge.get_message_status.return_value = {
            "error": "Message not found"
        }
        
        result = self.tracker.check_delivery_status("msg_123")
        
        assert result is not None
        assert result.delivery_status == OutreachStatus.SENT  # Should remain unchanged
        assert result.confirmation_attempts == 1

    def test_start_stop_tracking(self):
        """Test starting and stopping tracking"""
        # Start tracking
        self.tracker.start_tracking(1)  # 1 second interval for testing
        
        assert self.tracker.tracking_active is True
        assert self.tracker.tracking_thread is not None
        
        # Stop tracking
        self.tracker.stop_tracking()
        
        assert self.tracker.tracking_active is False


class TestStatusTrackingSystem:
    """Test cases for Status Tracking System"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_keys = {
            'MONDAY_API_KEY': 'test_monday_key',
            'GEMINI_API_KEY': 'test_gemini_key'
        }
        self.mongodb_connection = "mongodb://localhost:27017"

    @patch('agents.status_tracking_system.ResearchStorageManager')
    @patch('agents.status_tracking_system.WhatsAppBridge')
    @patch('agents.status_tracking_system.MondayStatusUpdater')
    def test_status_tracking_system_initialization(self, mock_monday, mock_whatsapp, mock_storage):
        """Test status tracking system initializes correctly"""
        system = StatusTrackingSystem(self.api_keys, self.mongodb_connection)
        
        assert system is not None
        assert system.api_keys == self.api_keys
        assert system.metrics is not None
        assert isinstance(system.metrics, StatusTrackingMetrics)

    @patch('agents.status_tracking_system.ResearchStorageManager')
    @patch('agents.status_tracking_system.WhatsAppBridge')
    @patch('agents.status_tracking_system.MondayStatusUpdater')
    def test_track_message_sent(self, mock_monday, mock_whatsapp, mock_storage):
        """Test tracking a sent message"""
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_instance.connect.return_value = True
        mock_storage_instance.database = None  # Set database to None to avoid collection creation
        mock_storage.return_value = mock_storage_instance

        system = StatusTrackingSystem(self.api_keys, self.mongodb_connection)
        
        # Mock history manager
        system.history_manager = Mock()
        system.history_manager.record_interaction.return_value = True
        
        # Mock delivery tracker
        system.delivery_tracker = Mock()
        system.delivery_tracker.add_message_for_tracking.return_value = True
        
        result = system.track_message_sent(
            "msg_123", "lead_456", "John Doe", "Acme Corp", "Test message"
        )
        
        assert result is True
        system.history_manager.record_interaction.assert_called_once()
        system.delivery_tracker.add_message_for_tracking.assert_called_once()

    @patch('agents.status_tracking_system.ResearchStorageManager')
    @patch('agents.status_tracking_system.WhatsAppBridge')
    @patch('agents.status_tracking_system.MondayStatusUpdater')
    def test_update_delivery_status(self, mock_monday, mock_whatsapp, mock_storage):
        """Test updating delivery status"""
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_instance.connect.return_value = True
        mock_storage_instance.database = None  # Set database to None to avoid collection creation
        mock_storage.return_value = mock_storage_instance

        system = StatusTrackingSystem(self.api_keys, self.mongodb_connection)
        
        # Mock delivery tracker with confirmation
        mock_confirmation = DeliveryConfirmation(
            message_id="msg_123",
            lead_id="lead_456",
            sent_timestamp=datetime.now(timezone.utc),
            delivery_status=OutreachStatus.SENT
        )
        
        system.delivery_tracker = Mock()
        system.delivery_tracker.check_delivery_status.return_value = mock_confirmation
        
        # Mock Monday updater
        system.monday_updater = Mock()
        system.monday_updater.update_lead_status.return_value = True
        
        # Mock history manager
        system.history_manager = Mock()
        system.history_manager.record_interaction.return_value = True
        
        result = system.update_delivery_status("msg_123", OutreachStatus.DELIVERED)
        
        assert result is True
        system.monday_updater.update_lead_status.assert_called_once()
        system.history_manager.record_interaction.assert_called_once()

    @patch('agents.status_tracking_system.ResearchStorageManager')
    @patch('agents.status_tracking_system.WhatsAppBridge')
    @patch('agents.status_tracking_system.MondayStatusUpdater')
    def test_start_stop_automatic_tracking(self, mock_monday, mock_whatsapp, mock_storage):
        """Test starting and stopping automatic tracking"""
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_instance.connect.return_value = True
        mock_storage_instance.database = None  # Set database to None to avoid collection creation
        mock_storage.return_value = mock_storage_instance

        system = StatusTrackingSystem(self.api_keys, self.mongodb_connection)
        
        # Mock delivery tracker
        system.delivery_tracker = Mock()
        
        # Test start tracking
        system.start_automatic_tracking(30)
        system.delivery_tracker.start_tracking.assert_called_once_with(30)
        
        # Test stop tracking
        system.stop_automatic_tracking()
        system.delivery_tracker.stop_tracking.assert_called_once()

    @patch('agents.status_tracking_system.ResearchStorageManager')
    @patch('agents.status_tracking_system.WhatsAppBridge')
    @patch('agents.status_tracking_system.MondayStatusUpdater')
    def test_get_tracking_metrics(self, mock_monday, mock_whatsapp, mock_storage):
        """Test getting tracking metrics"""
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_instance.connect.return_value = True
        mock_storage_instance.database = None  # Set database to None to avoid collection creation
        mock_storage.return_value = mock_storage_instance

        system = StatusTrackingSystem(self.api_keys, self.mongodb_connection)
        
        metrics = system.get_tracking_metrics()
        
        assert isinstance(metrics, StatusTrackingMetrics)
        assert metrics.total_messages_tracked == 0
        assert metrics.delivery_confirmations == 0

    def test_create_status_tracking_system_function(self):
        """Test convenience function for creating status tracking system"""
        with patch('agents.status_tracking_system.ResearchStorageManager'), \
             patch('agents.status_tracking_system.WhatsAppBridge'), \
             patch('agents.status_tracking_system.MondayStatusUpdater'):
            
            system = create_status_tracking_system(self.api_keys, self.mongodb_connection)
            assert isinstance(system, StatusTrackingSystem)

    def test_interaction_record_dataclass(self):
        """Test InteractionRecord dataclass"""
        record = InteractionRecord(
            interaction_id="test_123",
            lead_id="lead_456",
            lead_name="John Doe",
            company="Acme Corp",
            interaction_type=InteractionType.MESSAGE_SENT,
            timestamp=datetime.now(timezone.utc),
            details={"test": "data"}
        )
        
        assert record.interaction_id == "test_123"
        assert record.lead_id == "lead_456"
        assert record.interaction_type == InteractionType.MESSAGE_SENT

    def test_delivery_confirmation_dataclass(self):
        """Test DeliveryConfirmation dataclass"""
        confirmation = DeliveryConfirmation(
            message_id="msg_123",
            lead_id="lead_456",
            sent_timestamp=datetime.now(timezone.utc),
            delivery_status=OutreachStatus.SENT
        )
        
        assert confirmation.message_id == "msg_123"
        assert confirmation.lead_id == "lead_456"
        assert confirmation.delivery_status == OutreachStatus.SENT
        assert confirmation.confirmation_attempts == 0

    def test_status_tracking_metrics_dataclass(self):
        """Test StatusTrackingMetrics dataclass"""
        metrics = StatusTrackingMetrics(
            total_messages_tracked=10,
            delivery_confirmations=8,
            read_receipts=5,
            replies_received=2,
            monday_updates_successful=9,
            monday_updates_failed=1
        )
        
        assert metrics.total_messages_tracked == 10
        assert metrics.delivery_confirmations == 8
        assert metrics.read_receipts == 5
        assert metrics.replies_received == 2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
