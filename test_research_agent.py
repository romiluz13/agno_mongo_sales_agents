#!/usr/bin/env python3
"""
Test the research agent directly to verify Tavily integration
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add backend to path
sys.path.append('/Users/rom.iluz/Dev/agno_sales_agent/agno/agno-sales-extension/backend')

from agents.research_agent import ResearchAgent

# Load environment variables
load_dotenv()

async def test_research_agent():
    """Test research agent with a real company"""
    
    # Get API keys
    api_keys = {
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        'MONDAY_API_KEY': os.getenv('MONDAY_API_KEY'),
        'MONGODB_CONNECTION_STRING': os.getenv('MONGODB_CONNECTION_STRING')
    }
    
    print("🧪 Testing Research Agent with Tavily Integration\n")
    
    # Check API keys
    for key, value in api_keys.items():
        if value:
            print(f"✅ {key}: {value[:10]}...")
        else:
            print(f"❌ {key}: MISSING")
    
    print("\n🔬 Initializing Research Agent...")
    
    try:
        # Initialize research agent
        research_agent = ResearchAgent(api_keys=api_keys)
        print("✅ Research Agent initialized successfully")
        
        # Test with a well-known company
        print("\n🔍 Testing research for: Base44")

        # Import LeadInput
        from agents.research_agent import LeadInput

        lead_input = LeadInput(
            lead_name="Maor Shlomo",
            company="Base44",
            title="CTO",
            industry="Technology",
            company_size="Startup"
        )

        result = research_agent.research_lead(lead_input)
        
        print(f"\n📊 Research Results:")
        print(f"Confidence Score: {result.confidence_score}")
        print(f"Company Intelligence:")
        print(f"  Recent News: {result.company_intelligence.get('recent_news', 'N/A')[:200]}...")
        print(f"  Growth Signals: {result.company_intelligence.get('growth_signals', [])}")
        print(f"  Challenges: {result.company_intelligence.get('challenges', [])}")
        print(f"  Technology Stack: {result.company_intelligence.get('technology_stack', 'N/A')[:100]}...")

        # Check if we got real data
        recent_news = result.company_intelligence.get('recent_news', '')
        if "Need to perform web search" in recent_news or "No recent news found" in recent_news:
            print("❌ Still getting placeholder data!")
        else:
            print("✅ Got real research data from Tavily!")

        print(f"\nSources: {len(result.sources)} sources found")
        for i, source in enumerate(result.sources[:3], 1):
            print(f"  {i}. {source}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_research_agent())
