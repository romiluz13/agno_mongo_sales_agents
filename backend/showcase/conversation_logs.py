#!/usr/bin/env python3
"""
Conversation Logs Collection - MongoDB Showcase Enhancement

SAFETY: This is a NEW collection that doesn't modify existing code.
It safely stores WhatsApp conversation threads to showcase MongoDB's 
document flexibility for nested chat data.

Features:
- Complete conversation threads with nested message arrays
- Rich metadata for each message (timestamps, status, sender info)
- Conversation analytics and insights
- Thread-based organization for easy retrieval
"""

import os
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import MongoDBManager

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Message types for conversation tracking"""
    OUTBOUND = "outbound"
    INBOUND = "inbound"
    SYSTEM = "system"

class MessageStatus(Enum):
    """Message delivery status"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

@dataclass
class ConversationMessage:
    """Individual message in a conversation"""
    message_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    sender: str
    recipient: str
    status: MessageStatus
    whatsapp_message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ConversationThread:
    """Complete conversation thread"""
    thread_id: str
    lead_id: str
    lead_name: str
    company: str
    phone_number: str
    started_at: datetime
    last_activity: datetime
    messages: List[ConversationMessage]
    total_messages: int
    outbound_count: int
    inbound_count: int
    conversation_status: str  # "active", "closed", "pending"
    tags: List[str]
    analytics: Dict[str, Any]

