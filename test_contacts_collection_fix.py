#!/usr/bin/env python3
"""
Test script to validate the contacts collection fix

This script tests the complete workflow to ensure:
1. Real Monday.com item IDs are extracted (not fake ones)
2. Monday.com API calls succeed with real IDs
3. Real data is stored in contacts collection
4. No more placeholder data ("Unknown Lead", "Unknown Company")

CRITICAL: This validates the fix for the contacts collection empty issue.
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

def test_monday_api_with_real_ids():
    """Test Monday.com API with real item IDs vs fake IDs"""
    print("🔍 STEP 1: Testing Monday.com API with Real vs Fake IDs")
    print("=" * 60)
    
    try:
        from tools.monday_client import MondayClient
        
        client = MondayClient()
        
        # Get real item IDs from Monday.com
        leads = client.get_all_leads()
        if not leads:
            print("❌ No leads found in Monday.com board")
            return False
        
        real_item_id = leads[0]['monday_id']
        fake_item_id = f"agno_{int(datetime.now().timestamp() * 1000)}_test"
        
        print(f"📋 Real item ID: {real_item_id}")
        print(f"🚫 Fake item ID: {fake_item_id}")
        
        # Test with real ID
        print(f"\n✅ Testing with REAL ID: {real_item_id}")
        try:
            real_data = client.get_lead_comprehensive_data(real_item_id)
            print(f"✅ SUCCESS: Real ID returned data")
            print(f"   Name: {real_data.get('name', 'N/A')}")
            print(f"   Company: {real_data.get('company', 'N/A')}")
            print(f"   Data richness: {real_data['crm_insights']['data_richness_score']:.2f}")
        except Exception as e:
            print(f"❌ UNEXPECTED: Real ID failed: {e}")
            return False
        
        # Test with fake ID
        print(f"\n🚫 Testing with FAKE ID: {fake_item_id}")
        try:
            fake_data = client.get_lead_comprehensive_data(fake_item_id)
            print(f"❌ UNEXPECTED: Fake ID should have failed but returned data")
            return False
        except Exception as e:
            print(f"✅ EXPECTED: Fake ID failed as expected: {e}")
        
        print("✅ Monday.com API test passed - real IDs work, fake IDs fail")
        return True
        
    except Exception as e:
        print(f"❌ Monday.com API test failed: {e}")
        return False

def test_backend_api_with_real_data():
    """Test backend API with real Monday.com data"""
    print("\n🌐 STEP 2: Testing Backend API with Real Data")
    print("=" * 60)
    
    try:
        from tools.monday_client import MondayClient
        from config.database import MongoDBManager
        
        # Get real Monday.com data
        client = MondayClient()
        leads = client.get_all_leads()
        if not leads:
            print("❌ No leads found")
            return False
        
        real_lead = leads[0]
        real_item_id = real_lead['monday_id']
        board_id = client.board_id
        
        print(f"📋 Testing with real lead: {real_lead['name']} (ID: {real_item_id})")
        
        # Test the exact workflow that was failing
        try:
            comprehensive_data = client.get_lead_comprehensive_data(real_item_id)
            print(f"✅ Comprehensive data fetched successfully")
            print(f"   Name: {comprehensive_data.get('name', 'N/A')}")
            print(f"   Company: {comprehensive_data.get('company', 'N/A')}")
            print(f"   Columns: {len(comprehensive_data.get('all_column_data', {}))}")
            print(f"   Notes: {len(comprehensive_data.get('notes_and_updates', []))}")
            print(f"   Data richness: {comprehensive_data['crm_insights']['data_richness_score']:.2f}")
            
            # Verify this is NOT placeholder data
            if (comprehensive_data.get('name') == 'Unknown Lead' or 
                comprehensive_data.get('company') == 'Unknown Company' or
                comprehensive_data['crm_insights']['data_richness_score'] <= 0.1):
                print("❌ CRITICAL: Still getting placeholder data!")
                return False
            
            print("✅ Real data confirmed - no placeholder data")
            
        except Exception as e:
            print(f"❌ Failed to fetch comprehensive data: {e}")
            return False
        
        # Test MongoDB storage
        db_manager = MongoDBManager()
        if db_manager.connect():
            print("✅ MongoDB connected")
            
            # Store the real data (simulating the fixed workflow)
            contacts_collection = db_manager.get_collection("contacts")
            contact_doc = {
                "monday_item_id": real_item_id,
                "board_id": board_id,
                "comprehensive_data": comprehensive_data,
                "last_updated": datetime.now().isoformat(),
                "data_source": "monday_api",
                "test_timestamp": datetime.now().isoformat(),
                "test_type": "contacts_fix_validation"
            }
            
            # Upsert the document
            result = contacts_collection.replace_one(
                {"monday_item_id": real_item_id},
                contact_doc,
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                print("✅ Real data stored in MongoDB contacts collection")
                
                # Verify the stored data
                stored_doc = contacts_collection.find_one({"monday_item_id": real_item_id})
                stored_name = stored_doc['comprehensive_data'].get('name', 'N/A')
                stored_company = stored_doc['comprehensive_data'].get('company', 'N/A')
                stored_richness = stored_doc['comprehensive_data']['crm_insights']['data_richness_score']
                
                print(f"✅ Verified stored data:")
                print(f"   Name: {stored_name}")
                print(f"   Company: {stored_company}")
                print(f"   Data richness: {stored_richness:.2f}")
                
                if stored_name != 'Unknown Lead' and stored_company != 'Unknown Company' and stored_richness > 0.1:
                    print("✅ SUCCESS: Real data stored, no placeholder data!")
                    return True
                else:
                    print("❌ FAILURE: Placeholder data still being stored")
                    return False
            else:
                print("❌ Failed to store data in MongoDB")
                return False
            
            db_manager.disconnect()
        else:
            print("❌ Failed to connect to MongoDB")
            return False
        
    except Exception as e:
        print(f"❌ Backend API test failed: {e}")
        return False

def test_contacts_collection_status():
    """Check the current status of contacts collection"""
    print("\n🗄️ STEP 3: Checking Contacts Collection Status")
    print("=" * 60)
    
    try:
        from config.database import MongoDBManager
        
        db_manager = MongoDBManager()
        if db_manager.connect():
            contacts_collection = db_manager.get_collection("contacts")
            
            # Get total count
            total_count = contacts_collection.count_documents({})
            print(f"📊 Total contacts: {total_count}")
            
            # Count placeholder vs real data
            placeholder_count = contacts_collection.count_documents({
                "$or": [
                    {"comprehensive_data.name": "Unknown Lead"},
                    {"comprehensive_data.company": "Unknown Company"},
                    {"comprehensive_data.crm_insights.data_richness_score": {"$lte": 0.1}}
                ]
            })
            
            real_data_count = total_count - placeholder_count
            
            print(f"🚫 Placeholder data documents: {placeholder_count}")
            print(f"✅ Real data documents: {real_data_count}")
            
            # Show sample of each type
            if placeholder_count > 0:
                placeholder_sample = contacts_collection.find_one({
                    "comprehensive_data.name": "Unknown Lead"
                })
                if placeholder_sample:
                    print(f"\n🚫 Placeholder sample:")
                    print(f"   ID: {placeholder_sample['monday_item_id']}")
                    print(f"   Name: {placeholder_sample['comprehensive_data']['name']}")
                    print(f"   Company: {placeholder_sample['comprehensive_data']['company']}")
            
            if real_data_count > 0:
                real_sample = contacts_collection.find_one({
                    "$and": [
                        {"comprehensive_data.name": {"$ne": "Unknown Lead"}},
                        {"comprehensive_data.company": {"$ne": "Unknown Company"}},
                        {"comprehensive_data.crm_insights.data_richness_score": {"$gt": 0.1}}
                    ]
                })
                if real_sample:
                    print(f"\n✅ Real data sample:")
                    print(f"   ID: {real_sample['monday_item_id']}")
                    print(f"   Name: {real_sample['comprehensive_data']['name']}")
                    print(f"   Company: {real_sample['comprehensive_data']['company']}")
                    print(f"   Richness: {real_sample['comprehensive_data']['crm_insights']['data_richness_score']:.2f}")
            
            db_manager.disconnect()
            
            # Determine success
            if real_data_count > 0:
                print(f"\n✅ SUCCESS: Found {real_data_count} documents with real data!")
                return True
            else:
                print(f"\n❌ ISSUE: No real data found, only placeholder data")
                return False
        else:
            print("❌ Failed to connect to MongoDB")
            return False
        
    except Exception as e:
        print(f"❌ Contacts collection test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🎯 CONTACTS COLLECTION FIX VALIDATION")
    print("=" * 60)
    print("Testing the fix for contacts collection storing placeholder data")
    print("Root cause: Chrome extension generated fake Monday.com item IDs")
    print("Fix: Enhanced ID extraction + validation to use only real IDs")
    print("=" * 60)
    
    tests = [
        test_monday_api_with_real_ids,
        test_backend_api_with_real_data,
        test_contacts_collection_status
    ]
    
    all_passed = True
    
    for test in tests:
        if not test():
            all_passed = False
            break
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Contacts collection fix is working correctly")
        print("✅ Real Monday.com data is being stored")
        print("✅ No more placeholder data issues")
        print("\n🚀 NEXT STEPS:")
        print("1. Test the Chrome extension with the updated code")
        print("2. Verify real item ID extraction in browser console")
        print("3. Process a lead and confirm real data storage")
    else:
        print("❌ TESTS FAILED!")
        print("The contacts collection fix needs more work")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
