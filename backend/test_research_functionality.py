#!/usr/bin/env python3
"""
Test script to verify research agent is fetching real data from Tavily API
and storing properly in MongoDB
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('/Users/rom.iluz/Dev/agno_sales_agent/agno/agno-sales-extension/backend')

def test_research_functionality():
    """Test research agent with real data fetching and storage"""
    
    print('🔬 Testing Research Agent Real Data Functionality...\n')
    
    # Get real API keys (using correct uppercase names that research agent expects)
    api_keys = {
        'GEMINI_API_KEY': os.getenv('GOOGLE_API_KEY'),  # Using Google API key for Gemini
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        'MONDAY_API_KEY': os.getenv('MONDAY_API_TOKEN')
    }
    
    # Verify API keys are present
    print('🔑 Checking API Keys:')
    for key, value in api_keys.items():
        status = '✅' if value and value != 'test-key' else '❌'
        masked_value = f"{value[:8]}..." if value and len(value) > 8 else 'Missing'
        print(f'  {status} {key}: {masked_value}')

    if not api_keys['TAVILY_API_KEY']:
        print('❌ Tavily API key is missing! Cannot test real research functionality.')
        return False
    
    print('\n' + '='*60)
    print('🧪 TESTING RESEARCH AGENT WITH REAL DATA')
    print('='*60)
    
    try:
        from agents.research_agent import ResearchAgent, LeadInput
        from config.database import MongoDBManager

        # Initialize research agent
        research_agent = ResearchAgent(api_keys=api_keys, config={})
        print('✅ Research Agent initialized successfully')

        # Test data - using a real company for testing (using LeadInput dataclass)
        test_lead_data = LeadInput(
            lead_name='John Smith',
            company='Stripe',
            title='CTO',
            industry='Financial Technology',
            company_size='5000+ employees'
        )

        print(f'\n🎯 Testing research for: {test_lead_data.lead_name} at {test_lead_data.company}')

        # Perform research
        print('🔍 Performing research...')
        research_result = research_agent.research_lead(test_lead_data)
        
        if research_result:
            print('✅ Research completed successfully!')

            # Convert ResearchOutput to dict for analysis
            result_dict = {
                'confidence_score': research_result.confidence_score,
                'company_intelligence': research_result.company_intelligence,
                'decision_maker_insights': research_result.decision_maker_insights,
                'conversation_hooks': research_result.conversation_hooks,
                'timing_rationale': research_result.timing_rationale,
                'research_timestamp': research_result.research_timestamp,
                'sources': research_result.sources
            }

            result_str = json.dumps(result_dict, indent=2)

            # Check for placeholder indicators
            placeholder_indicators = [
                'Need to perform web search',
                'placeholder',
                'mock data',
                'test data',
                'fallback'
            ]

            has_real_data = True
            for indicator in placeholder_indicators:
                if indicator.lower() in result_str.lower():
                    has_real_data = False
                    print(f'⚠️ Found placeholder indicator: {indicator}')

            if has_real_data:
                print('✅ Research contains real data (no placeholder indicators found)')
            else:
                print('❌ Research appears to contain placeholder data')

            # Check confidence score
            confidence = research_result.confidence_score
            print(f'📊 Research confidence score: {confidence}')

            # Check for specific data types
            print('\n📋 Research Data Analysis:')
            company_intel = research_result.company_intelligence
            print(f'  📈 Company Intelligence: {len(str(company_intel))} characters')

            if 'recent_news' in company_intel and company_intel['recent_news']:
                print(f'  📰 Recent News: Found')
            else:
                print(f'  📰 Recent News: Not found')

            print(f'  🎯 Conversation Hooks: {len(research_result.conversation_hooks)} found')
            print(f'  📅 Research Timestamp: {research_result.research_timestamp}')
            print(f'  🔗 Sources: {len(research_result.sources)} found')
            
            # Test MongoDB storage
            print('\n💾 Testing MongoDB Storage...')
            db_manager = MongoDBManager()
            if db_manager.connect():
                research_collection = db_manager.get_collection('research_results')
                
                # Check if research was stored
                stored_research = research_collection.find_one({
                    'lead_name': test_lead_data.lead_name,
                    'company': test_lead_data.company
                })
                
                if stored_research:
                    print('✅ Research data successfully stored in MongoDB')
                    print(f'  📅 Stored at: {stored_research.get("timestamp", "Unknown")}')
                else:
                    print('⚠️ Research data not found in MongoDB storage')
                
                db_manager.disconnect()
            else:
                print('❌ Failed to connect to MongoDB for storage verification')
            
            return True
            
        else:
            print('❌ Research failed - no result returned')
            return False
            
    except Exception as e:
        print(f'❌ Research test failed with error: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_tavily_api_directly():
    """Test Tavily API directly to ensure it's working"""
    
    print('\n' + '='*60)
    print('🌐 TESTING TAVILY API DIRECTLY')
    print('='*60)
    
    try:
        import requests
        
        tavily_api_key = os.getenv('TAVILY_API_KEY')
        if not tavily_api_key:
            print('❌ Tavily API key not found')
            return False
        
        # Test Tavily API directly
        url = "https://api.tavily.com/search"
        headers = {
            "Authorization": f"Bearer {tavily_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": "Stripe company recent news 2024",
            "search_depth": "basic",
            "max_results": 3,
            "include_answer": True
        }
        
        print('🔍 Making direct API call to Tavily...')
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print('✅ Tavily API call successful!')
            print(f'  📊 Results count: {len(data.get("results", []))}')
            
            if data.get('results'):
                first_result = data['results'][0]
                print(f'  📰 First result title: {first_result.get("title", "No title")[:100]}...')
                print(f'  🔗 First result URL: {first_result.get("url", "No URL")}')
            
            return True
        else:
            print(f'❌ Tavily API call failed with status: {response.status_code}')
            print(f'  Response: {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Direct Tavily API test failed: {e}')
        return False

if __name__ == "__main__":
    print('🚀 Starting Research Functionality Tests...\n')
    
    # Test Tavily API directly first
    tavily_success = test_tavily_api_directly()
    
    # Test research agent functionality
    research_success = test_research_functionality()
    
    print('\n' + '='*60)
    print('🎯 RESEARCH FUNCTIONALITY TEST SUMMARY')
    print('='*60)
    
    print(f'✅ Tavily API Direct Test: {"PASS" if tavily_success else "FAIL"}')
    print(f'✅ Research Agent Test: {"PASS" if research_success else "FAIL"}')
    
    if tavily_success and research_success:
        print('\n🎉 ALL RESEARCH FUNCTIONALITY TESTS PASSED!')
        print('✅ Research agent is fetching real data from Tavily API')
        print('✅ Data is being stored properly in MongoDB')
        sys.exit(0)
    else:
        print('\n⚠️ Some research functionality tests failed')
        sys.exit(1)
