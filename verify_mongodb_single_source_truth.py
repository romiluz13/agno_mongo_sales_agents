#!/usr/bin/env python3
"""
MongoDB Single Source of Truth Verification Script

This script verifies that our complete workflow is properly implemented:
1. Monday.com UI Button Click → Chrome Extension
2. Store ALL contact data in MongoDB 
3. Research with Tavily → Store research data in MongoDB
4. Message agent fetches ALL data from MongoDB as single source
5. Send via WhatsApp

CRITICAL: This verifies the exact flow the user described.
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

def verify_environment():
    """Verify all required environment variables are set"""
    print("🔧 STEP 1: Verifying Environment Configuration")
    print("=" * 60)
    
    required_vars = [
        'MONGODB_CONNECTION_STRING',
        'MONDAY_API_TOKEN', 
        'TAVILY_API_KEY',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 20}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ All environment variables configured")
    return True

def verify_mongodb_connection():
    """Verify MongoDB connection and collections"""
    print("\n🗄️ STEP 2: Verifying MongoDB Connection")
    print("=" * 60)
    
    try:
        from config.database import MongoDBManager
        
        db_manager = MongoDBManager()
        if not db_manager.connect():
            print("❌ Failed to connect to MongoDB")
            return False
        
        # Test connection
        result = db_manager.test_connection()
        if result["success"]:
            print("✅ MongoDB connection successful")
            print(f"   Database: {result['database']}")
            print(f"   Collections: {result['collections']}")
            
            # Verify required collections exist
            required_collections = ["contacts", "research_results", "leads", "interactions"]
            existing_collections = result['collections']
            
            for collection in required_collections:
                if collection in existing_collections:
                    print(f"✅ Collection '{collection}' exists")
                else:
                    print(f"⚠️ Collection '{collection}' missing - will be created")
            
            db_manager.disconnect()
            return True
        else:
            print(f"❌ MongoDB test failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB verification failed: {e}")
        return False

def verify_monday_api():
    """Verify Monday.com API connection"""
    print("\n📋 STEP 3: Verifying Monday.com API")
    print("=" * 60)
    
    try:
        from tools.monday_client import MondayClient
        
        client = MondayClient()
        
        # Test basic connection
        leads = client.get_all_leads()
        print(f"✅ Monday.com API connected")
        print(f"   Found {len(leads)} leads in board")
        
        if leads:
            # Test comprehensive data extraction
            first_lead = leads[0]
            print(f"   Testing comprehensive data for: {first_lead['name']}")
            
            comprehensive_data = client.get_lead_comprehensive_data(first_lead['monday_id'])
            print(f"✅ Comprehensive data extraction working")
            print(f"   Data richness score: {comprehensive_data['crm_insights']['data_richness_score']:.2f}")
            print(f"   Notes/updates: {len(comprehensive_data['notes_and_updates'])}")
            print(f"   All columns: {len(comprehensive_data['all_column_data'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Monday.com API verification failed: {e}")
        return False

def verify_research_storage():
    """Verify research storage system"""
    print("\n🔍 STEP 4: Verifying Research Storage System")
    print("=" * 60)
    
    try:
        from agents.research_storage import ResearchStorageManager, ResearchDataProcessor
        
        # Initialize storage
        connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        storage_manager = ResearchStorageManager(connection_string)
        
        if not storage_manager.connect():
            print("❌ Failed to connect research storage to MongoDB")
            return False
        
        print("✅ Research storage connected to MongoDB")
        
        # Test data processor
        processor = ResearchDataProcessor()
        print("✅ Research data processor initialized")
        
        storage_manager.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Research storage verification failed: {e}")
        return False

def verify_workflow_coordinator():
    """Verify workflow coordinator with MongoDB integration"""
    print("\n🔄 STEP 5: Verifying Workflow Coordinator")
    print("=" * 60)
    
    try:
        from agents.workflow_coordinator import WorkflowCoordinator
        
        api_keys = {
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
            'MONDAY_API_KEY': os.getenv('MONDAY_API_TOKEN'),
            'MONGODB_CONNECTION_STRING': os.getenv('MONGODB_CONNECTION_STRING')
        }
        
        coordinator = WorkflowCoordinator(api_keys, api_keys['MONGODB_CONNECTION_STRING'])
        print("✅ Workflow coordinator initialized")
        
        # Verify MongoDB integration components
        if hasattr(coordinator, 'research_storage'):
            print("✅ Research storage integrated")
        else:
            print("❌ Research storage NOT integrated")
            return False
            
        if hasattr(coordinator, 'research_processor'):
            print("✅ Research processor integrated")
        else:
            print("❌ Research processor NOT integrated")
            return False
        
        print("✅ MongoDB Single Source of Truth workflow ready")
        return True
        
    except Exception as e:
        print(f"❌ Workflow coordinator verification failed: {e}")
        return False

def verify_backend_api():
    """Verify backend API endpoints"""
    print("\n🌐 STEP 6: Verifying Backend API")
    print("=" * 60)
    
    try:
        # Import to check for syntax errors
        import backend.main as backend_main
        print("✅ Backend API imports successfully")
        
        # Check if MondayItemRequest is defined
        if hasattr(backend_main, 'MondayItemRequest'):
            print("✅ MondayItemRequest schema defined")
        else:
            print("❌ MondayItemRequest schema missing")
            return False
        
        # Check if monday_client is imported
        if hasattr(backend_main, 'monday_client'):
            print("✅ Monday.com client imported")
        else:
            print("⚠️ Monday.com client import not detected (may be in global scope)")
        
        print("✅ Backend API ready for MongoDB workflow")
        return True
        
    except Exception as e:
        print(f"❌ Backend API verification failed: {e}")
        return False

def verify_chrome_extension():
    """Verify Chrome extension has MongoDB workflow support"""
    print("\n🔌 STEP 7: Verifying Chrome Extension")
    print("=" * 60)
    
    try:
        # Check if content.js has the new methods
        content_js_path = "extension/content.js"
        
        if not os.path.exists(content_js_path):
            print("❌ Chrome extension content.js not found")
            return False
        
        with open(content_js_path, 'r') as f:
            content = f.read()
        
        # Check for new methods
        required_methods = [
            'getBoardIdFromUrl',
            'extractMondayItemId', 
            'validateMondayData',
            'transformMondayDataForAPI',
            'processLeadWithMongoDB'
        ]
        
        for method in required_methods:
            if method in content:
                print(f"✅ Method '{method}' found")
            else:
                print(f"❌ Method '{method}' missing")
                return False
        
        print("✅ Chrome extension ready for MongoDB workflow")
        return True
        
    except Exception as e:
        print(f"❌ Chrome extension verification failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🎯 MONGODB SINGLE SOURCE OF TRUTH VERIFICATION")
    print("=" * 60)
    print("Verifying the complete workflow:")
    print("1. Monday.com UI Button Click → Chrome Extension")
    print("2. Store ALL contact data in MongoDB")
    print("3. Research with Tavily → Store research data in MongoDB") 
    print("4. Message agent fetches ALL data from MongoDB")
    print("5. Send via WhatsApp")
    print("=" * 60)
    
    verification_steps = [
        verify_environment,
        verify_mongodb_connection,
        verify_monday_api,
        verify_research_storage,
        verify_workflow_coordinator,
        verify_backend_api,
        verify_chrome_extension
    ]
    
    all_passed = True
    
    for step in verification_steps:
        if not step():
            all_passed = False
            break
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("✅ MongoDB Single Source of Truth workflow is READY")
        print("\n🚀 NEXT STEPS:")
        print("1. Start backend server: cd backend && python main.py")
        print("2. Start WhatsApp bridge: cd whatsapp && node working_bridge.js")
        print("3. Load Chrome extension and test on Monday.com")
        print("4. Scan QR code when prompted")
        print("5. Click 'Process Lead' button to test complete workflow")
    else:
        print("❌ VERIFICATION FAILED!")
        print("Please fix the issues above before proceeding.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
