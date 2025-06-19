"""
API Connection Testing Script
Tests all required API connections following Agno cookbook patterns
"""

import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def test_tavily_connection() -> Dict[str, Any]:
    """Test Tavily API connection using cookbook patterns"""
    try:
        from agno.agent import Agent
        from agno.tools.tavily import TavilyTools

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key or api_key == "your_tavily_api_key_here":
            return {
                "success": False,
                "message": "Tavily API key not configured",
                "service": "Tavily"
            }

        # Test Tavily connection using Agent pattern from cookbook
        # Use Gemini model to avoid OpenAI dependency
        from agno.models.google import Gemini
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        agent = Agent(
            model=Gemini(id="gemini-2.0-flash-001", api_key=gemini_key) if gemini_key else None,
            tools=[TavilyTools(api_key=api_key)]
        )

        # Simple test search
        response = agent.run("Search for 'test query'")

        return {
            "success": True,
            "message": "Tavily API connection successful",
            "service": "Tavily",
            "test_result": "Search completed successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Tavily API connection failed: {e}",
            "service": "Tavily"
        }

def test_gemini_connection() -> Dict[str, Any]:
    """Test Google Gemini API connection using cookbook patterns"""
    try:
        from agno.agent import Agent
        from agno.models.google import Gemini

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_gemini_api_key_here":
            return {
                "success": False,
                "message": "Google Gemini API key not configured",
                "service": "Gemini"
            }

        # Test Gemini connection using Agent pattern from cookbook
        agent = Agent(model=Gemini(id="gemini-2.0-flash-001", api_key=api_key))

        # Simple test prompt
        response = agent.run("Say 'Hello from Gemini!'")

        return {
            "success": True,
            "message": "Google Gemini API connection successful",
            "service": "Gemini",
            "test_result": "Model responded successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Google Gemini API connection failed: {e}",
            "service": "Gemini"
        }

def test_monday_connection() -> Dict[str, Any]:
    """Test Monday.com API connection"""
    try:
        import requests
        
        api_token = os.getenv("MONDAY_API_TOKEN")
        if not api_token or api_token == "your_monday_api_token_here":
            return {
                "success": False,
                "message": "Monday.com API token not configured",
                "service": "Monday.com"
            }
        
        # Test Monday.com connection with a simple query
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        query = """
        query {
            me {
                name
                email
            }
        }
        """
        
        response = requests.post(
            "https://api.monday.com/v2",
            json={"query": query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                return {
                    "success": False,
                    "message": f"Monday.com API error: {data['errors']}",
                    "service": "Monday.com"
                }
            
            return {
                "success": True,
                "message": "Monday.com API connection successful",
                "service": "Monday.com",
                "test_result": f"Connected as: {data.get('data', {}).get('me', {}).get('name', 'Unknown')}"
            }
        else:
            return {
                "success": False,
                "message": f"Monday.com API returned status {response.status_code}",
                "service": "Monday.com"
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Monday.com API connection failed: {e}",
            "service": "Monday.com"
        }

def test_mongodb_connection() -> Dict[str, Any]:
    """Test MongoDB connection"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from database import MongoDBManager
        
        manager = MongoDBManager()
        result = manager.test_connection()
        manager.disconnect()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "service": "MongoDB",
            "test_result": f"Database: {result.get('database', 'N/A')}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"MongoDB connection failed: {e}",
            "service": "MongoDB"
        }

def test_all_connections() -> Dict[str, Any]:
    """Test all API connections and return comprehensive results"""
    print("🔧 Testing all API connections...")
    print("=" * 50)
    
    tests = [
        ("MongoDB", test_mongodb_connection),
        ("Monday.com", test_monday_connection),
        ("Tavily", test_tavily_connection),
        ("Google Gemini", test_gemini_connection)
    ]
    
    results = {}
    all_success = True
    
    for service_name, test_func in tests:
        print(f"\n🧪 Testing {service_name}...")
        result = test_func()
        results[service_name] = result
        
        if result["success"]:
            print(f"✅ {service_name}: {result['message']}")
            if "test_result" in result:
                print(f"   📋 {result['test_result']}")
        else:
            print(f"❌ {service_name}: {result['message']}")
            all_success = False
    
    print("\n" + "=" * 50)
    if all_success:
        print("🎉 ALL API CONNECTIONS SUCCESSFUL!")
        print("✅ Ready to proceed with development")
    else:
        print("⚠️  SOME API CONNECTIONS FAILED")
        print("❌ Please configure missing API keys in .env file")
        print("\nRequired API keys:")
        print("- MONDAY_API_TOKEN (from Monday.com Developer section)")
        print("- TAVILY_API_KEY (from Tavily dashboard)")
        print("- GOOGLE_API_KEY (from Google AI Studio)")
    
    return {
        "all_success": all_success,
        "results": results,
        "summary": f"{sum(1 for r in results.values() if r['success'])}/{len(results)} services connected"
    }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Test all connections
    test_results = test_all_connections()
    
    # Exit with appropriate code
    exit(0 if test_results["all_success"] else 1)
