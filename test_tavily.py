#!/usr/bin/env python3
"""
Test script to verify Tavily API is working and check MongoDB research results
"""
import os
import sys
from dotenv import load_dotenv
import requests
import json
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def test_tavily_api():
    """Test Tavily API directly"""
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        print("❌ TAVILY_API_KEY not found in environment")
        return False
    
    print(f"✅ Tavily API key found: {api_key[:10]}...")
    
    # Test Tavily API directly
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "api_key": api_key,
        "query": "Base44 company acquisition news",
        "search_depth": "basic",
        "include_answer": True,
        "include_raw_content": False,
        "max_results": 3
    }
    
    try:
        print("🔍 Testing Tavily API directly...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Tavily API is working!")
            print(f"Results count: {len(result.get('results', []))}")
            if result.get('results'):
                print(f"First result: {result['results'][0].get('title', 'No title')}")
            return True
        else:
            print(f"❌ Tavily API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Tavily API exception: {e}")
        return False

def check_mongodb_research():
    """Check what's actually stored in MongoDB"""
    connection_string = os.getenv('MONGODB_CONNECTION_STRING')
    if not connection_string:
        print("❌ MONGODB_CONNECTION_STRING not found")
        return
    
    try:
        client = MongoClient(connection_string)
        db = client['agno_sales_agent']
        collection = db['research_results']
        
        # Get the latest research results
        latest_results = list(collection.find().sort("research_timestamp", -1).limit(3))
        
        print(f"\n📊 Found {len(latest_results)} recent research results in MongoDB:")
        
        for i, result in enumerate(latest_results, 1):
            print(f"\n--- Research Result {i} ---")
            print(f"Research ID: {result.get('research_id', 'N/A')}")
            print(f"Lead: {result.get('lead_name', 'N/A')} at {result.get('company', 'N/A')}")
            print(f"Confidence: {result.get('confidence_score', 'N/A')}")
            print(f"Timestamp: {result.get('research_timestamp', 'N/A')}")
            
            # Check if we have real data or placeholders
            company_intel = result.get('company_intelligence', {})
            recent_news = company_intel.get('recent_news', '')
            
            if 'Need to perform web search' in recent_news or 'placeholder' in recent_news.lower():
                print("❌ PLACEHOLDER DATA DETECTED!")
            else:
                print("✅ Appears to be real data")
            
            print(f"Recent News: {recent_news[:100]}...")
            
        client.close()
        
    except Exception as e:
        print(f"❌ MongoDB error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Tavily Integration\n")
    
    # Test 1: Direct Tavily API
    tavily_works = test_tavily_api()
    
    # Test 2: Check MongoDB data
    check_mongodb_research()
    
    print(f"\n🎯 Summary:")
    print(f"Tavily API: {'✅ Working' if tavily_works else '❌ Not Working'}")
    print(f"Next step: {'Check agent tool configuration' if tavily_works else 'Fix Tavily API access'}")
