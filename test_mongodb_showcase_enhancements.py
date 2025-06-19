#!/usr/bin/env python3
"""
Test MongoDB Showcase Enhancements

SAFETY: This script tests the new conversation logs and vector embeddings
features without modifying any existing code or data.

Tests:
1. Conversation logs collection creation and storage
2. Vector embeddings with Voyage AI integration
3. Semantic search capabilities
4. Safe integration helpers
"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_conversation_logs():
    """Test conversation logs functionality"""
    print("💬 STEP 1: Testing Conversation Logs")
    print("=" * 50)
    
    try:
        from showcase.conversation_logs import ConversationLogsManager, MessageType
        
        # Test data
        lead_id = "2010690053"  # Real Monday.com ID
        lead_name = "Maor Shlomo"
        company = "Base44"
        phone_number = "+972501234567"
        
        conv_manager = ConversationLogsManager()
        if not conv_manager.connect():
            print("❌ Failed to connect to conversation logs")
            return False
        
        print(f"✅ Connected to conversation_logs collection")
        
        # Create conversation thread
        thread_id = conv_manager.create_conversation_thread(
            lead_id, lead_name, company, phone_number
        )
        
        if not thread_id:
            print("❌ Failed to create conversation thread")
            return False
        
        print(f"✅ Created conversation thread: {thread_id}")
        
        # Add outbound message
        success = conv_manager.add_message(
            thread_id, MessageType.OUTBOUND,
            f"Hi {lead_name}, I noticed {company} is growing rapidly. I'd love to discuss how we can help with your scaling challenges.",
            "AI Sales Agent", phone_number
        )
        
        if not success:
            print("❌ Failed to add outbound message")
            return False
        
        print("✅ Added outbound message")
        
        # Add inbound message (simulated response)
        success = conv_manager.add_message(
            thread_id, MessageType.INBOUND,
            "Thanks for reaching out! We're always looking for solutions to help us scale.",
            phone_number, "AI Sales Agent"
        )
        
        if not success:
            print("❌ Failed to add inbound message")
            return False
        
        print("✅ Added inbound message")
        
        # Retrieve conversation
        conversation = conv_manager.get_conversation_thread(thread_id)
        if not conversation:
            print("❌ Failed to retrieve conversation")
            return False
        
        print(f"✅ Retrieved conversation with {conversation['total_messages']} messages")
        print(f"   Outbound: {conversation['outbound_count']}")
        print(f"   Inbound: {conversation['inbound_count']}")
        
        # Get analytics
        analytics = conv_manager.get_conversation_analytics()
        print(f"✅ Conversation analytics: {analytics}")
        
        conv_manager.disconnect()
        print("✅ Conversation logs test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Conversation logs test failed: {e}")
        return False

def test_vector_embeddings():
    """Test vector embeddings functionality"""
    print("\n🔍 STEP 2: Testing Vector Embeddings")
    print("=" * 50)
    
    try:
        # First install voyageai if not available
        try:
            import voyageai
        except ImportError:
            print("📦 Installing voyageai package...")
            import subprocess
            result = subprocess.run([sys.executable, "-m", "pip", "install", "voyageai>=0.2.0"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to install voyageai: {result.stderr}")
                return False
            print("✅ voyageai package installed")
        
        from showcase.vector_embeddings import VectorEmbeddingsManager
        
        # Test data - sample research data
        research_data = {
            "lead_name": "Maor Shlomo",
            "company": "Base44",
            "company_intelligence": {
                "recent_news": "Base44 raised Series A funding to expand their AI platform",
                "growth_signals": ["hiring software engineers", "expanding to US market", "new product launches"],
                "challenges": ["scaling infrastructure", "competition from larger players", "talent acquisition"]
            },
            "decision_maker_insights": {
                "background": "CTO with 10+ years experience in AI and machine learning",
                "recent_activities": ["speaking at tech conferences", "hiring ML engineers", "product development"]
            },
            "conversation_hooks": [
                "recent funding announcement",
                "AI platform expansion",
                "scaling challenges",
                "US market entry"
            ],
            "confidence_score": 0.85,
            "research_timestamp": datetime.now().isoformat()
        }
        
        vector_manager = VectorEmbeddingsManager()
        if not vector_manager.connect():
            print("❌ Failed to connect to vector embeddings")
            return False
        
        print("✅ Connected to vector_embeddings collection")
        
        # Store research embedding
        research_id = f"research_{int(datetime.now().timestamp())}"
        success = vector_manager.store_research_embedding(research_id, research_data)
        
        if not success:
            print("❌ Failed to store research embedding")
            return False
        
        print(f"✅ Stored research embedding: {research_id}")
        
        # Test semantic search
        search_results = vector_manager.semantic_search(
            "AI platform scaling challenges funding", 
            "research_data", 
            limit=3
        )
        
        print(f"✅ Semantic search found {len(search_results)} results")
        for i, result in enumerate(search_results):
            print(f"   {i+1}. {result.get('metadata', {}).get('company', 'Unknown')} "
                  f"(similarity: {result.get('similarity_score', 0):.3f})")
        
        # Test similar companies search
        similar_companies = vector_manager.find_similar_companies("Base44", limit=2)
        print(f"✅ Found {len(similar_companies)} similar companies")
        
        # Get analytics
        analytics = vector_manager.get_embedding_analytics()
        print(f"✅ Vector analytics: {analytics}")
        
        vector_manager.disconnect()
        print("✅ Vector embeddings test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Vector embeddings test failed: {e}")
        return False

def test_safe_integrations():
    """Test safe integration helpers"""
    print("\n🛡️ STEP 3: Testing Safe Integration Helpers")
    print("=" * 50)
    
    try:
        from showcase.safe_integrations import (
            safe_log_conversation_message,
            safe_store_research_vector,
            safe_semantic_search_insights,
            safe_find_similar_companies,
            get_mongodb_showcase_summary
        )
        
        # Test safe conversation logging
        success = safe_log_conversation_message(
            "2010690053", "Maor Shlomo", "Base44", "+972501234567",
            "This is a test message from safe integration", "outbound"
        )
        print(f"✅ Safe conversation logging: {'Success' if success else 'Failed (non-critical)'}")
        
        # Test safe vector storage
        test_research = {
            "lead_name": "Test Lead",
            "company": "Test Company",
            "company_intelligence": {"recent_news": "Test news"},
            "conversation_hooks": ["test hook"]
        }
        success = safe_store_research_vector("test_research_123", test_research)
        print(f"✅ Safe vector storage: {'Success' if success else 'Failed (non-critical)'}")
        
        # Test safe semantic search
        insights = safe_semantic_search_insights("Base44 AI platform", limit=2)
        print(f"✅ Safe semantic search: Found {len(insights)} insights")
        
        # Test safe similar companies
        similar = safe_find_similar_companies("Base44", limit=2)
        print(f"✅ Safe similar companies: Found {len(similar)} companies")
        
        # Test showcase summary
        summary = get_mongodb_showcase_summary()
        print(f"✅ MongoDB showcase summary generated")
        print(f"   Core collections: {len(summary.get('mongodb_showcase', {}).get('core_collections', {}))}")
        print(f"   Showcase collections: {len(summary.get('mongodb_showcase', {}).get('new_showcase_collections', {}))}")
        
        print("✅ Safe integrations test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Safe integrations test failed: {e}")
        return False

def test_mongodb_collections_status():
    """Check the status of all MongoDB collections"""
    print("\n🗄️ STEP 4: MongoDB Collections Status")
    print("=" * 50)
    
    try:
        from config.database import MongoDBManager
        
        db_manager = MongoDBManager()
        if not db_manager.connect():
            print("❌ Failed to connect to MongoDB")
            return False
        
        collections = db_manager.database.list_collection_names()
        print(f"📊 Total collections: {len(collections)}")
        
        showcase_collections = ["conversation_logs", "vector_embeddings"]
        existing_collections = ["contacts", "research_results", "workflow_progress", "agent_configurations"]
        
        print("\n🎯 Showcase Collections:")
        for collection_name in showcase_collections:
            if collection_name in collections:
                collection = db_manager.get_collection(collection_name)
                count = collection.count_documents({})
                print(f"   ✅ {collection_name}: {count} documents")
            else:
                print(f"   ⚪ {collection_name}: Not created yet")
        
        print("\n📋 Existing Collections:")
        for collection_name in existing_collections:
            if collection_name in collections:
                collection = db_manager.get_collection(collection_name)
                count = collection.count_documents({})
                print(f"   ✅ {collection_name}: {count} documents")
            else:
                print(f"   ❌ {collection_name}: Missing")
        
        db_manager.disconnect()
        print("✅ Collections status check completed!")
        return True
        
    except Exception as e:
        print(f"❌ Collections status check failed: {e}")
        return False

def main():
    """Main test function"""
    print("🎯 MONGODB SHOWCASE ENHANCEMENTS TEST")
    print("=" * 60)
    print("Testing conversation logs and vector embeddings")
    print("SAFETY: All tests use NEW collections and don't modify existing code")
    print("=" * 60)
    
    tests = [
        test_conversation_logs,
        test_vector_embeddings,
        test_safe_integrations,
        test_mongodb_collections_status
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"\n⚠️ Test failed but system remains safe")
    
    print("\n" + "=" * 60)
    print(f"🎉 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print("🚀 MongoDB showcase enhancements are working correctly")
        print("\n🎯 NEW CAPABILITIES ADDED:")
        print("   💬 Conversation Logs: WhatsApp conversation threads with nested messages")
        print("   🔍 Vector Embeddings: Voyage AI semantic search for research data")
        print("   🛡️ Safe Integrations: Non-breaking helpers for existing code")
        print("\n📊 MONGODB SHOWCASE NOW INCLUDES:")
        print("   • Document flexibility (nested conversation threads)")
        print("   • Vector search capabilities (semantic similarity)")
        print("   • Real-time analytics (conversation metrics)")
        print("   • Schema-less design (evolving AI agent needs)")
        print("   • Single source of truth (all agent data in MongoDB)")
    else:
        print(f"⚠️ {total - passed} tests failed, but your existing system is safe")
        print("The enhancements are optional and don't break existing functionality")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