class ConversationLogsManager:
    """
    SAFE MongoDB manager for conversation logs
    Creates new collection without touching existing code
    """
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv("MONGODB_CONNECTION_STRING")
        self.db_manager = None
        self.collection = None
        
    def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            self.db_manager = MongoDBManager()
            if self.db_manager.connect():
                # NEW COLLECTION - completely safe
                self.collection = self.db_manager.get_collection("conversation_logs")
                logger.info("✅ Connected to conversation_logs collection")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.db_manager:
            self.db_manager.disconnect()
    
    def create_conversation_thread(self, lead_id: str, lead_name: str, 
                                 company: str, phone_number: str) -> str:
        """Create a new conversation thread"""
        try:
            thread_id = f"conv_{lead_id}_{int(datetime.now().timestamp())}"
            
            thread = ConversationThread(
                thread_id=thread_id,
                lead_id=lead_id,
                lead_name=lead_name,
                company=company,
                phone_number=phone_number,
                started_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                messages=[],
                total_messages=0,
                outbound_count=0,
                inbound_count=0,
                conversation_status="active",
                tags=["ai_generated", "sales_outreach"],
                analytics={
                    "response_rate": 0.0,
                    "avg_response_time_minutes": 0.0,
                    "conversation_score": 0.0,
                    "engagement_level": "new"
                }
            )
            
            # Convert to dict for MongoDB storage
            thread_dict = asdict(thread)
            thread_dict['started_at'] = thread.started_at.isoformat()
            thread_dict['last_activity'] = thread.last_activity.isoformat()
            
            # Store in MongoDB
            result = self.collection.insert_one(thread_dict)
            
            if result.inserted_id:
                logger.info(f"✅ Created conversation thread: {thread_id}")
                return thread_id
            else:
                logger.error(f"❌ Failed to create thread: {thread_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating conversation thread: {e}")
            return None
    
    def add_message(self, thread_id: str, message_type: MessageType, 
                   content: str, sender: str, recipient: str,
                   whatsapp_message_id: str = None) -> bool:
        """Add a message to conversation thread"""
        try:
            message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
            
            message = ConversationMessage(
                message_id=message_id,
                message_type=message_type,
                content=content,
                timestamp=datetime.now(timezone.utc),
                sender=sender,
                recipient=recipient,
                status=MessageStatus.SENT,
                whatsapp_message_id=whatsapp_message_id,
                metadata={
                    "content_length": len(content),
                    "has_emoji": any(ord(char) > 127 for char in content),
                    "word_count": len(content.split())
                }
            )
            
            # Convert message to dict
            message_dict = asdict(message)
            message_dict['timestamp'] = message.timestamp.isoformat()
            message_dict['message_type'] = message.message_type.value
            message_dict['status'] = message.status.value
            
            # Update conversation thread
            update_result = self.collection.update_one(
                {"thread_id": thread_id},
                {
                    "$push": {"messages": message_dict},
                    "$inc": {
                        "total_messages": 1,
                        f"{message_type.value}_count": 1
                    },
                    "$set": {
                        "last_activity": datetime.now(timezone.utc).isoformat(),
                        "conversation_status": "active"
                    }
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(f"✅ Added {message_type.value} message to thread: {thread_id}")
                return True
            else:
                logger.error(f"❌ Failed to add message to thread: {thread_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error adding message: {e}")
            return False
    
    def get_conversation_thread(self, thread_id: str) -> Optional[Dict]:
        """Retrieve complete conversation thread"""
        try:
            thread = self.collection.find_one({"thread_id": thread_id})
            if thread:
                logger.info(f"✅ Retrieved conversation thread: {thread_id}")
                return thread
            else:
                logger.warning(f"⚠️ Thread not found: {thread_id}")
                return None
        except Exception as e:
            logger.error(f"❌ Error retrieving thread: {e}")
            return None
    
    def get_conversations_by_lead(self, lead_id: str) -> List[Dict]:
        """Get all conversations for a specific lead"""
        try:
            conversations = list(self.collection.find({"lead_id": lead_id}))
            logger.info(f"✅ Found {len(conversations)} conversations for lead: {lead_id}")
            return conversations
        except Exception as e:
            logger.error(f"❌ Error retrieving conversations: {e}")
            return []
    
    def update_message_status(self, thread_id: str, message_id: str, 
                            new_status: MessageStatus) -> bool:
        """Update message delivery status"""
        try:
            result = self.collection.update_one(
                {
                    "thread_id": thread_id,
                    "messages.message_id": message_id
                },
                {
                    "$set": {
                        "messages.$.status": new_status.value,
                        "last_activity": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated message status: {message_id} -> {new_status.value}")
                return True
            else:
                logger.warning(f"⚠️ Message not found for status update: {message_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating message status: {e}")
            return False
    
    def get_conversation_analytics(self) -> Dict[str, Any]:
        """Get conversation analytics across all threads"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_conversations": {"$sum": 1},
                        "total_messages": {"$sum": "$total_messages"},
                        "avg_messages_per_conversation": {"$avg": "$total_messages"},
                        "active_conversations": {
                            "$sum": {"$cond": [{"$eq": ["$conversation_status", "active"]}, 1, 0]}
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "total_conversations": 1,
                        "total_messages": 1,
                        "avg_messages_per_conversation": {"$round": ["$avg_messages_per_conversation", 2]},
                        "active_conversations": 1,
                        "response_rate": {
                            "$round": [
                                {"$multiply": [
                                    {"$divide": ["$active_conversations", "$total_conversations"]}, 
                                    100
                                ]}, 2
                            ]
                        }
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            analytics = result[0] if result else {
                "total_conversations": 0,
                "total_messages": 0,
                "avg_messages_per_conversation": 0,
                "active_conversations": 0,
                "response_rate": 0
            }
            
            logger.info("✅ Generated conversation analytics")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error generating analytics: {e}")
            return {}

# SAFE INTEGRATION HELPER - doesn't modify existing code
def safe_log_outbound_message(lead_id: str, lead_name: str, company: str, 
                            phone_number: str, message_content: str,
                            whatsapp_message_id: str = None) -> bool:
    """
    SAFE helper function to log outbound messages
    Can be called from existing outreach code without breaking anything
    """
    try:
        conv_manager = ConversationLogsManager()
        if conv_manager.connect():
            # Try to find existing thread or create new one
            existing_threads = conv_manager.get_conversations_by_lead(lead_id)
            
            if existing_threads:
                # Use most recent thread
                thread_id = existing_threads[-1]['thread_id']
            else:
                # Create new thread
                thread_id = conv_manager.create_conversation_thread(
                    lead_id, lead_name, company, phone_number
                )
            
            if thread_id:
                success = conv_manager.add_message(
                    thread_id, MessageType.OUTBOUND, message_content,
                    "AI Sales Agent", phone_number, whatsapp_message_id
                )
                conv_manager.disconnect()
                return success
            
        conv_manager.disconnect()
        return False
        
    except Exception as e:
        logger.error(f"❌ Safe logging failed: {e}")
        return False
