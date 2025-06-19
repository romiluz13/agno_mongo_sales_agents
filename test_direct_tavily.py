#!/usr/bin/env python3
"""
Test direct Tavily API integration to verify it works correctly
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_direct_tavily_search():
    """Test Tavily API with the exact format from documentation"""
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        print("❌ TAVILY_API_KEY not found in environment")
        return False
    
    print(f"✅ Tavily API key found: {api_key[:10]}...")
    
    # Test with Base44 company research
    url = "https://api.tavily.com/search"
    
    payload = {
        "query": "Base44 company acquisition news recent",
        "topic": "general",
        "search_depth": "advanced",
        "chunks_per_source": 3,
        "max_results": 5,
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        print("🔍 Testing Tavily API with Base44 research...")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Tavily API is working perfectly!")
            print(f"Query: {result.get('query', 'N/A')}")
            print(f"Answer: {result.get('answer', 'No answer')[:200]}...")
            print(f"Results count: {len(result.get('results', []))}")
            
            if result.get('results'):
                print("\n📰 Search Results:")
                for i, res in enumerate(result['results'][:3], 1):
                    print(f"  {i}. {res.get('title', 'No title')}")
                    print(f"     URL: {res.get('url', 'No URL')}")
                    print(f"     Content: {res.get('content', 'No content')[:100]}...")
                    print()
            
            return True
        else:
            print(f"❌ Tavily API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Tavily API exception: {e}")
        return False

def test_multiple_searches():
    """Test multiple search queries like the agent should do"""
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        return False
    
    searches = [
        "Base44 recent news 2024 2025",
        "Base44 funding growth acquisition",
        "Maor Shlomo Base44 background",
        "Base44 technology stack database infrastructure"
    ]
    
    print("\n🔍 Testing multiple searches (like the agent should do):")
    
    for i, query in enumerate(searches, 1):
        print(f"\n--- Search {i}: {query} ---")
        
        payload = {
            "query": query,
            "topic": "general",
            "search_depth": "basic",
            "max_results": 3,
            "include_answer": True
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post("https://api.tavily.com/search", json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Found {len(result.get('results', []))} results")
                if result.get('answer'):
                    print(f"Answer: {result['answer'][:150]}...")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🧪 Testing Direct Tavily API Integration\n")
    
    # Test 1: Basic functionality
    works = test_direct_tavily_search()
    
    if works:
        # Test 2: Multiple searches
        test_multiple_searches()
        
        print(f"\n🎯 Summary:")
        print(f"✅ Tavily API works perfectly with direct HTTP calls")
        print(f"❌ Issue is with Agno framework's TavilyTools integration")
        print(f"💡 Solution: Create custom Tavily tool or fix TavilyTools configuration")
    else:
        print(f"\n❌ Tavily API itself has issues")
